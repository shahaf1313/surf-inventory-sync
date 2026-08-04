# Surf Inventory Sync

כלי לעזרה בעדכוני מלאי תקופתיים: קורא את קובץ ה-Excel שמגיע מהיצרן (טופס הזמנה),
מסנן רק פריטים חדשים או מידות חדשות (לפי עמודת "New / Carry over"), וממיר אותם
לפורמט שרווחית (תוכנת ניהול המלאי) מצפה לו בייבוא.

## מצב נוכחי

- [x] קריאת קובץ היצרן וסינון לפי "New / Carry over" — `src/surf_inventory_sync/source_parser.py`
- [x] הבנת פורמט רווחית ובניית קובץ תואם — `src/surf_inventory_sync/rivhit_format.py`
      (בדיקת קצה-לקצה עוברת: קובץ יצרן אמיתי → סינון → 172 שורות רווחית תקינות)
- [ ] שני פרטים פתוחים לפני שהממיר "אמיתי" מוכן לשימוש: מיפוי שדה המחיר,
      ומקור מספר הפריט ההתחלתי — ראו `docs/rivhit_format_notes.md`
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
