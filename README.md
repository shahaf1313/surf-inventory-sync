# Surf Inventory Sync

כלי לעזרה בעדכוני מלאי תקופתיים: קורא את קובץ ה-Excel שמגיע מהיצרן (טופס הזמנה),
מסנן רק פריטים חדשים או מידות חדשות (לפי עמודת "New / Carry over"), וממיר אותם
לפורמט שרווחית (תוכנת ניהול המלאי) מצפה לו בייבוא.

## מצב נוכחי

- [x] קריאת קובץ היצרן וסינון לפי "New / Carry over" — `src/surf_inventory_sync/source_parser.py`
- [x] הבנת פורמט רווחית ובניית קובץ תואם — `src/surf_inventory_sync/rivhit_format.py`
- [x] מחיר = שער המרה (קלט) × Suggested Retail Price, ומספר פריט התחלתי כקלט —
      `src/surf_inventory_sync/conversion.py`, `config.py`
- [x] ממשק משתמש עם 2 טאבים ("המרה", "הגדרות") — `src/surf_inventory_sync/gui.py`
      (נבדק ידנית עם צילומי מסך; טקסט עברי מוצג נכון בעזרת `python-bidi`)
- [x] לוג של כל המרה (תאריך/שעה, קובץ מקור, שער המרה, מספר פריט התחלתי) —
      `src/surf_inventory_sync/conversion_log.py` (בלי תצוגה בממשק כרגע)
- [x] מחיר מעוגל לשקלים שלמים
- [x] תמיכה בכמה מותגים/תבניות עם ניסוחי עמודות שונים (North Kiteboarding, Mystic)
- [x] אריזה כקובץ הפעלה ל-Windows — בנייה אוטומטית ב-GitHub Actions על
      runner אמיתי של Windows (לא emulation), ראו למטה
- [x] לוגו שחף (וקטורי, נוצר בקוד) — אייקון החלון, קובץ ה-exe, וכותרת באפליקציה
- [ ] (אופציונלי, שלב ב') חיבור אוטומטי לאתר רווחית והעלאה ישירה

כל הפרטים הפתוחים על פורמט רווחית (שנפתרו) מתועדים ב-`docs/rivhit_format_notes.md`.

## הרצה (בזמן פיתוח, על מחשב עם Python)

```bash
python3 -m pip install -r requirements.txt
python3 run_app.py
```

## פיתוח ובדיקות

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install pytest
python3 -m pytest tests/
```

## אריזה ל-Windows (.exe)

הבנייה קורית **אוטומטית** ב-GitHub Actions, על מחשב Windows אמיתי (לא
סימולציה) — כי הפיתוח כאן נעשה בלינוקס, ו-PyInstaller חייב לרוץ על אותה
מערכת הפעלה שעבורה בונים את קובץ ה-exe.

**איך מורידים את קובץ ה-exe המוכן:**

1. בריפו ב-GitHub, לשונית **Actions**.
2. לבחור בהרצה האחרונה של "Build Windows EXE" (רץ אוטומטית אחרי כל שינוי
   בקוד; אפשר גם להריץ ידנית דרך "Run workflow").
3. לגלול למטה ל-**Artifacts**, ולהוריד את `SurfInventorySync-windows` —
   קובץ zip שבתוכו `SurfInventorySync.exe`.

הקובץ שמור שם 90 יום מכל הרצה. אם תרצה קישור קבוע במקום זה (למשל
GitHub Release), תגיד לי.

**לבנות ידנית** (אם יש בכל זאת גישה למחשב Windows עם Python):

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --name "SurfInventorySync" --paths src --icon assets\icon.ico --add-data "assets;assets" run_app.py
```

יווצר קובץ הפעלה בודד תחת `dist/SurfInventorySync.exe`.

## מבנה

```
src/surf_inventory_sync/
  source_parser.py   # פרסור וסינון קובץ היצרן
  rivhit_format.py    # קריאה/כתיבה של פורמט רווחית
  conversion.py        # החיבור בין השניים (משמש גם ה-GUI וגם הבדיקות)
  config.py             # שמירת שער ההמרה ומספר הפריט האחרון בין הרצות
  conversion_log.py      # לוג CSV של כל המרה (תאריך, קובץ, שער המרה, מספר פריט)
  gui.py                 # ממשק המשתמש (Tkinter)
run_app.py                # נקודת כניסה להרצת האפליקציה
assets/
  generate_logo.py         # יוצר את לוגו השחף (וקטורי, ניתן לעריכה) - python3 assets/generate_logo.py
  logo.png, logo_64.png, icon.ico   # פלט מוכן, נטען ע"י gui.py וע"י PyInstaller
tests/
  fixtures/           # קבצי דוגמה אמיתיים לבדיקות
docs/
  rivhit_format_notes.md   # תיעוד פורמט רווחית וההחלטות שהתקבלו
```
