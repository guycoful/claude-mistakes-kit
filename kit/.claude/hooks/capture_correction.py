#!/usr/bin/env python3
# UserPromptSubmit hook: מזהה תיקון בהודעה שלך, רושם אותו, ומזריק לקלוד את הלקחים הפעילים לפני שהוא עונה.
# עם --stop הוא רץ כ-Stop hook: אם נרשם תיקון ו-MISTAKES.md לא השתנה, הוא עוצר את סיום התשובה פעם אחת ומבקש רשומה.
import sys, json, re, os, datetime, hashlib


def lessons_dir(data):
    return os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd(), ".claude", "lessons")


def mistakes_sig(base):
    try:
        return hashlib.sha256(open(os.path.join(base, "MISTAKES.md"), "rb").read()).hexdigest()
    except OSError:
        return ""

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

if "--stop" in sys.argv[1:]:
    base = lessons_dir(data)
    pending = os.path.join(base, ".pending_entry.json")
    if not os.path.exists(pending):
        sys.exit(0)
    try:
        before = json.load(open(pending, encoding="utf8")).get("mistakes_sig", "")
    except Exception:
        before = ""
    if mistakes_sig(base) != before or data.get("stop_hook_active"):
        os.remove(pending)
        sys.exit(0)
    print(json.dumps({"decision": "block", "reason":
        "[טיפול בטעויות] בהודעה האחרונה נרשם תיקון, ו-.claude/lessons/MISTAKES.md לא השתנה. "
        "לפני שאתה מסיים, תוסיף שם רשומה לפי הפורמט שבקובץ, עם מוסר השכל ומה שונה בפועל. "
        "אם לדעתך לא טעית, תוסיף רשומה שמסבירה למה, עם ציטוט."}, ensure_ascii=False))
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
with open(os.path.join(base, ".pending_entry.json"), "w", encoding="utf8") as f:
    json.dump({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "mistakes_sig": mistakes_sig(base)}, f)
with open(os.path.join(base, "candidates.jsonl"), "a", encoding="utf8") as f:
    f.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                        "markers": hits, "text": text[:300], "context": context}, ensure_ascii=False) + "\n")

print("[טיפול בטעויות] בהודעה הזו יש תיקון. לפני שאתה עונה:")
print("1. תכתוב איזה כלל נשבר.")
print("2. תבדוק ב-.claude/lessons/MISTAKES.md אם טעות כזו כבר הופיעה.")
print("3. תוסיף רשומה לפי הפורמט שבקובץ, עם מוסר השכל ומה שונה בפועל.")
print("4. אם לדעתך לא טעית, תכתוב למה, עם ציטוט. אל תסכים רק כדי לרצות.")
rules = os.path.join(base, "LESSONS_ACTIVE.md")
if os.path.exists(rules):
    print(open(rules, encoding="utf8").read())
