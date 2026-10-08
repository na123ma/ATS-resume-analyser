"""Judge0 execution only: user code is never executed by the Django host."""
import base64
import os
import httpx
from ..security import APIError

DEFAULT_IDS = {'Python': 71, 'JavaScript': 63, 'Java': 62, 'C++': 54}
ENV_KEYS = {'Python': 'PYTHON', 'JavaScript': 'JAVASCRIPT', 'Java': 'JAVA', 'C++': 'CPP'}


def configured():
    return bool(os.getenv('JUDGE0_URL', '').strip())


def language_id(language):
    return int(os.getenv(f'JUDGE0_{ENV_KEYS[language]}_ID', DEFAULT_IDS[language]))


def encode(value):
    return base64.b64encode(value.encode()).decode()


def decode(value):
    if not value: return ''
    try: return base64.b64decode(value).decode('utf-8', errors='replace')[:4000]
    except (ValueError, TypeError): return ''


def request(method, path, **kwargs):
    url = os.getenv('JUDGE0_URL', '').rstrip('/')
    if not url: raise APIError('Code execution is not configured. Set JUDGE0_URL in backend/.env to an isolated Judge0 service.', 503)
    headers = {}
    if os.getenv('JUDGE0_AUTH_TOKEN'): headers['X-Auth-Token'] = os.environ['JUDGE0_AUTH_TOKEN']
    if os.getenv('JUDGE0_RAPIDAPI_KEY'): headers['X-RapidAPI-Key'] = os.environ['JUDGE0_RAPIDAPI_KEY']
    if os.getenv('JUDGE0_RAPIDAPI_HOST'): headers['X-RapidAPI-Host'] = os.environ['JUDGE0_RAPIDAPI_HOST']
    try:
        response = httpx.request(method, url + path, headers=headers, timeout=15, follow_redirects=False, **kwargs)
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        raise APIError('The code runner is unavailable or rejected this request. Check the Judge0 configuration and quota.', 503)


def submit(source, language, tests):
    jobs = [{'source_code': encode(source), 'language_id': language_id(language),
             'stdin': encode(t['stdin']), 'expected_output': encode(t['expected']),
             'cpu_time_limit': 3, 'wall_time_limit': 10, 'memory_limit': 256000,
             'max_file_size': 128, 'enable_network': False} for t in tests]
    result = request('POST', '/submissions/batch?base64_encoded=true', json={'submissions': jobs})
    if not isinstance(result, list) or len(result) != len(tests) or any(not x.get('token') for x in result):
        raise APIError('The code runner did not accept all test cases. No score was recorded.', 503)
    return [x['token'] for x in result]


def poll(tokens):
    result = request('GET', '/submissions/batch', params={'tokens': ','.join(tokens), 'base64_encoded': 'true',
                     'fields': 'token,status,stdout,stderr,compile_output,time,memory'})
    items = result.get('submissions', [])
    if len(items) != len(tokens) or any(not x for x in items):
        raise APIError('The runner returned an incomplete response. Try again shortly.', 503)
    by_token = {x.get('token'): x for x in items}
    if any(token not in by_token for token in tokens): raise APIError('The runner returned mismatched submissions.', 503)
    return [by_token[t] for t in tokens]


def completed(items):
    return all(x['status']['id'] not in (1, 2) for x in items)


def normalize(text):
    return '\n'.join(line.rstrip() for line in text.replace('\r\n', '\n').strip().splitlines())


def passed(item, case):
    return item['status']['id'] == 3 and normalize(decode(item.get('stdout'))) == normalize(case['expected'])
