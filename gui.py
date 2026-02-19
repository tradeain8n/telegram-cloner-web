import tkinter.messagebox as messagebox
from tkcalendar import DateEntry
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class AuthDialog(ctk.CTkToplevel):
    def __init__(self, parent, auth_type="phone"):
        super().__init__(parent)
        self.result = None
        self.title("Требуется авторизация")
        self.geometry("420x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        prompt_text = {
            "phone": "Введите номер телефона:",
            "code": "Введите код подтверждения:",
            "password": "Введите пароль 2FA:",
        }

        self.label = ctk.CTkLabel(self, text=prompt_text.get(auth_type, "Введите данные:"))
        self.label.pack(padx=20, pady=20)

        self.entry = ctk.CTkEntry(self, width=300)
        self.entry.pack(padx=20, pady=5)

        if auth_type == "password":
            self.entry.configure(show="*")

        self.ok_button = ctk.CTkButton(self, text="OK", command=self._on_ok)
        self.ok_button.pack(padx=20, pady=10)

        self.entry.focus()
        self.entry.bind("<Return>", lambda _: self._on_ok())
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _on_ok(self):
        self.result = self.entry.get()
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Telegram Cloner App")
        self.geometry("820x700")
        self.resizable(False, False)

        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.pack(padx=20, pady=20, fill="x")
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.api_id_label = ctk.CTkLabel(self.settings_frame, text="API ID:")
        self.api_id_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.api_id_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="1234567")
        self.api_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.api_hash_label = ctk.CTkLabel(self.settings_frame, text="API Hash:")
        self.api_hash_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.api_hash_entry = ctk.CTkEntry(
            self.settings_frame, placeholder_text="Ваш секретный ключ", show="*"
        )
        self.api_hash_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.source_ids_label = ctk.CTkLabel(
            self.settings_frame, text="ID Каналов-Источников (через запятую):"
        )
        self.source_ids_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.source_ids_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="-100111,-100222")
        self.source_ids_entry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        self.target_id_label = ctk.CTkLabel(self.settings_frame, text="ID Вашего Канала:")
        self.target_id_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.target_id_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="-100333")
        self.target_id_entry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

        self.date_frame = ctk.CTkFrame(self)
        self.date_frame.pack(padx=20, pady=(0, 10), fill="x")

        self.date_checkbox = ctk.CTkCheckBox(
            self.date_frame,
            text="Копировать с определенной даты",
            command=self._toggle_date_entry,
        )
        self.date_checkbox.pack(side="left", padx=5, pady=10)

        self.date_entry = DateEntry(
            self.date_frame,
            selectmode="day",
            date_pattern="dd.mm.yyyy",
            background="gray",
            foreground="white",
            bordercolor="gray",
        )
        self.date_entry.pack(side="left", padx=5, pady=10)
        self.date_entry.configure(state="disabled")

        self.save_creds_var = ctk.BooleanVar()
        self.save_creds_check = ctk.CTkCheckBox(
            self,
            text="Сохранить данные (API ID/Hash шифруются)",
            variable=self.save_creds_var,
        )
        self.save_creds_check.pack(padx=20, pady=(0, 10), anchor="w")

        self.buttons_frame = ctk.CTkFrame(self)
        self.buttons_frame.pack(padx=20, pady=5, fill="x")

        self.stop_migration_button = ctk.CTkButton(
            self.buttons_frame,
            text="Остановить миграцию",
            fg_color="red",
            hover_color="#ff4d4d",
            command=lambda: None,
            state="disabled",
        )
        self.stop_migration_button.pack(side="left", padx=5, fill="x", expand=True)

        self.start_migration_button = ctk.CTkButton(
            self.buttons_frame,
            text="Начать миграцию архива",
            fg_color="green",
            hover_color="#2d8f2d",
            height=40,
        )
        self.start_migration_button.pack(side="left", padx=5, fill="x", expand=True)

        self.log_textbox = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self.log_textbox.pack(padx=20, pady=20, fill="both", expand=True)

    def _toggle_date_entry(self):
        if self.date_checkbox.get() == 1:
            self.date_entry.configure(state="normal")
        else:
            self.date_entry.configure(state="disabled")

    def show_auth_dialog(self, auth_type):
        dialog = AuthDialog(self, auth_type)
        self.wait_window(dialog)
        return dialog.result

    def append_log(self, message: str):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"{message}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def toggle_action_buttons(self, is_running: bool):
        if is_running:
            self.start_migration_button.configure(state="disabled")
            self.stop_migration_button.configure(command=lambda: None)
            self.stop_migration_button.configure(state="normal")
        else:
            self.start_migration_button.configure(state="normal")
            self.stop_migration_button.configure(state="disabled")

    def show_error(self, title, message):
        messagebox.showerror(title, message)