"""Desktop UI (Tkinter - ships with standard Python on Windows, no extra
install needed). Two tabs:

  - "המרה" (Convert): pick the manufacturer file, preview what will be
    exported, and save the Rivhit file.
  - "הגדרות" (Settings): the exchange rate and the starting item number,
    both entered by hand each run per the user's workflow. Values are
    pre-filled from the last run as a convenience default, but always
    editable.

Every successful export is still logged (date/time, source file, exchange
rate, starting item number) via conversion_log.py, even though there's no
"History" tab showing it anymore (removed per user request) - the log
itself stays, in case a UI for it is wanted again later.

Business logic lives in conversion.py/rivhit_format.py/source_parser.py and
is unit-tested there; this module is a thin, mostly-untested UI layer over
it (Tkinter widgets aren't practical to unit test - keep this file simple
and push any real logic down into the tested modules instead).
"""

from __future__ import annotations

import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from bidi.algorithm import get_display

from .config import Settings, load_settings, save_settings
from .conversion import ConversionResult, export_to_rivhit_file, run_conversion
from .conversion_log import ConversionLogEntry, append_log_entry


def asset_path(filename: str) -> Path:
    """Resolves a file under assets/, both running from source and when
    frozen into a PyInstaller .exe (which unpacks bundled data next to
    sys._MEIPASS rather than next to this source file)."""
    base = Path(getattr(sys, "_MEIPASS", None) or Path(__file__).resolve().parents[2])
    return base / "assets" / filename


APP_TITLE = "פריטי מלאי חדשים לרווחית"


def rtl(text: str) -> str:
    """Reorder text (Hebrew, or mixed Hebrew/Latin/numbers) into visual
    left-to-right glyph order for display in Tk widgets specifically.

    This is needed on Linux, where Tk draws text as a flat glyph run with
    no Unicode Bidirectional Algorithm support (confirmed via screenshot
    during development - Hebrew rendered mirrored/reversed). It is NOT
    needed on Windows - confirmed via real testing on the target machine:
    Windows' Tk renders Hebrew correctly on its own (likely via GDI/
    Uniscribe doing bidi shaping under the hood), so applying this on top
    there double-reverses it back into mirrored text. Hence the platform
    check below, rather than always applying or always skipping it.
    """
    if sys.platform.startswith("win"):
        return text
    # Reorder each line independently - running the algorithm across an
    # embedded newline can bleed direction across lines incorrectly.
    return "\n".join(get_display(line) for line in text.split("\n"))


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(rtl(APP_TITLE))
        self.geometry("900x640")

        # Keep references on self - Tk doesn't hold its own reference to a
        # PhotoImage, so it gets garbage-collected (and the icon vanishes)
        # if the only reference is a local variable here.
        self._window_icon = tk.PhotoImage(file=str(asset_path("logo.png")))
        self.iconphoto(True, self._window_icon)

        self.settings = load_settings()
        self.selected_file: Path | None = None
        self.last_result: ConversionResult | None = None

        self._build_header()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.convert_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)
        notebook.add(self.convert_tab, text=rtl("המרה"))
        notebook.add(self.settings_tab, text=rtl("הגדרות"))

        self._build_settings_tab()
        self._build_convert_tab()

    # ---------------------------------------------------------------- header
    def _build_header(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", padx=8, pady=(8, 0))

        self._header_logo = tk.PhotoImage(file=str(asset_path("logo_64.png")))
        ttk.Label(header, image=self._header_logo).pack(side="right", padx=(0, 10))
        ttk.Label(
            header,
            text=rtl(APP_TITLE),
            font=("TkDefaultFont", 14, "bold"),
            justify="right",
        ).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8, pady=8)

    # ---------------------------------------------------------------- settings tab
    def _build_settings_tab(self) -> None:
        frame = self.settings_tab
        pad = {"padx": 10, "pady": 8}

        ttk.Label(
            frame,
            text=rtl("שער המרה (מחיר לצרכן בקובץ היצרן X שער המרה = מחיר לצרכן ברווחית)"),
            justify="right",
        ).grid(row=0, column=1, sticky="e", **pad)
        self.exchange_rate_var = tk.StringVar(value=str(self.settings.exchange_rate))
        ttk.Entry(frame, textvariable=self.exchange_rate_var, width=15, justify="right").grid(
            row=0, column=0, sticky="w", **pad
        )

        ttk.Label(frame, text=rtl("מספר פריט התחלתי ברווחית"), justify="right").grid(
            row=1, column=1, sticky="e", **pad
        )
        self.start_id_var = tk.StringVar(value=str(self.settings.next_item_number))
        ttk.Entry(frame, textvariable=self.start_id_var, width=15, justify="right").grid(
            row=1, column=0, sticky="w", **pad
        )

        ttk.Label(
            frame,
            text=rtl(
                "שני השדות ניתנים לעריכה בכל המרה. הערכים כאן הם רק ברירת מחדל\n"
                "(מתעדכנים אוטומטית אחרי ייצוא מוצלח, לפי המספר הבא בתור)."
            ),
            justify="right",
            foreground="#666",
        ).grid(row=2, column=0, columnspan=2, sticky="e", padx=10, pady=(20, 0))

    def _read_settings_from_ui(self) -> tuple[float, int]:
        """Parse and validate the settings fields; raises ValueError with a
        Hebrew message on bad input."""
        try:
            exchange_rate = float(self.exchange_rate_var.get())
        except ValueError:
            raise ValueError("שער ההמרה חייב להיות מספר (למשל 3.7)") from None
        if exchange_rate <= 0:
            raise ValueError("שער ההמרה חייב להיות גדול מאפס")

        try:
            start_id = int(self.start_id_var.get())
        except ValueError:
            raise ValueError("מספר הפריט ההתחלתי חייב להיות מספר שלם") from None
        if start_id <= 0:
            raise ValueError("מספר הפריט ההתחלתי חייב להיות גדול מאפס")

        return exchange_rate, start_id

    # ---------------------------------------------------------------- convert tab
    def _build_convert_tab(self) -> None:
        frame = self.convert_tab

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=10, pady=10)

        self.file_label_var = tk.StringVar(value=rtl("לא נבחר קובץ"))
        ttk.Button(top, text=rtl("בחר קובץ מהיצרן..."), command=self._on_pick_file).pack(
            side="right"
        )
        ttk.Label(top, textvariable=self.file_label_var, justify="right").pack(
            side="right", padx=10
        )

        self.run_button = ttk.Button(
            top, text=rtl("הרץ המרה"), command=self._on_run_conversion, state="disabled"
        )
        self.run_button.pack(side="right", padx=10)

        self.summary_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.summary_var, justify="right", foreground="#333").pack(
            fill="x", padx=10
        )

        self.warning_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.warning_var, justify="right", foreground="#b30000").pack(
            fill="x", padx=10
        )

        columns = ("item_number", "price", "size", "color", "description", "item_code")
        headers = {
            "item_number": "מס' פריט",
            "price": "מחיר",
            "size": "מידה",
            "color": "צבע",
            "description": "תיאור",
            "item_code": 'מק"ט יצרן',
        }
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=rtl(headers[col]))
            self.tree.column(col, width=120, anchor="e")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.export_button = ttk.Button(
            frame, text=rtl("שמור קובץ לרווחית..."), command=self._on_export, state="disabled"
        )
        self.export_button.pack(padx=10, pady=(0, 10), anchor="e")

    def _on_pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title=rtl("בחר את קובץ ההזמנה מהיצרן"),
            filetypes=[("Excel files", "*.xlsx *.xls"), (rtl("כל הקבצים"), "*.*")],
        )
        if not path:
            return
        self.selected_file = Path(path)
        self.file_label_var.set(self.selected_file.name)
        self.run_button.configure(state="normal")

    def _on_run_conversion(self) -> None:
        if self.selected_file is None:
            return
        try:
            exchange_rate, start_id = self._read_settings_from_ui()
        except ValueError as exc:
            messagebox.showerror(rtl("קלט לא תקין"), rtl(str(exc)))
            return

        try:
            result = run_conversion(
                self.selected_file, exchange_rate=exchange_rate, start_item_number=start_id
            )
        except Exception as exc:  # noqa: BLE001 - surface any parsing failure to the user
            messagebox.showerror(rtl("שגיאה בקריאת הקובץ"), rtl(f"לא הצלחתי לקרוא את הקובץ:\n{exc}"))
            return

        self.last_result = result
        self._populate_preview(result)
        self.export_button.configure(state="normal" if result.rivhit_rows else "disabled")

    def _populate_preview(self, result: ConversionResult) -> None:
        self.tree.delete(*self.tree.get_children())
        for row in result.rivhit_rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row.rivhit_item_number,
                    "" if row.price is None else f"{row.price:,.0f}",
                    row.size,
                    row.color_description,
                    row.description,
                    row.manufacturer_item_code,
                ),
            )

        summary = (
            f'נמצאו {len(result.all_products)} שורות בקובץ היצרן, מתוכן {len(result.new_products)} '
            f'חדשות / מידה חדשה שיוכנסו לרווחית (מספרים {result.rivhit_rows[0].rivhit_item_number}'
            f"-{result.rivhit_rows[-1].rivhit_item_number})"
            if result.rivhit_rows
            else f"נמצאו {len(result.all_products)} שורות בקובץ היצרן, ואף לא אחת מסומנת כחדשה/מידה חדשה"
        )
        self.summary_var.set(rtl(summary))

        if result.missing_retail_price:
            warning = (
                f"שים לב: {len(result.missing_retail_price)} פריטים חדשים בלי מחיר קמעונאי בקובץ "
                "המקור - המחיר שלהם יישאר ריק, כדאי לבדוק ידנית"
            )
            self.warning_var.set(rtl(warning))
        else:
            self.warning_var.set("")

    def _on_export(self) -> None:
        if self.last_result is None or not self.last_result.rivhit_rows:
            return
        path = filedialog.asksaveasfilename(
            title=rtl("שמור קובץ עבור רווחית"),
            defaultextension=".txt",
            filetypes=[("Text (Tab delimited)", "*.txt")],
        )
        if not path:
            return
        try:
            export_to_rivhit_file(self.last_result, path)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(rtl("שגיאה בשמירה"), rtl(f"לא הצלחתי לשמור את הקובץ:\n{exc}"))
            return

        next_id = self.last_result.next_item_number
        self.start_id_var.set(str(next_id))
        self.settings = Settings(
            exchange_rate=float(self.exchange_rate_var.get()), next_item_number=next_id
        )
        save_settings(self.settings)

        # Logged even without a "History" tab to show it - keeps the record
        # (exchange rate + Rivhit item number, per conversion) available in
        # case a UI for it comes back later.
        append_log_entry(
            ConversionLogEntry(
                timestamp=datetime.now(),
                source_file=self.selected_file.name if self.selected_file else "",
                exchange_rate=self.settings.exchange_rate,
                start_item_number=self.last_result.rivhit_rows[0].rivhit_item_number,
                item_count=len(self.last_result.rivhit_rows),
            )
        )

        messagebox.showinfo(
            rtl("הצלחה"),
            rtl(
                f"הקובץ נשמר בהצלחה:\n{path}\n\n"
                f"מספר הפריט הבא בתור עבור ההמרה הבאה עודכן אוטומטית ל-{next_id}."
            ),
        )


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
