from datetime import timedelta
from django.conf import settings
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from ..db import database, now, uid
from ..security import APIError
from ..schemas import QuestionSet
from . import bank
from .ai import generate


def create_exam(user_id, form):
    db = database()
    old = db.exams.find_one({'user_id': user_id, 'status': 'active'})
    if old:
        if old['deadline'] <= now(): finish(old)
        else: raise APIError('You already have an active assessment. Resume it from this page.', 409)
    if form.mode == 'ranked' and not (form.monitoring_consent and form.fullscreen):
        raise APIError('Ranked assessments require monitoring consent and full-screen mode.')
    qs = bank.questions(form.technology)
    source, notice = 'Curated question bank', ''
    if form.mode == 'practice' and form.use_ai:
        generated, provider = generate('exam', 'Create exactly 10 distinct multiple-choice questions on the selected technology for a junior developer. Each must have exactly four distinct options, one unambiguous correct index (0 to 3), and an accurate explanation. Mix knowledge, code interpretation and practical debugging.', {'technology': form.technology}, QuestionSet)
        if generated:
            qs = [{'id': uid(), **q.model_dump()} for q in generated.questions]
            source = provider
        else: notice = provider
    start = now()
    doc = {'_id': uid(), 'user_id': user_id, 'technology': form.technology, 'mode': form.mode,
           'bank_version': bank.BANK_VERSION, 'source': source, 'notice': notice, 'questions': qs,
           'answers': {}, 'events': [], 'event_count': 0, 'status': 'active', 'score': None,
           'created_at': start, 'deadline': start + timedelta(seconds=settings.EXAM_SECONDS),
           'last_heartbeat': start, 'integrity': 'clear', 'monitoring_consent': form.monitoring_consent}
    if form.mode == 'ranked': doc['rank_key'] = f'{user_id}:{form.technology}:{start.date()}:{bank.BANK_VERSION}'
    try:
        db.exams.insert_one(doc)
    except DuplicateKeyError:
        raise APIError('You have an active assessment or have already taken this ranked technology test today. Practice is still available.', 409)
    return doc


def finish(exam):
    db = database()
    timestamp = now()
    # An atomic status transition freezes autosaves and ensures one grader wins.
    frozen = db.exams.find_one_and_update({'_id': exam['_id'], 'status': 'active'},
        {'$set': {'status': 'grading', 'submitted_at': timestamp}}, return_document=ReturnDocument.AFTER)
    if not frozen:
        frozen = db.exams.find_one({'_id': exam['_id']})
        if frozen['status'] == 'completed': return frozen
    # Recovery is deterministic if a worker stopped after the transition to grading.
    correct = sum(frozen['answers'].get(q['id']) == q['correct'] for q in frozen['questions'])
    gap = (min(frozen['submitted_at'], frozen['deadline']) - frozen['last_heartbeat']).total_seconds() > 45
    flagged = frozen['mode'] == 'ranked' and (frozen['event_count'] >= settings.MAX_EXAM_EVENTS or gap)
    result = {'status': 'completed', 'score': round(correct / len(frozen['questions']) * 100),
              'correct_count': correct, 'integrity': 'review_required' if flagged else 'clear',
              'elapsed_seconds': max(1, min(settings.EXAM_SECONDS, int((frozen['submitted_at'] - frozen['created_at']).total_seconds()))),
              'timed_out': frozen['submitted_at'] >= frozen['deadline'], 'heartbeat_gap': gap}
    db.exams.update_one({'_id': frozen['_id'], 'status': 'grading'}, {'$set': result})
    return db.exams.find_one({'_id': frozen['_id']})


def expose(exam):
    if exam['status'] == 'grading' or (exam['status'] == 'active' and exam['deadline'] <= now()):
        exam = finish(exam)
    data = {k: v for k, v in exam.items() if k not in ['user_id', 'rank_key']}
    if exam['status'] != 'completed':
        data['questions'] = [{k: q[k] for k in ['id', 'question', 'options']} for q in exam['questions']]
    data['server_now'] = now()
    data['violation_limit'] = settings.MAX_EXAM_EVENTS
    return data


def save_answer(exam, form):
    if not any(q['id'] == form.question_id for q in exam['questions']): raise APIError('Unknown question.')
    result = database().exams.update_one({'_id': exam['_id'], 'status': 'active', 'deadline': {'$gt': now()}},
                                         {'$set': {f'answers.{form.question_id}': form.option}})
    if not result.matched_count: raise APIError('This assessment has ended. Submit it to see the result.', 409)


def record_event(exam, event):
    if exam['mode'] != 'ranked': return exam
    # The caller supplies only a kind and a nonce. The server owns the clock and count.
    updated = database().exams.find_one_and_update(
        {'_id': exam['_id'], 'status': 'active', 'deadline': {'$gt': now()}, 'events.event_id': {'$ne': event.event_id}},
        {'$push': {'events': {'$each': [{'event_id': event.event_id, 'kind': event.kind, 'at': now()}], '$slice': -50}},
         '$inc': {'event_count': 1}}, return_document=ReturnDocument.AFTER)
    if updated and updated['event_count'] >= settings.MAX_EXAM_EVENTS:
        return finish(updated)
    return updated or database().exams.find_one({'_id': exam['_id']})
