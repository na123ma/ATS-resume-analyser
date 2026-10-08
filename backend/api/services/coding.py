from ..db import database, now, uid
from ..schemas import CodeSet
from ..security import APIError
from . import judge
from .ai import generate
from .code_bank import get_problems


def create(user_id, form):
    qs = get_problems(form.language, form.difficulty)
    source, notice, status, checks = 'Curated coding bank', '', 'ready', []
    if form.use_ai and judge.configured():
        generated, label = generate('coding', 'Create exactly 3 distinct programming problems for the selected language and difficulty. Programs read stdin and write stdout. Clearly specify input/output and constraints. For each problem provide a starter, a complete correct reference_solution in the requested language (Java class Main), and exactly 5 deterministic input/output tests including edge cases. The first test is a public example; the other 4 are hidden. No randomness, interactive input, external packages, files or network. Avoid ambiguous output ordering.',
            {'language': form.language, 'difficulty': form.difficulty}, CodeSet)
        if generated:
            try:
                proposed = [{'id': uid(), **q.model_dump()} for q in generated.questions]
                for q in proposed:
                    checks.append({'question_id': q['id'], 'tokens': judge.submit(q['reference_solution'], form.language, q['tests'])})
                qs, source, status = proposed, label, 'validating'
            except APIError:
                notice = 'Generated problem validation could not start. A curated problem set is available.'
                checks = []
        else: notice = label
    elif form.use_ai:
        notice = 'AI-generated coding problems require a configured runner to check reference solutions. This is a curated set.'
    doc = {'_id': uid(), 'user_id': user_id, 'language': form.language, 'difficulty': form.difficulty,
           'questions': qs, 'source': source, 'notice': notice, 'status': status, 'validation': checks,
           'best_scores': {}, 'created_at': now()}
    database().coding.insert_one(doc)
    return doc


def refresh(doc):
    if doc['status'] != 'validating': return doc
    good, pending = True, False
    if (now() - doc['created_at']).total_seconds() > 180:
        good = False
    else:
        for check in doc['validation']:
            items = judge.poll(check['tokens'])
            if not judge.completed(items): pending = True; continue
            q = next(q for q in doc['questions'] if q['id'] == check['question_id'])
            if not all(judge.passed(item, case) for item, case in zip(items, q['tests'])): good = False
    if pending and good: return doc
    update = {'status': 'ready', 'validation': []}
    if not good:
        update.update({'questions': get_problems(doc['language'], doc['difficulty']), 'source': 'Curated coding bank',
                       'notice': 'The generated reference solutions did not pass validation. A curated set replaced them.'})
    else:
        # Reference solutions are never exposed to the browser or retained after validation.
        update['questions'] = [{k: v for k, v in q.items() if k != 'reference_solution'} for q in doc['questions']]
    database().coding.update_one({'_id': doc['_id'], 'status': 'validating'}, {'$set': update})
    return database().coding.find_one({'_id': doc['_id']})


def expose(doc):
    data = {k: v for k, v in doc.items() if k not in ['user_id', 'validation', 'questions']}
    data['runner_configured'] = judge.configured()
    data['questions'] = [] if doc['status'] == 'validating' else [{
        **{k: q[k] for k in ['id', 'title', 'description', 'constraints', 'starter']},
        'example': q['tests'][0], 'hidden_test_count': len(q['tests']) - 1,
    } for q in doc['questions']]
    return data


def submit(doc, user_id, form):
    if doc['status'] != 'ready': raise APIError('This problem set is still being validated.', 409)
    q = next((q for q in doc['questions'] if q['id'] == form.question_id), None)
    if not q: raise APIError('Problem not found.', 404)
    cases = q['tests'] if form.mode == 'submit' else q['tests'][:1]
    tokens = judge.submit(form.source, doc['language'], cases)
    entry = {'_id': uid(), 'user_id': user_id, 'session_id': doc['_id'], 'question_id': q['id'],
             'mode': form.mode, 'tokens': tokens, 'tests': cases, 'status': 'pending', 'created_at': now(),
             'source': form.source}
    database().submissions.insert_one(entry)
    return {'id': entry['_id'], 'status': 'pending'}


def submission_result(entry):
    if entry['status'] == 'pending':
        if (now() - entry['created_at']).total_seconds() > 180:
            entry.update({'status': 'unavailable', 'message': 'The runner timed out. No score was recorded.'})
        else:
            items = judge.poll(entry['tokens'])
            if not judge.completed(items): return {'id': entry['_id'], 'status': 'pending'}
            if any(i['status']['id'] in (13, 14) for i in items):
                entry.update({'status': 'unavailable', 'message': 'The runner reported an infrastructure error. No score was recorded.'})
            else:
                results = []
                for i, (item, case) in enumerate(zip(items, entry['tests'])):
                    result = {'case': i + 1, 'public': i == 0, 'passed': judge.passed(item, case), 'status': item['status']['description']}
                    if i == 0:
                        result.update({'stdin': case['stdin'], 'expected': case['expected'], 'stdout': judge.decode(item.get('stdout')),
                                       'error': judge.decode(item.get('compile_output')) or judge.decode(item.get('stderr'))})
                    results.append(result)
                score = round(100 * sum(r['passed'] for r in results) / len(results))
                entry.update({'status': 'completed', 'results': results, 'score': score})
                if entry['mode'] == 'submit':
                    database().coding.update_one({'_id': entry['session_id'], 'user_id': entry['user_id']},
                                                 {'$max': {f"best_scores.{entry['question_id']}": score}})
        database().submissions.update_one({'_id': entry['_id']}, {'$set': {k: entry[k] for k in ['status', 'results', 'score', 'message'] if k in entry}})
    return {k: entry[k] for k in ['_id', 'status', 'score', 'results', 'message', 'mode'] if k in entry}
