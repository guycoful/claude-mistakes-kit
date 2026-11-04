#!/usr/bin/env python3
"""install.py [PROJECT_DIR]
מתקין את ערכת הטיפול בטעויות בפרויקט: hook, יומן, לקחים, hooks ב-settings.json וסעיף ב-CLAUDE.md.
לא מוחק ולא דורס: קובץ יומן או לקחים קיים נשאר, hooks קיימים נשמרים, והסעיף ב-CLAUDE.md נוסף פעם אחת.
אם כבר יש capture_correction.py שונה, ה-hook של הערכה מותקן בשם נפרד (mistakes_kit_capture.py), וה-hook שלך לא מורץ.
גיבוי של settings.json נוצר רק כשההגדרות משתנות, עם תאריך ושעה בשם, ולא דורס גיבוי קודם.
בסוף מריץ את בקרה 1 בתיקייה זמנית, על ה-hook של הערכה בלבד."""
import datetime, difflib, json, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '..', 'assets')
FORCE = '--force' in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith('--')]
P = os.path.abspath(args[0] if args else os.getcwd())
done = []
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
def backup(path):
    b = f'{path}.bak-mistakes-kit-{STAMP}'
    i = 1
    while os.path.exists(b): b = f'{path}.bak-mistakes-kit-{STAMP}-{i}'; i += 1
    shutil.copy(path, b); return b
def copy(rel, dst_rel=None):
    src, dst = os.path.join(A, rel), os.path.join(P, dst_rel or rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        if open(src, encoding='utf-8').read() == open(dst, encoding='utf-8').read():
            done.append(f'זהה, לא נגעתי: {dst_rel or rel}'); return
        done.append(f'קיים, לא נגעתי: {dst_rel or rel}'); return
    shutil.copy(src, dst); done.append(f'הועתק: {dst_rel or rel}')
# ה-hook: לא נוגעים בקובץ שאינו של הערכה ולא מריצים אותו. בוחרים את השם הראשון שפנוי או שכבר מכיל בדיוק את ה-hook של הערכה.
HOOK_SRC = open(os.path.join(A, '.claude', 'hooks', 'capture_correction.py'), encoding='utf-8').read()
def same(path): return os.path.exists(path) and open(path, encoding='utf-8').read() == HOOK_SRC
names = ['capture_correction.py', 'mistakes_kit_capture.py'] + [f'mistakes_kit_capture_{i}.py' for i in range(2, 20)]
main = os.path.join(P, '.claude', 'hooks', names[0])
if FORCE and os.path.exists(main) and not same(main):
    done.append(f'--force: ה-hook הקיים נשמר כ-{os.path.basename(backup(main))}')
    os.remove(main)
HOOK_REL = None
for nm in names:
    path = os.path.join(P, '.claude', 'hooks', nm)
    if same(path): HOOK_REL = f'.claude/hooks/{nm}'; done.append(f'זהה, לא נגעתי: {HOOK_REL}'); break
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'x', encoding='utf-8').write(HOOK_SRC); HOOK_REL = f'.claude/hooks/{nm}'; done.append(f'הועתק: {HOOK_REL}'); break
    done.append(f'יש כבר {nm} שאינו ה-hook של הערכה. לא נגעתי בו ולא הרצתי אותו.')
if not HOOK_REL: print('\n'.join(done)); print('לא נמצא שם פנוי ל-hook. ההתקנה נעצרה בלי לשנות את settings.json.'); sys.exit(1)
if HOOK_REL != '.claude/hooks/capture_correction.py':
    done.append(f'ה-hook של הערכה הותקן בשם {os.path.basename(HOOK_REL)}, ו-settings.json יפנה אליו.')
copy('.claude/lessons/MISTAKES.md')
copy('.claude/lessons/LESSONS_ACTIVE.md')
# בקרה 5 צריכה קובץ מועמדים. נוצר ריק רק אם אין, בלי דריסה
cf = os.path.join(P, '.claude', 'lessons', 'candidates.jsonl')
if not os.path.exists(cf): open(cf, 'x', encoding='utf-8').close(); done.append('נוצר קובץ ריק: .claude/lessons/candidates.jsonl')
# settings.json: מיזוג בלי למחוק
sp = os.path.join(P, '.claude', 'settings.json')
new = json.load(open(os.path.join(A, '.claude', 'settings.json'), encoding='utf-8'))
cur = json.load(open(sp, encoding='utf-8')) if os.path.exists(sp) else {}
before = json.dumps(cur, sort_keys=True)
hooks = cur.setdefault('hooks', {})
for event, groups in new['hooks'].items():
    have = {h.get('command') for grp in hooks.get(event, []) for h in grp.get('hooks', [])}
    for g in groups:
        g = json.loads(json.dumps(g).replace('capture_correction.py', os.path.basename(HOOK_REL)))
        cmd = g['hooks'][0]['command']
        if cmd in have: done.append(f'hook קיים: {event}'); continue
        hooks.setdefault(event, []).append(g); done.append(f'נוסף hook: {event}')
if json.dumps(cur, sort_keys=True) != before:
    if os.path.exists(sp): done.append(f'גיבוי של settings.json: {os.path.basename(backup(sp))}')
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    json.dump(cur, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
else: done.append('settings.json לא השתנה, ולא נוצר גיבוי')
# CLAUDE.md
cp = os.path.join(P, 'CLAUDE.md'); sec = open(os.path.join(A, 'CLAUDE-section.md'), encoding='utf-8').read().strip()
old = open(cp, encoding='utf-8').read() if os.path.exists(cp) else ''
if sec.splitlines()[1] in old: done.append('הסעיף כבר קיים ב-CLAUDE.md')
else:
    open(cp, 'a', encoding='utf-8').write(('\n\n' if old.strip() else '') + sec + '\n'); done.append('נוסף סעיף ל-CLAUDE.md')
# בקרה 1: רצה בתיקיית זמנית, כדי לא לגעת ב-candidates.jsonl האמיתי
hook = os.path.join(P, HOOK_REL)  # רק ה-hook של הערכה, אף פעם לא hook אחר שלך
if open(hook, encoding='utf-8').read() != open(hsrc, encoding='utf-8').read():
    print('\n'.join(done)); print('בקרה 1: לא הורצה. הקובץ ב-' + HOOK_REL + ' אינו ה-hook של הערכה, ולכן לא הרצתי אותו.'); sys.exit(1)
tmp = tempfile.mkdtemp(prefix='mk-check-')
env = dict(os.environ, CLAUDE_PROJECT_DIR=tmp)
r1 = subprocess.run([sys.executable, hook], input='{"prompt":"טעית, כבר אמרתי לך"}', capture_output=True, text=True, env=env)
r0 = subprocess.run([sys.executable, hook], input='{"prompt":"תודה, זה מעולה"}', capture_output=True, text=True, env=env)
cand = os.path.join(tmp, '.claude', 'lessons', 'candidates.jsonl')
n = len(open(cand, encoding='utf-8').read().splitlines()) if os.path.exists(cand) else 0
ok = r1.stdout.startswith('[טיפול בטעויות]') and r0.stdout == '' and n == 1
shutil.rmtree(tmp, ignore_errors=True)
print('\n'.join(done))
print('בקרה 1:', 'עברה' if ok else 'נכשלה')
if not ok:
    print('ה-hook של הערכה לא הגיב כמצופה. פלט:')
    print((r1.stdout + r1.stderr + r0.stdout + r0.stderr).strip() or '(ריק)'); sys.exit(1)
print('עכשיו לפתוח סשן חדש של Claude Code ולהריץ /hooks (בקרה 2).')
