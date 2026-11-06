"""OnlyFans Authentication Section

OF-specific authentication widget with:
- Session cookie (sess)
- Auth ID
- Auth UID (2FA only)
- User Agent
- X-BC token
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox


class OnlyFansAuthSection(ctk.CTkFrame):
    """OnlyFans authentication credentials widget"""

    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config

        # Title
        title = ctk.CTkLabel(
            self,
            text="OnlyFans Authentication",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=(10, 5))

        # Help button
        help_frame = ctk.CTkFrame(self)
        help_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            help_frame,
            text="How to get OF credentials?",
            command=self.show_credential_guide,
            width=200,
            fg_color="orange",
            hover_color="darkorange"
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            help_frame,
            text="Test Connection",
            command=self.test_connection,
            width=150
        ).pack(side="left", padx=5)

        # Session cookie
        ctk.CTkButton(
            self, text="Import from OnlyGoblins Cookie Helper",
            command=self.show_cookie_helper_import, fg_color="#663d91",
            hover_color="#8050af"
        ).pack(fill="x", padx=15, pady=5)

        self.create_field("Session Cookie (sess):", "sess")

        # Auth ID
        self.create_field("Auth ID:", "auth_id")

        # Auth UID (optional)
        self.create_field("Auth UID (2FA only, optional):", "auth_uid")

        # User Agent
        self.create_field("User Agent:", "user_agent")

        # X-BC Token
        self.create_field("X-BC Token:", "x_bc")

        # Load values from config
        self.load_from_config()

    def create_field(self, label_text: str, field_name: str):
        """Create labeled entry field"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=10, pady=5)

        label = ctk.CTkLabel(
            frame,
            text=label_text,
            width=250,
            anchor="w"
        )
        label.pack(side="left", padx=5)

        # Store reference as attribute
        entry = ctk.CTkEntry(
            frame,
            width=400,
            show="*" if "cookie" in label_text.lower() or "token" in label_text.lower() else None
        )
        entry.pack(side="left", fill="x", expand=True, padx=5)

        # Bind to save on change
        entry.bind("<FocusOut>", lambda e: self.save_to_config())
        entry.bind("<Return>", lambda e: self.save_to_config())

        setattr(self, f"{field_name}_entry", entry)

    def load_from_config(self):
        """Load values from config"""
        if hasattr(self, 'sess_entry'):
            self.sess_entry.delete(0, tk.END)
            if self.config.sess:
                self.sess_entry.insert(0, self.config.sess)

        if hasattr(self, 'auth_id_entry'):
            self.auth_id_entry.delete(0, tk.END)
            if self.config.auth_id:
                self.auth_id_entry.insert(0, self.config.auth_id)

        if hasattr(self, 'auth_uid_entry'):
            self.auth_uid_entry.delete(0, tk.END)
            if self.config.auth_uid:
                self.auth_uid_entry.insert(0, self.config.auth_uid)

        if hasattr(self, 'user_agent_entry'):
            self.user_agent_entry.delete(0, tk.END)
            if self.config.user_agent:
                self.user_agent_entry.insert(0, self.config.user_agent)

        if hasattr(self, 'x_bc_entry'):
            self.x_bc_entry.delete(0, tk.END)
            if self.config.x_bc:
                self.x_bc_entry.insert(0, self.config.x_bc)

    def save_to_config(self, *, settings_changed=False):
        """Save values to config"""
        for name in ("sess", "auth_id", "auth_uid", "user_agent", "x_bc"):
            value = getattr(self, f"{name}_entry").get().strip() or None
            if value != (getattr(self.config, name) or None):
                settings_changed = True
                setattr(self.config, name, value)
                self.config._api = None  # Reconnect with the edited credentials.

        if settings_changed:
            self.config._save_config()

    def test_connection(self):
        """Test OF authentication"""
        # Save first
        self.save_to_config()

        if not self.config.has_credentials():
            messagebox.showerror(
                "Missing Credentials",
                "Please fill in all required fields (sess, auth_id, user_agent, x_bc)"
            )
            return

        try:
            from api.onlyfans_api import OnlyFansApi

            api = OnlyFansApi(
                sess=self.config.sess,
                auth_id=self.config.auth_id,
                auth_uid=self.config.auth_uid,
                user_agent=self.config.user_agent,
                x_bc=self.config.x_bc
            )

            # Test auth
            if api.test_auth():
                messagebox.showinfo("Success", "OnlyFans authentication successful!")
            else:
                messagebox.showerror("Error", "Authentication failed")

        except Exception as error:
            status = getattr(getattr(error, "response", None), "status_code", None)
            detail = f" (HTTP {status})" if isinstance(status, int) and 400 <= status <= 599 else ""
            messagebox.showerror("Error", f"Authentication failed{detail}. Check your session and network, then try again.")

    def show_cookie_helper_import(self):
        from gui.widgets.cookie_helper_import import CookieHelperImportDialog
        CookieHelperImportDialog(self)

    def confirm_cookie_helper_import(self, values, parent=None):
        """Do not populate autosaving entries until the user explicitly confirms."""
        from utils.cookie_helper import FIELDS
        from utils.privacy import register_secrets
        if not messagebox.askyesno(
            "Save imported credentials?",
            "The export contains all required fields.\n\n"
            "Replace the current OnlyFans authentication fields and save them locally?\n"
            "An absent Auth UID will clear the previous account's UID.\n"
            "You can then use Test Connection.", parent=parent or self
        ):
            return False
        previous = {name: getattr(self, f"{name}_entry").get() for name in FIELDS}
        previous_config = {name: getattr(self.config, name) for name in FIELDS}
        register_secrets(values["sess"], values["auth_id"], values["auth_uid"], values["x_bc"])
        for name in FIELDS:
            entry = getattr(self, f"{name}_entry")
            entry.delete(0, tk.END)
            entry.insert(0, values[name])
        try:
            self.save_to_config()
        except OSError:
            for name in FIELDS:
                setattr(self.config, name, previous_config[name])
                entry = getattr(self, f"{name}_entry")
                entry.delete(0, tk.END)
                entry.insert(0, previous[name])
            messagebox.showerror("Save failed", "Could not save credentials. Check file permissions.", parent=parent or self)
            return False
        return True

    def show_credential_guide(self):
        """Show credential extraction guide"""
        from gui.widgets.credential_help import show_of_credential_guide
        show_of_credential_guide(self)
