# טיפול בטעויות של קלוד קוד

ערכה שהופכת כל תיקון של קלוד קוד לרשומה ביומן, ודפוס שחוזר לכלל שנטען בכל סשן.

הדף עם כל הפרומפטים והבקרות: https://guycoful.github.io/claude-mistakes-kit/

הקבצים בתיקייה kit/:
- .claude/hooks/capture_correction.py: hook של UserPromptSubmit שמזהה תיקון ורושם אותו. עם --stop הוא רץ כ-hook של Stop, ועוצר את סיום התשובה פעם אחת אם נרשם תיקון ו-MISTAKES.md לא השתנה
- .claude/settings.json: רישום ה-hooks (UserPromptSubmit, Stop ו-SessionStart)
- .claude/lessons/MISTAKES.md: תבנית היומן
- .claude/lessons/LESSONS_ACTIVE.md: הלקחים שנטענים בתחילת סשן
- CLAUDE-section.md: הסעיף להוספה ל-CLAUDE.md

## הסקיל הנלווה
בתיקייה skill/claude-mistakes-kit/ יש סקיל ל-Claude Code. הוא מתקין את הערכה בפקודה אחת, רושם טעויות בפורמט קבוע, ומציג מצב יומן. הוא גם מכין קובץ לבדיקה שבועית וחודשית במודל אחר, ומחייב ראיה לפני "בוצע".

התקנה:
```bash
git clone https://github.com/guycoful/claude-mistakes-kit.git /tmp/mk
cp -r /tmp/mk/skill/claude-mistakes-kit ~/.claude/skills/
python3 ~/.claude/skills/claude-mistakes-kit/scripts/install.py "$PWD"
```
אחרי ההתקנה פותחים סשן חדש ומריצים /hooks.
