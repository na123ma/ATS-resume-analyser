"""Run once before starting. Existing .env files are never overwritten."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent
for relative in ['.env', 'backend/.env']:
    target = root / relative
    if target.exists():
        print(f'Keeping existing {relative}')
        continue
    text = (root / (relative + '.example')).read_text(encoding='utf-8')
    text = text.replace('development-only-change-before-deployment', secrets.token_urlsafe(48))
    text = text.replace('change-this-before-starting', secrets.token_hex(24))
    target.write_text(text, encoding='utf-8')
    print(f'Created {relative}')
print('Ready. See README.md for Docker or Windows/local startup.')
