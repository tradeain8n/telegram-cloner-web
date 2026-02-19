import asyncio
import datetime
import json
import logging
import os
import queue
import threading
import tkinter.messagebox as messagebox
from cryptography.fernet import Fernet

from gui import App
from telegram_logic import TelegramLogic

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)


class AppController:
    KEY_FILE = "app.key"
    CREDS_FILE = "credentials.json"

    def __init__(self, app_instance: App):
        self.app = app_instance
        self.log_queue = queue.Queue()
        self.logic = None
        self.thread = None
        self.logger = logging.getLogger("TelegramCloner")

        self._load_credentials()
        self.app.start_migration_button.configure(command=self.start_migration)
        self.app.stop_migration_button.configure(command=self.stop_migration)
        self.app.after(100, self.process_log_queue)

    def _load_key(self):
        if os.path.exists(self.KEY_FILE):
            with open(self.KEY_FILE, "rb") as f:
                return f.read()
        key = Fernet.generate_key()
        with open(self.KEY_FILE, "wb") as f:
            f.write(key)
        return key

    def _encrypt(self, data: str) -> str:
        return Fernet(self._load_key()).encrypt(data.encode()).decode()

    def _decrypt(self, data: str) -> str:
        return Fernet(self._load_key()).decrypt(data.encode()).decode()

    def _save_credentials(self):
        if self.app.save_creds_var.get():
            creds = {
                "api_id": self._encrypt(self.app.api_id_entry.get()),
                "api_hash": self._encrypt(self.app.api_hash_entry.get()),
                "source_ids": self.app.source_ids_entry.get(),
                "target_id": self.app.target_id_entry.get(),
            }
            with open(self.CREDS_FILE, "w", encoding="utf-8") as f:
                json.dump(creds, f)
        elif os.path.exists(self.CREDS_FILE):
            os.remove(self.CREDS_FILE)

    def _load_credentials(self):
        if os.path.exists(self.CREDS_FILE):
            try:
                with open(self.CREDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.app.api_id_entry.delete(0, "end")
                self.app.api_id_entry.insert(0, self._decrypt(data["api_id"]))
                self.app.api_hash_entry.delete(0, "end")
                self.app.api_hash_entry.insert(0, self._decrypt(data["api_hash"]))
                self.app.source_ids_entry.delete(0, "end")
                self.app.source_ids_entry.insert(0, data.get("source_ids", ""))
                self.app.target_id_entry.delete(0, "end")
                self.app.target_id_entry.insert(0, data.get("target_id", ""))
                self.app.save_creds_var.set(True)
            except Exception as exc:
                self.logger.error("Ошибка загрузки credentials: %s", exc)
                self._log(f"Ошибка загрузки сохранённых данных: {exc}", level="error")

    def _log(self, message, level="info"):
        self.log_queue.put(message)
        getattr(self.logger, level)(message)

    def process_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.app.append_log(message)
        except queue.Empty:
            pass
        finally:
            self.app.after(100, self.process_log_queue)

    def _threadsafe_auth_dialog(self, auth_type):
        result_holder = {"value": None}
        event = threading.Event()

        def show():
            try:
                result_holder["value"] = self.app.show_auth_dialog(auth_type)
            finally:
                event.set()

        self.app.after(0, show)
        event.wait()
        return result_holder["value"]

    def start_migration(self):
        if self.thread and self.thread.is_alive():
            self._log("Миграция уже выполняется.", level="warning")
            return

        if not self.app.api_id_entry.get().strip() or not self.app.api_hash_entry.get().strip():
            messagebox.showwarning("Недостаточно данных", "Заполните API ID и API Hash.")
            return

        source_input = self.app.source_ids_entry.get().strip()
        if not source_input:
            messagebox.showwarning("Недостаточно данных", "Укажите хотя бы один канал-источник.")
            return

        try:
            source_ids = [
                int(item.strip()) for item in source_input.split(",") if item.strip()
            ]
        except ValueError:
            messagebox.showerror("Ошибка", "ID источников должны быть числами.")
            return

        target_text = self.app.target_id_entry.get().strip()
        if not target_text:
            messagebox.showwarning("Недостаточно данных", "Укажите ID канала получателя.")
            return

        try:
            target_id = int(target_text)
        except ValueError:
            messagebox.showerror("Ошибка", "ID целевого канала должен быть числом.")
            return

        start_date = None
        if self.app.date_checkbox.get() == 1:
            selected_date = self.app.date_entry.get_date()
            start_date = datetime.datetime.combine(selected_date, datetime.time.min)

        self._save_credentials()

        self.logic = TelegramLogic(
            api_id=self.app.api_id_entry.get(),
            api_hash=self.app.api_hash_entry.get(),
            log_callback=self.log_queue.put,
            auth_callback=self._threadsafe_auth_dialog,
            start_date=start_date,
        )
        self.app.toggle_action_buttons(True)
        self._log("Запуск миграции...")
        self.thread = threading.Thread(
            target=self._run_logic,
            args=(source_ids, target_id),
            daemon=True,
        )
        self.thread.start()

    def _run_logic(self, source_ids, target_id):
        try:
            self.logic.start_migration(source_ids, target_id)
        except Exception as exc:
            self._log(f"Критическая ошибка: {exc}", level="error")
            self.app.after(0, lambda: self.app.show_error("Ошибка запуска миграции", str(exc)))
        finally:
            self.app.after(0, lambda: self.app.toggle_action_buttons(False))

    def stop_migration(self):
        if self.logic and self.logic.is_running:
            self._log("Остановка миграции по запросу.")
            self.logic.stop()
        else:
            self._log("Миграция не была запущена.", level="warning")


if __name__ == "__main__":
    app_gui = App()
    AppController(app_gui)
    app_gui.mainloop()