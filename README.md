# טיפול בטעויות של קלוד קוד

ערכה שהופכת כל תיקון של קלוד קוד לרשומה ביומן, ודפוס שחוזר לכלל שנטען בכל סשן.

הדף עם כל הפרומפטים והבקרות: https://guycoful.github.io/claude-mistakes-kit/

הקבצים בתיקייה kit/:
- .claude/hooks/capture_correction.py: hook של UserPromptSubmit שמזהה תיקון ורושם אותו
- .claude/settings.json: רישום ה-hooks (UserPromptSubmit ו-SessionStart)
- .claude/lessons/MISTAKES.md: תבנית היומן
- .claude/lessons/LESSONS_ACTIVE.md: הלקחים שנטענים בתחילת סשן
- CLAUDE-section.md: הסעיף להוספה ל-CLAUDE.md
