from datetime import timedelta
from django.http import HttpResponse
from pymongo import ReturnDocument
from .db import database, now, uid
from .security import api, APIError, owned, rate_limit
from .schemas import ResumeDraft, StartExam, Answer, ExamEvent, StartInterview, InterviewAnswer, StartCoding, CodeSubmission
from .services import ai, bank, resume, pdf, exams, interviews, coding, judge


@api(authenticated=False, limit=0)
def health(request):
    database().command('ping')
    return {'status': 'ok'}


@api()
def catalog(request):
    return {'technologies': bank.TECHNOLOGIES, 'languages': list(judge.DEFAULT_IDS),
            'difficulties': ['easy', 'medium', 'hard'], 'ai': ai.status(),
            'runner_configured': judge.configured()}


@api(('GET', 'POST'), limit=12)
def reports(request):
    db = database()
    if request.method == 'GET':
        return {'items': list(db.reports.find({'user_id': request.user_doc['_id']}, {'report': 0}).sort('created_at', -1).limit(30))}
    rate_limit('resume-daily:' + request.user_doc['_id'], 30, 86400)
    upload = request.FILES.get('resume')
    text, pages = resume.read_pdf(upload)
    technology = request.POST.get('technology', '')
    if technology and technology not in bank.TECHNOLOGIES: raise APIError('Choose a supported technology.')
    report = resume.analyze(text, pages, technology, request.POST.get('use_ai') == 'true')
    doc = {'_id': uid(), 'user_id': request.user_doc['_id'], 'filename': upload.name[:180],
           'created_at': now(), 'score': report['score'], 'report': report}
    db.reports.insert_one(doc)
    # The uploaded PDF and its raw extracted text are not stored.
    return {k: v for k, v in doc.items() if k != 'user_id'}


@api(('GET', 'DELETE'))
def report_detail(request, resource_id):
    doc = owned('reports', resource_id, request)
    if request.method == 'DELETE':
        database().reports.delete_one({'_id': doc['_id'], 'user_id': request.user_doc['_id']})
        return {'ok': True}
    return {k: v for k, v in doc.items() if k != 'user_id'}


@api(('GET', 'POST'))
def drafts(request):
    if request.method == 'GET':
        return {'items': list(database().drafts.find({'user_id': request.user_doc['_id']}, {'data': 0}).sort('updated_at', -1).limit(50))}
    data = ResumeDraft.model_validate(request.data).model_dump()
    doc = {'_id': uid(), 'user_id': request.user_doc['_id'], 'title': data['title'], 'data': data,
           'created_at': now(), 'updated_at': now()}
    database().drafts.insert_one(doc)
    return {k: v for k, v in doc.items() if k != 'user_id'}


@api(('GET', 'PUT', 'DELETE'))
def draft_detail(request, resource_id):
    doc = owned('drafts', resource_id, request)
    if request.method == 'DELETE':
        database().drafts.delete_one({'_id': doc['_id'], 'user_id': request.user_doc['_id']})
        return {'ok': True}
    if request.method == 'PUT':
        data = ResumeDraft.model_validate(request.data).model_dump()
        doc.update({'data': data, 'title': data['title'], 'updated_at': now()})
        database().drafts.update_one({'_id': doc['_id'], 'user_id': request.user_doc['_id']}, {'$set': {'data': data, 'title': data['title'], 'updated_at': doc['updated_at']}})
    return {k: v for k, v in doc.items() if k != 'user_id'}


@api()
def draft_pdf(request, resource_id):
    doc = owned('drafts', resource_id, request)
    data = ResumeDraft.model_validate(doc['data']).model_dump()
    if not data['full_name']: raise APIError('Add your name before exporting.')
    response = HttpResponse(pdf.export_resume(data), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="skillentra-resume.pdf"'
    return response


@api(('POST',), limit=4)
def exam_start(request):
    rate_limit('exam-daily:' + request.user_doc['_id'], 30, 86400)
    doc = exams.create_exam(request.user_doc['_id'], StartExam.model_validate(request.data))
    return exams.expose(doc)


@api()
def exam_active(request):
    doc = database().exams.find_one({'user_id': request.user_doc['_id'], 'status': {'$in': ['active', 'grading']}})
    return {'exam': exams.expose(doc) if doc else None}


@api()
def exam_detail(request, resource_id):
    return exams.expose(owned('exams', resource_id, request))


@api(('POST',))
def exam_answer(request, resource_id):
    doc = owned('exams', resource_id, request)
    exams.save_answer(doc, Answer.model_validate(request.data))
    return {'ok': True}


@api(('POST',))
def exam_event(request, resource_id):
    doc = owned('exams', resource_id, request)
    return exams.expose(exams.record_event(doc, ExamEvent.model_validate(request.data)))


@api(('POST',))
def exam_heartbeat(request, resource_id):
    doc = owned('exams', resource_id, request)
    timestamp = now()
    if doc['status'] == 'active' and doc['deadline'] > timestamp:
        if doc['mode'] == 'ranked' and (timestamp - doc['last_heartbeat']).total_seconds() > 45:
            doc = exams.record_event(doc, ExamEvent(event_id=uid(), kind='connection_gap'))
        database().exams.update_one({'_id': doc['_id'], 'status': 'active'}, {'$set': {'last_heartbeat': timestamp}})
    return exams.expose(database().exams.find_one({'_id': doc['_id']}))


@api(('POST',))
def exam_submit(request, resource_id):
    doc = owned('exams', resource_id, request)
    return exams.expose(exams.finish(doc))


@api()
def leaderboard(request):
    technology = request.GET.get('technology', 'Python')
    if technology not in bank.TECHNOLOGIES: raise APIError('Unknown technology.')
    pipeline = [
        {'$match': {'technology': technology, 'mode': 'ranked', 'status': 'completed', 'integrity': 'clear', 'bank_version': bank.BANK_VERSION}},
        {'$sort': {'score': -1, 'elapsed_seconds': 1, 'submitted_at': 1}},
        {'$group': {'_id': '$user_id', 'best': {'$first': '$$ROOT'}}},
        {'$lookup': {'from': 'users', 'localField': '_id', 'foreignField': '_id', 'as': 'user'}},
        {'$unwind': '$user'}, {'$match': {'user.leaderboard_opt_in': True}},
        {'$sort': {'best.score': -1, 'best.elapsed_seconds': 1, 'best.submitted_at': 1}}, {'$limit': 50},
        {'$project': {'_id': 0, 'user_id': '$_id', 'name': '$user.full_name', 'score': '$best.score', 'elapsed_seconds': '$best.elapsed_seconds'}},
    ]
    items = list(database().exams.aggregate(pipeline))
    for i, row in enumerate(items):
        row['rank'] = i + 1
        row['is_you'] = row.pop('user_id') == request.user_doc['_id']
    return {'items': items, 'technology': technology, 'bank_version': bank.BANK_VERSION,
            'notice': 'Best ranked score per participant; ties use faster completion then earlier submission. This is a practice leaderboard with browser monitoring, not an identity-verified exam.'}


@api(('POST',), limit=4)
def interview_start(request):
    rate_limit('interview-daily:' + request.user_doc['_id'], 30, 86400)
    doc = interviews.create_interview(request.user_doc['_id'], StartInterview.model_validate(request.data))
    return {k: v for k, v in doc.items() if k not in ['user_id', 'questions']}


@api()
def interview_detail(request, resource_id):
    doc = owned('interviews', resource_id, request)
    if doc['status'] == 'evaluating' and (now() - doc['locked_at']).total_seconds() > 180:
        database().interviews.update_one({'_id': doc['_id'], 'status': 'evaluating'}, {'$set': {'status': 'active'}})
        doc['status'] = 'active'
    return {k: v for k, v in doc.items() if k not in ['user_id', 'questions']}


@api(('POST',), limit=10)
def interview_answer(request, resource_id):
    doc = interviews.answer_interview(owned('interviews', resource_id, request), InterviewAnswer.model_validate(request.data))
    return {k: v for k, v in doc.items() if k not in ['user_id', 'questions']}


@api(('POST',), limit=3)
def coding_start(request):
    rate_limit('coding-daily:' + request.user_doc['_id'], 15, 86400)
    return coding.expose(coding.create(request.user_doc['_id'], StartCoding.model_validate(request.data)))


@api()
def coding_detail(request, resource_id):
    doc = coding.refresh(owned('coding', resource_id, request))
    return coding.expose(doc)


@api(('POST',), limit=10)
def coding_submit(request, resource_id):
    rate_limit('submissions-daily:' + request.user_doc['_id'], 100, 86400)
    return coding.submit(owned('coding', resource_id, request), request.user_doc['_id'], CodeSubmission.model_validate(request.data))


@api()
def submission_detail(request, resource_id):
    return coding.submission_result(owned('submissions', resource_id, request))


@api()
def progress(request):
    owner = {'user_id': request.user_doc['_id']}
    for doc in database().exams.find({**owner, 'status': {'$in': ['active', 'grading']}, 'deadline': {'$lte': now()}}): exams.finish(doc)
    fields = {
        'reports': ['filename', 'score'], 'drafts': ['title'],
        'interviews': ['technology', 'difficulty', 'status', 'score', 'ai_scored_turns'],
        'exams': ['technology', 'mode', 'status', 'score', 'integrity'],
        'coding': ['language', 'difficulty', 'status', 'best_scores'],
    }
    response = {}
    for name, keys in fields.items():
        response[name] = list(database()[name].find(owner, {'_id': 1, 'created_at': 1, **{k: 1 for k in keys}}).sort('created_at', -1).limit(30))
    response['totals'] = {name: database()[name].count_documents(owner) for name in fields}
    return response
