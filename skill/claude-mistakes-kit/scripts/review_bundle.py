#!/usr/bin/env python3
"""review_bundle.py weekly|monthly [PROJECT_DIR] : מייצר קובץ אחד עם הפרומפט והקבצים, להדבקה בצ'אט של מודל אחר."""
import os, sys
kind = sys.argv[1] if len(sys.argv) > 1 else 'weekly'
P = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
L = os.path.join(P, '.claude', 'lessons')
WEEKLY = """אתה בודק. לא כתבת את הרשומות האלה, ואין לך את ההסברים של מי שכתב אותן.
לכל רשומה מהשבוע האחרון:
1. סיבת השורש במשפט אחד, עם ציטוט מהרשומה.
2. האם היא חוזרת על רשומה קודמת, ועל איזו.
3. האם "הפתרון שיושם" באמת מונע את הטעות, או רק מבטיח להיזהר.
4. בדיקה אחת שאפשר להוסיף: hook, סקריפט, או בדיקה של קורא לפני שהתוצר יוצא.
בסוף: הדפוסים שחזרו לפחות 3 פעמים, ולכל אחד כלל קצר ל-LESSONS_ACTIVE.md.
אל תבנה דפוס משורה אחת."""
MONTHLY = """מצורפים MISTAKES.md ו-LESSONS_ACTIVE.md.
לכל כלל ב-LESSONS_ACTIVE.md:
1. מתי הוא נוסף.
2. האם אחרי התאריך הזה יש ב-MISTAKES.md רשומה מאותו סוג. אם יש, תצטט אותה.
3. אם הטעות חזרה: איזו בדיקה מכנית (hook או סקריפט) הייתה תופסת אותה, במקום כלל כתוב.
אל תניח שכלל עובד רק מפני שהוא כתוב."""
parts = [WEEKLY if kind == 'weekly' else MONTHLY]
for f in ['MISTAKES.md'] + (['LESSONS_ACTIVE.md'] if kind == 'monthly' else []):
    parts.append(f'===== {f} =====\n' + open(os.path.join(L, f), encoding='utf-8').read())
out = os.path.join(L, f'review-{kind}.txt')
open(out, 'w', encoding='utf-8').write('\n\n'.join(parts))
print(out)
