from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from tkinter import BOTH, DISABLED, END, LEFT, NORMAL, RIGHT, TOP, Button, Frame, Label, StringVar, Tk
from tkinter.scrolledtext import ScrolledText

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

from app.database.db import fetch_one  # noqa: E402
from app.exchange.exchange_client import CoincheckClient  # noqa: E402
from config import settings  # noqa: E402
from main import run_once  # noqa: E402


def _mask(value: str) -> str:
    if not value:
        return "未設定"
    if len(value) <= 8:
        return "********"
    return f"{value[:4]}...{value[-4:]}"


class CryptoBotGui:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("一攫千金くん 操作パネル")
        self.root.geometry("900x620")
        self.root.minsize(760, 520)

        self.messages: queue.Queue[str] = queue.Queue()
        self.action_buttons: list[Button] = []
        self.loop_thread: threading.Thread | None = None
        self.stop_loop = threading.Event()

        self.status_var = StringVar()
        self.config_var = StringVar()

        self._build()
        self._refresh_config()
        self._poll_messages()

    def _build(self) -> None:
        header = Frame(self.root, padx=14, pady=10)
        header.pack(side=TOP, fill="x")

        title = Label(header, text="一攫千金くん 操作パネル", font=("Yu Gothic UI", 16, "bold"))
        title.pack(anchor="w")

        self.status_label = Label(header, textvariable=self.status_var, font=("Yu Gothic UI", 10, "bold"))
        self.status_label.pack(anchor="w", pady=(6, 0))

        config = Label(header, textvariable=self.config_var, justify=LEFT, font=("Yu Gothic UI", 9))
        config.pack(anchor="w", pady=(6, 0))

        body = Frame(self.root, padx=14, pady=8)
        body.pack(side=TOP, fill=BOTH, expand=True)

        toolbar = Frame(body)
        toolbar.pack(side=TOP, fill="x", pady=(0, 10))

        self._add_button(toolbar, "設定確認", self._refresh_config)
        self._add_button(toolbar, "DB接続確認", lambda: self._run_action("DB接続確認", self._check_db))
        self._add_button(toolbar, "Coincheck価格取得", lambda: self._run_action("Coincheck価格取得", self._get_ticker))
        self._add_button(toolbar, "Coincheck残高取得", lambda: self._run_action("Coincheck残高取得", self._get_balance))
        self._add_button(toolbar, "APIテスト実行", lambda: self._run_action("APIテスト実行", self._run_pytest))
        self._add_button(toolbar, "1回だけ実行", lambda: self._run_action("1回だけ実行", run_once))

        loopbar = Frame(body)
        loopbar.pack(side=TOP, fill="x", pady=(0, 10))

        self.start_button = Button(loopbar, text="定期実行開始", command=self._start_loop, width=18)
        self.start_button.pack(side=LEFT, padx=(0, 8))
        self.stop_button = Button(loopbar, text="定期実行停止", command=self._stop_loop, width=18, state=DISABLED)
        self.stop_button.pack(side=LEFT, padx=(0, 8))

        clear_button = Button(loopbar, text="ログ消去", command=self._clear_log, width=14)
        clear_button.pack(side=RIGHT)

        self.log = ScrolledText(body, wrap="word", font=("Consolas", 10))
        self.log.pack(side=TOP, fill=BOTH, expand=True)
        self.log.configure(state=DISABLED)

    def _add_button(self, parent: Frame, text: str, command) -> None:
        button = Button(parent, text=text, command=command, width=18)
        button.pack(side=LEFT, padx=(0, 8), pady=2)
        self.action_buttons.append(button)

    def _refresh_config(self) -> None:
        env_path = BASE_DIR / ".env"
        trading_text = "ON: 実注文許可" if settings.trading_enabled else "OFF: 実注文しない"
        self.status_var.set(f"TRADING_ENABLED = {trading_text}")
        self.status_label.configure(fg="#b00020" if settings.trading_enabled else "#1b7f3a")
        self.config_var.set(
            "\n".join(
                [
                    f".env: {'あり' if env_path.exists() else 'なし'}",
                    f"取引所: {settings.exchange_name}",
                    f"銘柄: {settings.symbol}",
                    f"注文金額: {settings.order_amount_jpy} JPY",
                    f"Coincheck Access Key: {_mask(settings.coincheck_access_key)}",
                    f"Coincheck Secret Key: {_mask(settings.coincheck_secret_key)}",
                ]
            )
        )
        self._write("設定を確認しました。")

    def _set_action_buttons(self, state: str) -> None:
        for button in self.action_buttons:
            button.configure(state=state)

    def _run_action(self, title: str, func) -> None:
        self._set_action_buttons(DISABLED)
        self._write(f"[開始] {title}")

        def worker() -> None:
            try:
                result = func()
                if result is not None:
                    self.messages.put(self._format_result(result))
                self.messages.put(f"[完了] {title}")
            except Exception as exc:
                self.messages.put(f"[失敗] {title}: {exc}")
            finally:
                self.messages.put("__ENABLE_ACTIONS__")

        threading.Thread(target=worker, daemon=True).start()

    def _check_db(self) -> str:
        row = fetch_one("SELECT @@SERVERNAME, DB_NAME(), GETDATE()")
        if row is None:
            return "DBから結果が返りませんでした。"
        return f"DB接続成功\nサーバー名: {row[0]}\nDB名: {row[1]}\n現在時刻: {row[2]}"

    def _get_ticker(self) -> dict:
        client = CoincheckClient()
        return client.get_ticker(pair=settings.symbol.lower())

    def _get_balance(self) -> dict:
        client = CoincheckClient()
        return client.get_balance()

    def _run_pytest(self) -> str:
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_exchange_client.py"],
            cwd=BASE_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        output = "\n".join(part for part in [completed.stdout, completed.stderr] if part.strip())
        return f"終了コード: {completed.returncode}\n{output}"

    def _start_loop(self) -> None:
        if self.loop_thread and self.loop_thread.is_alive():
            self._write("定期実行はすでに動作中です。")
            return

        self.stop_loop.clear()
        self.start_button.configure(state=DISABLED)
        self.stop_button.configure(state=NORMAL)
        self._write(f"定期実行を開始しました。間隔: {settings.main_loop_interval_seconds}秒")

        def loop_worker() -> None:
            while not self.stop_loop.is_set():
                try:
                    run_once()
                    self.messages.put("定期実行: 1回分が完了しました。")
                except Exception as exc:
                    self.messages.put(f"定期実行エラー: {exc}")
                self.stop_loop.wait(settings.main_loop_interval_seconds)
            self.messages.put("定期実行を停止しました。")
            self.messages.put("__LOOP_STOPPED__")

        self.loop_thread = threading.Thread(target=loop_worker, daemon=True)
        self.loop_thread.start()

    def _stop_loop(self) -> None:
        self.stop_loop.set()
        self.stop_button.configure(state=DISABLED)

    def _poll_messages(self) -> None:
        while True:
            try:
                message = self.messages.get_nowait()
            except queue.Empty:
                break

            if message == "__ENABLE_ACTIONS__":
                self._set_action_buttons(NORMAL)
            elif message == "__LOOP_STOPPED__":
                self.start_button.configure(state=NORMAL)
                self.stop_button.configure(state=DISABLED)
            else:
                self._write(message)

        self.root.after(100, self._poll_messages)

    def _format_result(self, result) -> str:
        if isinstance(result, (dict, list)):
            return json.dumps(result, ensure_ascii=False, indent=2)
        return str(result)

    def _write(self, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log.configure(state=NORMAL)
        self.log.insert(END, f"{timestamp}  {message}\n\n")
        self.log.see(END)
        self.log.configure(state=DISABLED)

    def _clear_log(self) -> None:
        self.log.configure(state=NORMAL)
        self.log.delete("1.0", END)
        self.log.configure(state=DISABLED)


def main() -> None:
    root = Tk()
    CryptoBotGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
