#!/usr/bin/env python3
"""install.py [PROJECT_DIR]
מתקין את ערכת הטיפול בטעויות בפרויקט: hook, יומן, לקחים, hooks ב-settings.json וסעיף ב-CLAUDE.md.
לא מוחק ולא דורס: קובץ יומן או לקחים קיים נשאר, hooks קיימים נשמרים, והסעיף ב-CLAUDE.md נוסף פעם אחת.
בסוף מריץ את בקרה 1 ומוחק את שורת הבדיקה."""
import json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '..', 'assets')
P = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())
done = []
def copy(rel, overwrite):
    src, dst = os.path.join(A, rel), os.path.join(P, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and not overwrite:
        done.append(f'קיים, לא נגעתי: {rel}'); return
    shutil.copy(src, dst); done.append(f'הועתק: {rel}')
copy('.claude/hooks/capture_correction.py', True)
copy('.claude/lessons/MISTAKES.md', False)
copy('.claude/lessons/LESSONS_ACTIVE.md', False)
# settings.json: מיזוג בלי למחוק
sp = os.path.join(P, '.claude', 'settings.json')
new = json.load(open(os.path.join(A, '.claude', 'settings.json'), encoding='utf-8'))
cur = json.load(open(sp, encoding='utf-8')) if os.path.exists(sp) else {}
if os.path.exists(sp): shutil.copy(sp, sp + '.bak-mistakes-kit')
hooks = cur.setdefault('hooks', {})
for event, groups in new['hooks'].items():
    have = {h.get('command') for grp in hooks.get(event, []) for h in grp.get('hooks', [])}
    for g in groups:
        cmd = g['hooks'][0]['command']
        if cmd in have: done.append(f'hook קיים: {event}'); continue
        hooks.setdefault(event, []).append(g); done.append(f'נוסף hook: {event}')
json.dump(cur, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
# CLAUDE.md
cp = os.path.join(P, 'CLAUDE.md'); sec = open(os.path.join(A, 'CLAUDE-section.md'), encoding='utf-8').read().strip()
old = open(cp, encoding='utf-8').read() if os.path.exists(cp) else ''
if sec.splitlines()[1] in old: done.append('הסעיף כבר קיים ב-CLAUDE.md')
else:
    open(cp, 'a', encoding='utf-8').write(('\n\n' if old.strip() else '') + sec + '\n'); done.append('נוסף סעיף ל-CLAUDE.md')
# בקרה 1
hook = os.path.join(P, '.claude', 'hooks', 'capture_correction.py')
cand = os.path.join(P, '.claude', 'lessons', 'candidates.jsonl')
before = open(cand, encoding='utf-8').read() if os.path.exists(cand) else None
env = dict(os.environ, CLAUDE_PROJECT_DIR=P)
r1 = subprocess.run([sys.executable, hook], input='{"prompt":"טעית, כבר אמרתי לך"}', capture_output=True, text=True, env=env)
r0 = subprocess.run([sys.executable, hook], input='{"prompt":"תודה, זה מעולה"}', capture_output=True, text=True, env=env)
after = open(cand, encoding='utf-8').read() if os.path.exists(cand) else ''
ok = r1.stdout.startswith('[טיפול בטעויות]') and r0.stdout == '' and after != (before or '')
if before is None: os.remove(cand)
else: open(cand, 'w', encoding='utf-8').write(before)
print('\n'.join(done))
print('בקרה 1:', 'עברה' if ok else 'נכשלה')
if not ok: print(r1.stdout, r1.stderr, r0.stdout, r0.stderr); sys.exit(1)
print('עכשיו לפתוח סשן חדש של Claude Code ולהריץ /hooks (בקרה 2).')
