import io
import re
from pypdf import PdfReader
from ..security import APIError
from ..schemas import ResumeAdvice
from .ai import generate

SKILLS = {
 'Python': ['python', 'django', 'flask', 'fastapi', 'pytest', 'pandas', 'rest', 'sql', 'git'],
 'JavaScript': ['javascript', 'typescript', 'node.js', 'express', 'react', 'html', 'css', 'rest', 'git'],
 'React': ['react', 'javascript', 'typescript', 'hooks', 'redux', 'html', 'css', 'testing', 'git'],
 'Django': ['django', 'python', 'rest', 'orm', 'postgresql', 'authentication', 'testing', 'git'],
 'SQL': ['sql', 'mysql', 'postgresql', 'joins', 'indexes', 'transactions', 'normalization'],
 'Java': ['java', 'spring', 'junit', 'maven', 'sql', 'rest', 'git'],
}
EXTRA = ['mongodb', 'docker', 'aws', 'azure', 'linux', 'bootstrap', 'tailwind', 'flutter', 'dart', 'machine learning', 'power bi']
SECTION_PATTERNS = {
 'summary': r'^(?:professional\s+)?(?:summary|profile|objective|career objective)\s*:?$',
 'skills': r'^(?:technical\s+|core\s+)?(?:skills|technologies|technical expertise)\s*:?$',
 'education': r'^(?:education|academic qualifications|academic background)\s*:?$',
 'experience': r'^(?:(?:work|professional|internship)\s+)?(?:experience|employment|internships?)\s*:?$',
 'projects': r'^(?:(?:academic|personal|technical)\s+)?projects?\s*:?$',
}
ACTIONS = r'\b(built|developed|implemented|designed|improved|reduced|increased|created|automated|tested|deployed|integrated|optimized|led|delivered|managed)\b'


def read_pdf(upload):
    if not upload or upload.size > 5 * 1024 * 1024:
        raise APIError('Upload a PDF smaller than 5 MB.')
    raw = upload.read()
    if not raw.startswith(b'%PDF-'):
        raise APIError('This file is not a valid PDF.')
    try:
        reader = PdfReader(io.BytesIO(raw), strict=False)
        if reader.is_encrypted:
            raise APIError('Remove the PDF password before uploading.')
        if not 1 <= len(reader.pages) <= 10:
            raise APIError('Please upload a resume with 1 to 10 pages.')
        parts = []
        for page in reader.pages:
            contents = page.get_contents()
            if contents and len(contents.get_data()) > 5 * 1024 * 1024:
                raise APIError('The PDF is too complex. Export a simpler text-based PDF.')
            parts.append(page.extract_text() or '')
        text = '\n'.join(parts).strip()[:40000]
    except APIError:
        raise
    except Exception:
        raise APIError('We could not read this PDF. Export a fresh text-based PDF and try again.')
    if len(re.findall(r'\w+', text)) < 40:
        raise APIError('This PDF contains too little readable text. Scanned images need OCR first; export a selectable-text PDF.')
    return text, len(reader.pages)


def analyze(text, pages, technology='', use_ai=False):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    words = re.findall(r'\b[\w+#.]+\b', text)
    low = text.lower()
    sections = {name: any(re.match(pattern, line, re.I) for line in lines) for name, pattern in SECTION_PATTERNS.items()}
    known = sorted(set(sum(SKILLS.values(), []) + EXTRA))
    found = [s for s in known if re.search(r'(?<!\w)' + re.escape(s) + r'(?!\w)', low)]
    chosen = technology if technology in SKILLS else (max(SKILLS, key=lambda t: len(set(SKILLS[t]) & set(found))) if found else '')
    expected = SKILLS.get(chosen, [])
    missing = [s for s in expected if s not in found]
    checks = []
    def check(category, passed, title, fix, weight=1):
        checks.append({'category': category, 'passed': bool(passed), 'title': title, 'recommendation': fix, 'weight': weight})
    check('ATS friendliness', bool(re.search(r'[^\s@]+@[^\s@]+\.[^\s@]+', text)), 'Email is readable', 'Add a plain-text professional email address.')
    check('ATS friendliness', bool(re.search(r'(?:\+?\d[\d ()-]{7,}\d)', text)), 'Phone number is readable', 'Add your phone number as selectable text.')
    check('ATS friendliness', len(words) >= 150, 'Enough selectable text', 'Export from a document editor and include substantive education and project details.')
    check('ATS friendliness', pages <= 2, 'Concise page count', 'For an early-career resume, aim for one or two focused pages.')
    check('Readability', 250 <= len(words) <= 900, 'Focused resume length', 'Aim for roughly 250–900 relevant words; adjust to your experience.')
    check('Readability', sum(len(x.split()) > 35 for x in lines) <= max(2, len(lines) // 8), 'Manageable text blocks', 'Break long paragraphs into short achievement bullets.')
    check('Readability', not re.search(r'\b(i am|myself|i have)\b', low), 'Direct professional wording', 'Use concise action statements instead of first-person introductions.')
    for key, label in [('skills', 'Skills'), ('education', 'Education')]:
        check('Structure', sections[key], f'{label} heading found', f'Use a standard {label} heading on its own line.')
    check('Structure', sections['experience'] or sections['projects'], 'Experience or projects section found', 'Add Projects or Experience with your own contributions and outcomes.', 2)
    check('Keywords', len(found) >= 4, 'Technical skills are identifiable', 'List specific technologies you can demonstrate rather than generic skill labels.')
    check('Keywords', any(re.search(ACTIONS, x, re.I) for x in lines), 'Action verbs found', 'Start relevant bullets with verbs such as Built, Tested or Improved.')
    check('Keywords', not expected or len(set(found) & set(expected)) >= 3, 'Relevant technology terms found', 'Review suggested terms for your field and add only skills you actually have.')
    action_lines = [x for x in lines if re.search(ACTIONS, x, re.I)]
    quantified = [x for x in action_lines if re.search(r'\b\d+(?:\.\d+)?\s*(?:%|users?|requests?|seconds?|hours?|tests?|pages?|endpoints?|records?|projects?|ms\b)', x, re.I)]
    check('Evidence', bool(action_lines), 'Contributions described', 'Describe what you personally built, tested or delivered.')
    check('Evidence', bool(quantified), 'A specific outcome or scope is stated', 'Add real scope or results where available, such as tested endpoints or time saved. Do not invent numbers.', 2)
    check('Consistency', '\ufffd' not in text, 'No replacement-character extraction errors', 'Use an embedded standard font and export the PDF again.')
    check('Consistency', len(set(x.casefold() for x in action_lines)) == len(action_lines), 'No repeated achievement lines', 'Remove duplicate bullets and focus each line on a distinct contribution.')
    dates = set()
    if re.search(r'\b\d{1,2}/\d{4}\b', text): dates.add('numeric')
    if re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b', text, re.I): dates.add('written')
    check('Consistency', len(dates) <= 1, 'Date styles appear consistent', 'Use one date style throughout, such as Aug 2025.')
    weights = {'ATS friendliness': 25, 'Readability': 15, 'Structure': 20, 'Keywords': 15, 'Evidence': 15, 'Consistency': 10}
    categories = []
    for name, weight in weights.items():
        group = [c for c in checks if c['category'] == name]
        score = round(100 * sum(c['weight'] for c in group if c['passed']) / sum(c['weight'] for c in group))
        categories.append({'name': name, 'score': score, 'weight': weight})
    total = round(sum(c['score'] * c['weight'] / 100 for c in categories))
    report = {'score': total, 'categories': categories, 'checks': checks, 'skills': found,
              'suggested_keywords': missing, 'technology': chosen, 'word_count': len(words), 'page_count': pages,
              'notice': 'Estimated resume-readiness score, not a score from an employer ATS. No job description is used. Visual columns, tables, reading order and every ATS parser cannot be verified by this text-based check.',
              'ai': None, 'source': 'Rule-based checks', 'ai_notice': ''}
    if use_ai:
        result, source = generate('resume', 'Review this resume for an early-career applicant. Give precise actionable recommendations based only on the supplied resume. Do not invent facts or guarantee an ATS result. Do not assign another score.', {'resume': text[:16000], 'target_technology': chosen, 'checks': checks}, ResumeAdvice)
        report['ai'] = result.model_dump() if result else None
        report['source'] = source if result else 'Rule-based checks'
        report['ai_notice'] = '' if result else source
    return report
