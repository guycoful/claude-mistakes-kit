#!/usr/bin/env python3
# UserPromptSubmit hook: מזהה תיקון בהודעה שלך, רושם אותו, ומזריק לקלוד את הלקחים הפעילים לפני שהוא עונה.
import sys, json, re, os, datetime

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
text = (data.get("prompt") or "")[:1500]
if not text:
    sys.exit(0)

# ביטויים שאתה משתמש בהם כשאתה מתקן. כדאי להתאים לשפה שלך.
MARKERS = [r"טעית", r"לא נכון", r"אתה אמור", r"כבר אמרתי", r"ביקשתי", r"לא בדקת", r"שוב ",
           r"\bwrong\b", r"you should have", r"I already told you"]
hits = [m for m in MARKERS if re.search(m, text, flags=re.I)]
if not hits:
    sys.exit(0)

base = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd(), ".claude", "lessons")
os.makedirs(base, exist_ok=True)
with open(os.path.join(base, "candidates.jsonl"), "a", encoding="utf8") as f:
    f.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"),
                        "markers": hits, "text": text[:600]}, ensure_ascii=False) + "\n")

print("[טיפול בטעויות] בהודעה הזו יש תיקון. לפני שאתה עונה:")
print("1. תכתוב איזה כלל נשבר.")
print("2. תבדוק ב-.claude/lessons/MISTAKES.md אם טעות כזו כבר הופיעה.")
print("3. תוסיף רשומה לפי הפורמט שבקובץ, עם מוסר השכל ומה שונה בפועל.")
print("4. אם לדעתך לא טעית, תכתוב למה, עם ציטוט. אל תסכים רק כדי לרצות.")
rules = os.path.join(base, "LESSONS_ACTIVE.md")
if os.path.exists(rules):
    print(open(rules, encoding="utf8").read())
