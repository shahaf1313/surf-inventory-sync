# Surf Inventory Sync

כלי לעזרה בעדכוני מלאי תקופתיים: קורא את קובץ ה-Excel שמגיע מהיצרן (טופס הזמנה),
מסנן רק פריטים חדשים או מידות חדשות (לפי עמודת "New / Carry over"), וממיר אותם
לפורמט שרווחית (תוכנת ניהול המלאי) מצפה לו בייבוא.

## מצב נוכחי

- [x] קריאת קובץ היצרן וסינון לפי "New / Carry over" — `src/surf_inventory_sync/source_parser.py`
- [ ] המרה לפורמט ייבוא של רווחית — ממתין לדוגמה של קובץ רווחית
- [ ] ממשק משתמש (חלון לבחירת קובץ, תצוגה מקדימה, ייצוא)
- [ ] אריזה כקובץ הפעלה ל-Windows (PyInstaller)
- [ ] (אופציונלי, שלב ב') חיבור אוטומטי לאתר רווחית והעלאה ישירה

## פיתוח

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install pytest
python3 -m pytest tests/
```

## מבנה

```
src/surf_inventory_sync/
  source_parser.py   # פרסור וסינון קובץ היצרן
tests/
  fixtures/           # קבצי דוגמה אמיתיים לבדיקות
  test_source_parser.py
```
