#!/usr/bin/env python3
"""status.py [PROJECT_DIR] : מצב היומן. כמה רשומות, כמה חוזרות, רשומות לא גמורות, ותיקונים שנתפסו בלי רשומה."""
import json, os, re, sys
P = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
L = os.path.join(P, '.claude', 'lessons')
m = open(os.path.join(L, 'MISTAKES.md'), encoding='utf-8').read()
body = m.split('## רשומות', 1)[1] if '## רשומות' in m else ''
entries = [b.strip() for b in re.split(r'\n(?=\d{1,2}[./]\d{1,2}[./]\d{2,4}\s*\|)', '\n' + body) if b.strip()]
def last_col(e): return e.split('\n')[0].split('|')[-1].strip().strip('"״“”').strip()
rec = [e for e in entries if last_col(e).startswith('כן')]
bad = [e.split('\n')[0][:80] for e in entries if 'מוסר השכל:' not in e or 'הפתרון שיושם:' not in e]
pending = [e.split('\n')[0][:80] for e in entries if re.search(r'הפתרון שיושם:\s*["״“”]?\s*טרם יושם', e)]
cf = os.path.join(L, 'candidates.jsonl')
cand = sum(1 for _ in open(cf, encoding='utf-8')) if os.path.exists(cf) else 0
rules = [l for l in open(os.path.join(L, 'LESSONS_ACTIVE.md'), encoding='utf-8').read().splitlines() if l.strip().startswith(('-', '*')) or re.match(r'\d+\.', l.strip())]
print(f'רשומות ביומן: {len(entries)}')
print(f'מסומנות חוזרות: {len(rec)}')
print(f'כללים פעילים: {len(rules)}')
print(f'שורות ב-candidates.jsonl (מועמדים לתיקון): {cand}')
if cand > len(entries): print(f'  יש {cand - len(entries)} מועמדים יותר מרשומות. זה סימן לבדיקה ולא מסקנה: כמה שורות יכולות להיות אותו תיקון, וביטוי יכול להופיע גם בהודעה שאינה תיקון. תעברו על candidates.jsonl.')
if bad: print('רשומות לא גמורות (חסר מוסר השכל או הפתרון שיושם):'); [print('  ' + b) for b in bad]
if pending: print('"טרם יושם", כלומר עוד אין מנגנון:'); [print('  ' + b) for b in pending]
