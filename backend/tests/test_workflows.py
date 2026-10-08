import io
from datetime import timedelta
import pytest
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader
from api.db import now
from api.schemas import ResumeDraft, QuestionSet
from api.services.pdf import export_resume
from api.services import judge, ai, bank, code_bank
from conftest import register


def post(c, path, data=None):
    return c.post('/api' + path, data or {}, content_type='application/json')


def test_csrf_auth_and_logout(client, mongo):
    assert Client().get('/api/progress').status_code == 401
    c = Client(enforce_csrf_checks=True)
    assert post(c, '/auth/login', {'email': 'candidate@example.com', 'password': 'Bright!Sky927#'}).status_code == 403
    assert mongo.users.find_one()['password_hash'].startswith('pbkdf2_sha256$')
    assert 'password' not in str(client.get('/api/auth/me').json())
    assert client.cookies['skillentra_session']['httponly']
    assert post(client, '/auth/logout').status_code == 200
    assert client.get('/api/auth/me').status_code == 401
    assert mongo.sessions.count_documents({}) == 0


def test_email_case_and_duplicate(client):
    c = Client(enforce_csrf_checks=True)
    t = c.get('/api/auth/csrf').json()['csrfToken']
    result = c.post('/api/auth/login', {'email': 'CANDIDATE@EXAMPLE.COM', 'password': 'Bright!Sky927#'}, content_type='application/json', HTTP_X_CSRFTOKEN=t)
    assert result.status_code == 200
    result = post(client, '/auth/register', {'full_name': 'Other', 'email': 'CANDIDATE@example.com', 'password': 'Bright!Sky927#', 'confirm_password': 'Bright!Sky927#'})
    assert result.status_code == 409


def test_cross_account_ownership(client):
    created = post(client, '/drafts', {'full_name': 'Owner'}).json()
    other = register(Client(enforce_csrf_checks=True), 'other@example.com')
    assert other.get('/api/drafts/' + created['id']).status_code == 404
    assert other.get('/api/drafts/' + created['id'] + '/pdf').status_code == 404


@pytest.mark.parametrize('template', ['classic', 'modern', 'compact'])
def test_builder_export_and_pdf_analysis(client, template, mongo):
    draft = ResumeDraft(full_name='Naresh Test', email='naresh@example.com', phone='+91 9876543210', template=template,
        summary='Junior Python developer with experience building web applications and testing REST services. Focused on practical problem solving, clear communication and reliable software.',
        skills=['Python', 'Django', 'React', 'SQL', 'Git'],
        projects=[{'title': 'Resume platform', 'organization': 'Personal project', 'start': 'Aug 2025', 'end': 'Present',
                   'details': 'Built and tested 12 REST endpoints with validation and automated tests.\nImplemented authentication and project documentation for a web platform used for practice and learning.'}],
        education=[{'title': 'MCA', 'organization': 'Example University', 'details': 'Studied programming, database systems and software engineering.'}]).model_dump()
    created = post(client, '/drafts', draft).json()
    response = client.get('/api/drafts/' + created['id'] + '/pdf')
    assert response.status_code == 200
    assert response.content.startswith(b'%PDF')
    text = '\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(response.content)).pages)
    assert 'Naresh Test' in text and 'Python' in text and 'EDUCATION' in text
    upload = SimpleUploadedFile('resume.pdf', response.content, content_type='application/pdf')
    analyzed = client.post('/api/resumes', {'resume': upload, 'technology': 'Python', 'use_ai': 'false'})
    assert analyzed.status_code == 200, analyzed.content
    result = analyzed.json()['report']
    assert 0 <= result['score'] <= 100 and len(result['categories']) == 6
    assert 'python' in result['skills'] and result['ai'] is None
    stored = mongo.reports.find_one()
    assert 'text' not in stored and 'pdf' not in stored


def test_invalid_and_scanned_pdf_rejected(client):
    assert client.post('/api/resumes', {'resume': SimpleUploadedFile('fake.pdf', b'not a PDF')}).status_code == 400
    from pypdf import PdfWriter
    out = io.BytesIO(); writer = PdfWriter(); writer.add_blank_page(612, 792); writer.write(out)
    r = client.post('/api/resumes', {'resume': SimpleUploadedFile('scan.pdf', out.getvalue())})
    assert r.status_code == 400 and 'OCR' in r.json()['error']


def exam(c, mode='practice'):
    r = post(c, '/exams', {'technology': 'Python', 'mode': mode, 'use_ai': False, 'monitoring_consent': mode == 'ranked', 'fullscreen': mode == 'ranked'})
    assert r.status_code == 200, r.content
    return r.json()


def test_exam_no_answer_key_server_grading_and_idempotency(client, mongo):
    result = exam(client)
    assert all('correct' not in q and 'explanation' not in q for q in result['questions'])
    stored = mongo.exams.find_one({'_id': result['id']})
    for q in stored['questions']:
        assert post(client, f"/exams/{result['id']}/answers", {'question_id': q['id'], 'option': q['correct']}).status_code == 200
    done = post(client, f"/exams/{result['id']}/submit", {'score': 0}).json()
    assert done['score'] == 100
    assert post(client, f"/exams/{result['id']}/submit").json()['score'] == 100
    assert post(client, f"/exams/{result['id']}/answers", {'question_id': q['id'], 'option': 0}).status_code == 409


def test_expired_exam_cannot_save(client, mongo):
    e = exam(client)
    mongo.exams.update_one({'_id': e['id']}, {'$set': {'deadline': now() - timedelta(seconds=1)}})
    assert post(client, f"/exams/{e['id']}/answers", {'question_id': e['questions'][0]['id'], 'option': 0}).status_code == 409
    done = client.get('/api/exams/' + e['id']).json()
    assert done['status'] == 'completed' and done['score'] == 0 and done['timed_out']


def test_only_one_active_and_ranked_daily_limit(client):
    e = exam(client, 'ranked')
    assert post(client, '/exams', {'technology': 'Java', 'mode': 'practice'}).status_code == 409
    post(client, f"/exams/{e['id']}/submit")
    assert post(client, '/exams', {'technology': 'Python', 'mode': 'ranked', 'monitoring_consent': True, 'fullscreen': True}).status_code == 409


def test_events_deduplicate_and_exclude_flagged_result(client):
    e = exam(client, 'ranked')
    for i in range(3):
        r = post(client, f"/exams/{e['id']}/events", {'event_id': str(i), 'kind': 'visibility_lost'})
        assert r.status_code == 200
        again = post(client, f"/exams/{e['id']}/events", {'event_id': str(i), 'kind': 'visibility_lost'})
        assert again.json()['event_count'] == i + 1
    assert r.json()['status'] == 'completed' and r.json()['integrity'] == 'review_required'
    assert client.get('/api/leaderboard').json()['items'] == []


def test_heartbeat_gap_and_leaderboard_privacy(client, mongo):
    e = exam(client, 'ranked')
    post(client, f"/exams/{e['id']}/submit")
    rows = client.get('/api/leaderboard').json()['items']
    assert len(rows) == 1 and rows[0]['is_you'] and 'email' not in rows[0]
    client.patch('/api/auth/me', {'leaderboard_opt_in': False}, content_type='application/json')
    assert client.get('/api/leaderboard').json()['items'] == []


def test_unknown_option_id_and_payload_validation(client):
    e = exam(client)
    assert post(client, f"/exams/{e['id']}/answers", {'question_id': '$bad.key', 'option': 0}).status_code == 400
    assert post(client, f"/exams/{e['id']}/answers", {'question_id': e['questions'][0]['id'], 'option': True}).status_code == 400
    assert post(client, '/interviews', {'technology': {'$ne': None}}).status_code == 400


def test_interview_five_turns_no_fake_ai_grade(client):
    r = post(client, '/interviews', {'technology': 'Django', 'use_ai': False}).json()
    for i in range(5):
        r = post(client, f"/interviews/{r['id']}/answers", {'turn': i, 'answer': 'I built a project and tested the behavior using repeatable test cases.'}).json()
        assert len(r['turns']) == i + 1
    assert r['status'] == 'completed' and r['score'] is None and r['ai_scored_turns'] == 0
    assert post(client, f"/interviews/{r['id']}/answers", {'turn': 4, 'answer': 'another'}).status_code == 409


@pytest.mark.parametrize('language', ['Python', 'JavaScript', 'Java', 'C++'])
@pytest.mark.parametrize('difficulty', ['easy', 'medium', 'hard'])
def test_coding_exactly_three_and_hidden_cases_private(client, language, difficulty):
    result = post(client, '/coding', {'language': language, 'difficulty': difficulty, 'use_ai': False}).json()
    assert len(result['questions']) == 3
    for q in result['questions']:
        assert 'tests' not in q and 'reference_solution' not in q and q['hidden_test_count'] >= 4
    r = post(client, f"/coding/{result['id']}/submissions", {'question_id': result['questions'][0]['id'], 'source': 'print(1)'})
    assert r.status_code == 503


def test_code_execution_scoring_and_hidden_output(client, mongo, monkeypatch):
    monkeypatch.setenv('JUDGE0_URL', 'http://isolated-judge.example')
    monkeypatch.setattr(judge, 'submit', lambda source, language, tests: [str(i) for i in range(len(tests))])
    d = post(client, '/coding', {'language': 'Python', 'difficulty': 'easy', 'use_ai': False}).json()
    r = post(client, f"/coding/{d['id']}/submissions", {'question_id': d['questions'][0]['id'], 'source': 'untrusted program', 'mode': 'submit'}).json()
    cases = mongo.submissions.find_one({'_id': r['id']})['tests']
    monkeypatch.setattr(judge, 'poll', lambda tokens: [{'status': {'id': 3, 'description': 'Accepted'}, 'stdout': judge.encode(t['expected'])} for t in cases])
    result = client.get('/api/submissions/' + r['id']).json()
    assert result['score'] == 100 and result['status'] == 'completed'
    assert 'stdout' in result['results'][0]
    assert all('stdout' not in x and 'stdin' not in x and 'expected' not in x for x in result['results'][1:])
    best = client.get('/api/coding/' + d['id']).json()['best_scores']
    assert best[d['questions'][0]['id']] == 100


def test_ai_failure_and_schema_invalid_fallback(monkeypatch):
    monkeypatch.setenv('AI_PROVIDER', 'ollama')
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'message': {'content': '{"questions": []}'}}
    monkeypatch.setattr('httpx.Client.post', lambda *a, **kw: Response())
    result, notice = ai.generate('exam', 'Generate questions', {}, QuestionSet)
    assert result is None and 'unavailable' in notice


def test_account_deletion_removes_data(client, mongo):
    post(client, '/drafts', {'full_name': 'Test'})
    r = client.delete('/api/auth/me', {'password': 'Bright!Sky927#'}, content_type='application/json')
    assert r.status_code == 200
    assert mongo.users.count_documents({}) == mongo.drafts.count_documents({}) == mongo.sessions.count_documents({}) == 0


def test_curated_bank_schema():
    for tech in bank.TECHNOLOGIES:
        rows = bank.questions(tech)
        QuestionSet.model_validate({'questions': [{k: v for k, v in q.items() if k != 'id'} for q in rows]})
