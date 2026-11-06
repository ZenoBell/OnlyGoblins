"""Explicit local paste/file import with confirmation before touching saved fields."""

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from utils.cookie_helper import CookieHelperError, MAX_EXPORT_BYTES, parse_cookie_helper_export


class CookieHelperImportDialog(ctk.CTkToplevel):
    def __init__(self, auth_section):
        super().__init__(auth_section)
        self.auth_section = auth_section
        self.title("Import from OnlyGoblins Cookie Helper")
        self.geometry("680x440")
        self.transient(auth_section.winfo_toplevel())
        ctk.CTkLabel(self, text="Paste your exported JSON or choose a JSON file.\n"
                    "Session credentials are sensitive. Import stays on this computer.").pack(pady=12)
        self.text = ctk.CTkTextbox(self, wrap="word")
        self.text.pack(fill="both", expand=True, padx=15)
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=15, pady=12)
        ctk.CTkButton(row, text="Choose JSON file", command=self.choose_file).pack(side="left", padx=5)
        ctk.CTkButton(row, text="Validate and import", command=self.import_json).pack(side="left", padx=5)
        ctk.CTkButton(row, text="Cancel", command=self.close).pack(side="right", padx=5)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(100, self.grab_set)

    def choose_file(self):
        filename = filedialog.askopenfilename(parent=self, title="Choose Cookie Helper export",
                                              filetypes=[("JSON export", "*.json")])
        if not filename:
            return
        try:
            with Path(filename).open("rb") as handle:
                raw = handle.read(MAX_EXPORT_BYTES + 1)
            if len(raw) > MAX_EXPORT_BYTES:
                raise ValueError
            raw = raw.decode("utf-8-sig")
        except (OSError, ValueError, UnicodeError):
            messagebox.showerror("Cannot read export", "Choose a UTF-8 JSON file smaller than 64 KiB.", parent=self)
            return
        self.text.delete("1.0", "end")
        self.text.insert("1.0", raw)

    def import_json(self):
        try:
            values = parse_cookie_helper_export(self.text.get("1.0", "end"))
        except CookieHelperError as error:
            messagebox.showerror("Invalid export", str(error), parent=self)
            return
        if self.auth_section.confirm_cookie_helper_import(values, parent=self):
            self.close()

    def close(self):
        self.text.delete("1.0", "end")
        self.destroy()
