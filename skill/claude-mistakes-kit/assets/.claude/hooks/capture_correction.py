#!/usr/bin/env python3
# UserPromptSubmit hook: מזהה תיקון בהודעה שלך, רושם אותו, ומזריק לקלוד את הלקחים הפעילים לפני שהוא עונה.
# עם --stop הוא רץ כ-Stop hook: אם בסשן נרשמו תיקונים ולא נוספו ל-lessons/MISTAKES.md רשומות חדשות (שורות "מוסר השכל:" אחרי "## רשומות") במספר התיקונים,
# הוא עוצר את סיום התשובה פעם אחת ומבקש את הרשומות החסרות.
import sys, json, re, os, datetime

FORMAT = ('תאריך | מה קרה, עם ציטוט | הכלל שנשבר | מה בודקים בפעם הבאה | חוזרת ? (כן, עם תאריך קודם, או לא)\n'
          'מוסר השכל: המשפט הכללי.\n'
          'הפתרון שיושם: מה שונה בפועל, עם נתיב. אם לא שונה כלום: "טרם יושם", ומה מוצע.')


def lessons_dir(data):
    return os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd(), "lessons")


def entry_count(base):
    """מספר הרשומות: שורות שמתחילות ב'מוסר השכל:' אחרי הכותרת '## רשומות'. None אם היומן חסר."""
    try:
        t = open(os.path.join(base, "MISTAKES.md"), encoding="utf8").read()
    except OSError:
        return None
    if "## רשומות" in t:
        t = t.split("## רשומות", 1)[1]
    return sum(1 for line in t.splitlines() if line.strip().startswith("מוסר השכל:"))


def pending_path(base, data):
    sid = re.sub(r"[^A-Za-z0-9_-]", "", str(data.get("session_id") or "nosession"))[:80] or "nosession"
    return os.path.join(base, f".pending_entry-{sid}.json")


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if "--stop" in sys.argv[1:]:
    base = lessons_dir(data)
    pending = pending_path(base, data)
    if not os.path.exists(pending):
        sys.exit(0)
    try:
        p = json.load(open(pending, encoding="utf8"))
        needed, baseline = int(p["needed"]), int(p["baseline"])
    except Exception:
        needed, baseline = None, None  # סמן פגום: לא מניחים שהרשומה נכתבה
    now = entry_count(base)
    if needed is not None and now is not None and now >= baseline + needed:
        os.remove(pending)
        sys.exit(0)
    if data.get("stop_hook_active"):
        # כבר חסמנו פעם אחת בתשובה הזו. לא חוסמים שוב, כדי שלא תיווצר לולאה.
        os.remove(pending)
        sys.exit(0)
    if now is None:
        reason = ("[טיפול בטעויות] בסשן נרשם תיקון, ו-lessons/MISTAKES.md חסר. לפני שאתה מסיים, תיצור אותו עם הכותרות "
                  "'# יומן טעויות' ו-'## רשומות', ותוסיף תחת '## רשומות' רשומה בפורמט הזה:\n" + FORMAT)
    elif needed is None:
        reason = ("[טיפול בטעויות] בסשן נרשם תיקון, אבל קובץ המעקב שלו פגום, ולא ידוע אם נוספה רשומה. "
                  "תבדוק ב-lessons/MISTAKES.md שיש רשומה לכל תיקון מהסשן הזה, ואם חסרה, תוסיף אותה בפורמט שבקובץ.")
    else:
        missing = baseline + needed - now
        reason = (f"[טיפול בטעויות] בסשן נרשמו {needed} תיקונים, וב-lessons/MISTAKES.md חסרות {missing} רשומות חדשות. "
                  "לפני שאתה מסיים, תוסיף תחת '## רשומות' רשומה לכל תיקון, בפורמט שבקובץ, עם שורת 'מוסר השכל:' ושורת 'הפתרון שיושם:'. "
                  "אם לדעתך לא טעית, תכתוב את זה ברשומה, עם ציטוט.")
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
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
try:
    p = json.load(open(pending, encoding="utf8"))
    p = {"needed": int(p["needed"]) + 1, "baseline": int(p["baseline"])}
except Exception:
    p = {"needed": 1, "baseline": entry_count(base) or 0}
p["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
with open(pending, "w", encoding="utf8") as f:
    json.dump(p, f)
with open(os.path.join(base, "candidates.jsonl"), "a", encoding="utf8") as f:
    f.write(json.dumps({"ts": p["ts"], "markers": hits, "text": text[:300], "context": context}, ensure_ascii=False) + "\n")

print("[טיפול בטעויות] בהודעה הזו יש תיקון. לפני שאתה עונה:")
print("1. תכתוב איזה כלל נשבר.")
print("2. תבדוק ב-lessons/MISTAKES.md אם טעות כזו כבר הופיעה.")
print("3. תוסיף רשומה תחת '## רשומות', לפי הפורמט שבקובץ, עם מוסר השכל ומה שונה בפועל.")
print("4. אם לדעתך לא טעית, תכתוב למה, עם ציטוט. אל תסכים רק כדי לרצות.")
if not os.path.exists(os.path.join(base, "MISTAKES.md")):
    print("lessons/MISTAKES.md חסר. תיצור אותו עם '# יומן טעויות' ו-'## רשומות', והפורמט הוא:\n" + FORMAT)
rules = os.path.join(base, "LESSONS_ACTIVE.md")
if os.path.exists(rules):
    print(open(rules, encoding="utf8").read())
