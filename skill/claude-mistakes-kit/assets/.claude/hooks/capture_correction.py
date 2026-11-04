#!/usr/bin/env python3
# UserPromptSubmit hook: מזהה תיקון בהודעה שלך, רושם אותו, ומזריק לקלוד את הלקחים הפעילים לפני שהוא עונה.
# לכל תיקון יש מזהה (למשל #mk-3f9a1c), וקלוד מתבקש לכתוב אותו ברשומה ב-lessons/MISTAKES.md.
# עם --stop הוא רץ כ-Stop hook: אם מזהה של תיקון מהסשן לא מופיע ביומן, הוא עוצר את סיום התשובה ומבקש רשומה.
# חסימה אחת לכל תשובה, כדי שלא תיווצר לולאה. המעקב נשאר פתוח, והחסימה חוזרת בתשובה הבאה עד שהמזהה מופיע.
# המגבלה: ה-hook בודק שהמזהה מופיע ביומן, ולא בודק את איכות הרשומה.
import sys, json, re, os, datetime, secrets

FORMAT = ('תאריך | מזהה התיקון | מה קרה, עם ציטוט | הכלל שנשבר | מה בודקים בפעם הבאה | חוזרת ? (כן, עם תאריך קודם, או לא)\n'
          'מוסר השכל: המשפט הכללי.\n'
          'הפתרון שיושם: מה שונה בפועל, עם נתיב. אם לא שונה כלום: "טרם יושם", ומה מוצע.')


def lessons_dir(data):
    return os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd(), "lessons")


def read_log(base):
    try:
        return open(os.path.join(base, "MISTAKES.md"), encoding="utf8").read()
    except OSError:
        return None


def pending_path(base, data):
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(data.get("session_id") or "nosession"))[:80] or "nosession"
    return os.path.join(base, f".pending_entry-{sid}.json")


def load_pending(path):
    """מחזיר (ids, corrupt). סמן פגום לא מתאפס: הוא נשמר בצד ומסומן, כדי שתיקונים קודמים לא ייעלמו מהמעקב."""
    if not os.path.exists(path):
        return [], False
    try:
        p = json.load(open(path, encoding="utf8"))
        ids = [str(i) for i in p["ids"]]
        return ids, bool(p.get("corrupt"))
    except Exception:
        keep = f"{path}.corrupt-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        os.replace(path, keep)
        return [], True


def save_pending(path, ids, corrupt):
    with open(path, "w", encoding="utf8") as f:
        json.dump({"ids": ids, "corrupt": corrupt, "ts": datetime.datetime.now().isoformat(timespec="seconds")}, f)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if "--stop" in sys.argv[1:]:
    base = lessons_dir(data)
    pending = pending_path(base, data)
    if not os.path.exists(pending):
        sys.exit(0)
    ids, corrupt = load_pending(pending)
    log = read_log(base)
    missing = [i for i in ids if log is None or i not in log]
    if not missing and not corrupt:
        os.remove(pending)
        sys.exit(0)
    if data.get("stop_hook_active"):
        # כבר חסמנו פעם אחת בתשובה הזו. לא חוסמים שוב, אבל המעקב נשאר פתוח לתשובה הבאה.
        save_pending(pending, missing, False)
        sys.exit(0)
    save_pending(pending, missing, False)
    parts = ["[טיפול בטעויות] לפני שאתה מסיים:"]
    if log is None:
        parts.append("lessons/MISTAKES.md חסר. תיצור אותו עם הכותרות '# יומן טעויות' ו-'## רשומות'.")
    if missing:
        parts.append("חסרה ב-lessons/MISTAKES.md רשומה לתיקונים האלה: " + ", ".join(missing) + ". "
                     "תוסיף תחת '## רשומות' רשומה לכל אחד, עם המזהה שלו, בפורמט:\n" + FORMAT)
    if corrupt:
        parts.append("קובץ המעקב היה פגום, ולכן ייתכן שיש בסשן תיקונים קודמים בלי רשומה. תבדוק בשיחה ותוסיף רשומה לכל תיקון שחסר.")
    parts.append("אם לדעתך לא טעית, תכתוב את זה ברשומה, עם ציטוט.")
    print(json.dumps({"decision": "block", "reason": "\n".join(parts)}, ensure_ascii=False))
    sys.exit(0)

text = (data.get("prompt") or "")[:1500]
if not text:
    sys.exit(0)

# ביטויים שאתה משתמש בהם כשאתה מתקן. כדאי להתאים לשפה שלך.
MARKERS = [r"טעית", r"לא נכון", r"אתה אמור", r"כבר אמרתי", r"ביקשתי", r"לא בדקת", r"שוב ",
           r"\bwrong\b", r"you should have", r"I already told you"]
found = [(m, re.search(m, text, flags=re.I)) for m in MARKERS]
found = [(m, x) for m, x in found if x]
if not found:
    sys.exit(0)
hits = [m for m, x in found]
# שומרים את תחילת ההודעה וגם קטע סביב הביטוי הראשון, כדי שתיקון בסוף הודעה ארוכה לא יאבד
pos = min(x.start() for m, x in found)
context = text[max(0, pos - 200):pos + 200]

base = lessons_dir(data)
os.makedirs(base, exist_ok=True)
pending = pending_path(base, data)
ids, corrupt = load_pending(pending)
cid = "#mk-" + secrets.token_hex(3)
ids.append(cid)
save_pending(pending, ids, corrupt)
ts = datetime.datetime.now().isoformat(timespec="seconds")
with open(os.path.join(base, "candidates.jsonl"), "a", encoding="utf8") as f:
    f.write(json.dumps({"ts": ts, "id": cid, "markers": hits, "text": text[:300], "context": context}, ensure_ascii=False) + "\n")

print(f"[טיפול בטעויות] בהודעה הזו יש תיקון, והמזהה שלו {cid}. לפני שאתה עונה:")
print("1. תכתוב איזה כלל נשבר.")
print("2. תבדוק ב-lessons/MISTAKES.md אם טעות כזו כבר הופיעה.")
print(f"3. תוסיף רשומה תחת '## רשומות', לפי הפורמט שבקובץ, עם המזהה {cid}, מוסר השכל ומה שונה בפועל.")
print("4. אם לדעתך לא טעית, תכתוב למה, עם ציטוט. אל תסכים רק כדי לרצות.")
if read_log(base) is None:
    print("lessons/MISTAKES.md חסר. תיצור אותו עם '# יומן טעויות' ו-'## רשומות', והפורמט הוא:\n" + FORMAT)
rules = os.path.join(base, "LESSONS_ACTIVE.md")
if os.path.exists(rules):
    print(open(rules, encoding="utf8").read())
