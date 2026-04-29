"""
可视化界面 - 超星学习通智能刷课助手
暗色主题 | 账号登录 | 课程自动检测 | 实时日志
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import sys
import os
import time
import json

sys.path.insert(0, os.path.dirname(__file__))
from config import CONFIG


# ============================================================
# 暗色主题配色
# ============================================================
COLORS = {
    "bg": "#1a1b2e",
    "card": "#232440",
    "card_hover": "#2a2b4a",
    "accent": "#6c5ce7",
    "accent_hover": "#7d6ff0",
    "success": "#00b894",
    "warning": "#fdcb6e",
    "error": "#e17055",
    "text": "#dfe6e9",
    "text_dim": "#a0a4b8",
    "input_bg": "#2d2e50",
    "input_border": "#3d3e60",
    "log_bg": "#12132a",
}


class GUILogHandler:
    """将日志重定向到 GUI 文本框"""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, msg):
        if msg.strip():
            self.text_widget.after(0, self._append, msg)

    def _append(self, msg):
        self.text_widget.config(state="normal")
        self.text_widget.insert(tk.END, msg + "\n")
        self.text_widget.see(tk.END)
        self.text_widget.config(state="disabled")

    def flush(self):
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("XueXiTong Auto Helper")
        self.geometry("960x720")
        self.minsize(860, 640)
        self.configure(bg=COLORS["bg"])
        self.running = False
        self.browser_mgr = None
        self.page = None
        self.detected_courses = []
        self.course_vars = []
        self.chapters_done = 0
        self.chapters_total = 0

        self._build_ui()
        self._load_saved_config()
        self._load_env_api_key()

    # ============================================================
    # UI 构建
    # ============================================================
    def _build_ui(self):
        # 标题栏 - 渐变效果模拟
        header = tk.Frame(self, bg="#5b4cdb", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        title_frame = tk.Frame(header, bg="#5b4cdb")
        title_frame.pack(side="left", padx=20, pady=8)
        tk.Label(title_frame, text="XueXiTong Auto Helper",
                 font=("Segoe UI", 15, "bold"),
                 bg="#5b4cdb", fg="white").pack(anchor="w")
        tk.Label(title_frame, text="DrissionPage Stealth  |  DeepSeek AI  |  Zero Risk",
                 font=("Segoe UI", 8),
                 bg="#5b4cdb", fg="#c8bfff").pack(anchor="w")

        # 安全指示灯
        status_frame = tk.Frame(header, bg="#5b4cdb")
        status_frame.pack(side="right", padx=20)
        self.safety_dot = tk.Label(status_frame, text="  SAFE  ",
                                    font=("Consolas", 8, "bold"),
                                    bg=COLORS["success"], fg="white")
        self.safety_dot.pack(side="right", pady=2)

        # 主体区域（左右分栏）
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=15, pady=10)

        left = tk.Frame(body, bg=COLORS["bg"], width=420)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        right = tk.Frame(body, bg=COLORS["bg"], width=420)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # === 左栏 ===
        self._build_login_card(left)
        self._build_course_card(left)

        # === 右栏 ===
        self._build_config_card(right)
        self._build_log_card(right)

        # 底部
        self._build_progress_bar()
        self._build_footer()

    def _card(self, parent, title):
        frame = tk.LabelFrame(parent, text=f"  {title}  ",
                              font=("Microsoft YaHei UI", 10, "bold"),
                              bg=COLORS["card"], fg=COLORS["text"],
                              bd=1, relief="solid",
                              highlightbackground=COLORS["input_border"],
                              highlightthickness=1)
        frame.pack(fill="x", pady=(0, 10))
        return frame

    def _entry(self, parent, label, show=None, row=0):
        tk.Label(parent, text=label, font=("Microsoft YaHei UI", 9),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).grid(
            row=row, column=0, sticky="w", padx=10, pady=4)
        entry = tk.Entry(parent, font=("Consolas", 10),
                         bg=COLORS["input_bg"], fg=COLORS["text"],
                         insertbackground=COLORS["text"],
                         bd=0, relief="flat", show=show)
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=4, ipady=4)
        parent.columnconfigure(1, weight=1)
        return entry

    def _build_login_card(self, parent):
        card = self._card(parent, "🔑 账号登录")
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="x", padx=5, pady=8)

        self.phone_entry = self._entry(inner, "手 机 号", row=0)
        self.pwd_entry = self._entry(inner, "密　　码", show="●", row=1)

        btn_frame = tk.Frame(card, bg=COLORS["card"])
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.login_btn = tk.Button(
            btn_frame, text="🔍 登录并检测课程",
            font=("Microsoft YaHei UI", 10, "bold"),
            bg=COLORS["accent"], fg="white", activebackground=COLORS["accent_hover"],
            bd=0, relief="flat", cursor="hand2", pady=6,
            command=self._on_login_detect)
        self.login_btn.pack(fill="x")

        self.login_status = tk.Label(card, text="",
                                     font=("Microsoft YaHei UI", 9),
                                     bg=COLORS["card"], fg=COLORS["text_dim"])
        self.login_status.pack(pady=(0, 5))

    def _build_course_card(self, parent):
        card = self._card(parent, "📚 课程选择 (登录后自动检测)")
        self.course_frame = tk.Frame(card, bg=COLORS["card"])
        self.course_frame.pack(fill="both", expand=True, padx=10, pady=8)

        self.course_placeholder = tk.Label(
            self.course_frame, text="请先登录，课程将自动检测显示在此处",
            font=("Microsoft YaHei UI", 9), bg=COLORS["card"],
            fg=COLORS["text_dim"])
        self.course_placeholder.pack(pady=20)

        # 全选按钮区域
        self.select_btns = tk.Frame(card, bg=COLORS["card"])
        self.select_btns.pack(fill="x", padx=10, pady=(0, 8))

    def _build_config_card(self, parent):
        card = self._card(parent, "⚙️ 运行配置")
        inner = tk.Frame(card, bg=COLORS["card"])
        inner.pack(fill="x", padx=5, pady=8)

        self.api_key_entry = self._entry(inner, "DeepSeek Key", show="●", row=0)

        # 调度设置
        tk.Label(inner, text="学习时段", font=("Microsoft YaHei UI", 9),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).grid(
            row=1, column=0, sticky="w", padx=10, pady=4)

        time_frame = tk.Frame(inner, bg=COLORS["card"])
        time_frame.grid(row=1, column=1, sticky="ew", padx=10, pady=4)

        self.start_hour = tk.Spinbox(time_frame, from_=0, to=23, width=3,
                                      font=("Consolas", 10),
                                      bg=COLORS["input_bg"], fg=COLORS["text"],
                                      buttonbackground=COLORS["card"])
        self.start_hour.pack(side="left")
        self.start_hour.delete(0, "end")
        self.start_hour.insert(0, "8")

        tk.Label(time_frame, text=" : 00  —  ", bg=COLORS["card"],
                 fg=COLORS["text_dim"], font=("Consolas", 10)).pack(side="left")

        self.end_hour = tk.Spinbox(time_frame, from_=0, to=23, width=3,
                                    font=("Consolas", 10),
                                    bg=COLORS["input_bg"], fg=COLORS["text"],
                                    buttonbackground=COLORS["card"])
        self.end_hour.pack(side="left")
        self.end_hour.delete(0, "end")
        self.end_hour.insert(0, "22")

        tk.Label(time_frame, text=" : 00", bg=COLORS["card"],
                 fg=COLORS["text_dim"], font=("Consolas", 10)).pack(side="left")

        # 每日上限
        tk.Label(inner, text="每日上限(h)", font=("Microsoft YaHei UI", 9),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).grid(
            row=2, column=0, sticky="w", padx=10, pady=4)

        self.max_hours = tk.Spinbox(inner, from_=1, to=16, width=5,
                                     font=("Consolas", 10),
                                     bg=COLORS["input_bg"], fg=COLORS["text"],
                                     buttonbackground=COLORS["card"])
        self.max_hours.grid(row=2, column=1, sticky="w", padx=10, pady=4)
        self.max_hours.delete(0, "end")
        self.max_hours.insert(0, "8")

    def _build_log_card(self, parent):
        card = self._card(parent, "LOG")
        self.log_text = scrolledtext.ScrolledText(
            card, font=("Consolas", 9), bg=COLORS["log_bg"],
            fg=COLORS["text"], insertbackground=COLORS["text"],
            bd=0, relief="flat", height=14, state="disabled",
            wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

        # 欢迎日志
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, "[READY] XueXiTong Auto Helper v1.0\n")
        self.log_text.insert(tk.END, "[SAFE]  Anti-detect: ON | Speed: 1.0x | Scheduler: ON\n")
        self.log_text.insert(tk.END, "---\n")
        self.log_text.config(state="disabled")

    def _build_progress_bar(self):
        prog_frame = tk.Frame(self, bg=COLORS["bg"])
        prog_frame.pack(fill="x", padx=15, pady=(0, 4))

        self.progress_label = tk.Label(prog_frame, text="Ready",
                                        font=("Consolas", 8),
                                        bg=COLORS["bg"], fg=COLORS["text_dim"])
        self.progress_label.pack(side="left")

        self.progress_pct = tk.Label(prog_frame, text="",
                                      font=("Consolas", 8, "bold"),
                                      bg=COLORS["bg"], fg=COLORS["accent"])
        self.progress_pct.pack(side="right")

        # 进度条
        style = ttk.Style()
        style.theme_use('default')
        style.configure("custom.Horizontal.TProgressbar",
                        troughcolor=COLORS["input_bg"],
                        background=COLORS["accent"],
                        thickness=6)
        self.progress_bar = ttk.Progressbar(self, style="custom.Horizontal.TProgressbar",
                                             maximum=100, value=0)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 8))

    def _build_footer(self):
        footer = tk.Frame(self, bg=COLORS["bg"])
        footer.pack(fill="x", padx=15, pady=(0, 12))

        self.start_btn = tk.Button(
            footer, text="START",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["success"], fg="white",
            activebackground="#00a885", bd=0, relief="flat",
            cursor="hand2", pady=8, command=self._on_start)
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.stop_btn = tk.Button(
            footer, text="STOP",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS["error"], fg="white",
            activebackground="#d35400", bd=0, relief="flat",
            cursor="hand2", pady=8, state="disabled",
            command=self._on_stop)
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

    # ============================================================
    # 事件处理
    # ============================================================
    def _log(self, msg):
        self.log_text.config(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def _on_login_detect(self):
        phone = self.phone_entry.get().strip()
        pwd = self.pwd_entry.get().strip()
        if not phone or not pwd:
            messagebox.showwarning("提示", "请填写手机号和密码")
            return

        self.login_btn.config(state="disabled", text="⏳ 登录中...")
        self.login_status.config(text="正在启动浏览器...", fg=COLORS["warning"])
        self._log("正在启动浏览器并登录...")

        threading.Thread(target=self._login_thread, args=(phone, pwd),
                         daemon=True).start()

    def _login_thread(self, phone, pwd):
        try:
            from core.browser import BrowserManager
            from core.login import perform_login
            from core.course import CourseManager

            # 启动浏览器
            self.browser_mgr = BrowserManager(CONFIG.get("browser", {}))
            self.page = self.browser_mgr.start()
            self.after(0, lambda: self._log("✅ 浏览器已启动"))
            self.after(0, lambda: self.login_status.config(
                text="正在登录...", fg=COLORS["warning"]))

            # 登录
            login_cfg = {"phone": phone, "password": pwd}
            ok = perform_login(self.page, login_cfg)
            if not ok:
                self.after(0, lambda: self._log("❌ 登录失败"))
                self.after(0, lambda: self.login_status.config(
                    text="❌ 登录失败，请检查账号密码", fg=COLORS["error"]))
                self.after(0, lambda: self.login_btn.config(
                    state="normal", text="🔍 登录并检测课程"))
                return

            self.after(0, lambda: self._log("✅ 登录成功！"))
            self.after(0, lambda: self.login_status.config(
                text="登录成功，正在检测课程...", fg=COLORS["success"]))

            # 保存账号密码到本地
            self.after(0, self._save_config)

            # 检测课程
            course_mgr = CourseManager(self.page, [])
            courses = course_mgr.fetch_courses()
            self.detected_courses = courses

            self.after(0, lambda: self._log(f"📚 检测到 {len(courses)} 门课程"))
            self.after(0, lambda: self._populate_courses(courses))
            self.after(0, lambda: self.login_status.config(
                text=f"✅ 已检测到 {len(courses)} 门课程", fg=COLORS["success"]))
            self.after(0, lambda: self.login_btn.config(
                state="normal", text="🔄 重新检测"))

        except Exception as e:
            self.after(0, lambda: self._log(f"❌ 错误: {e}"))
            self.after(0, lambda: self.login_status.config(
                text=f"❌ 错误: {str(e)[:40]}", fg=COLORS["error"]))
            self.after(0, lambda: self.login_btn.config(
                state="normal", text="🔍 登录并检测课程"))

    def _populate_courses(self, courses):
        # 清除旧内容
        for w in self.course_frame.winfo_children():
            w.destroy()
        for w in self.select_btns.winfo_children():
            w.destroy()

        self.course_vars = []

        if not courses:
            tk.Label(self.course_frame, text="未检测到课程",
                     font=("Microsoft YaHei UI", 9),
                     bg=COLORS["card"], fg=COLORS["text_dim"]).pack(pady=10)
            return

        # 添加滚动区域
        canvas = tk.Canvas(self.course_frame, bg=COLORS["card"],
                           highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(self.course_frame, orient="vertical",
                                  command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=COLORS["card"])

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 课程复选框
        for i, course in enumerate(courses):
            var = tk.BooleanVar(value=True)
            self.course_vars.append((var, course))

            cb = tk.Checkbutton(
                scroll_frame, text=course["name"],
                variable=var,
                font=("Microsoft YaHei UI", 9),
                bg=COLORS["card"], fg=COLORS["text"],
                selectcolor=COLORS["input_bg"],
                activebackground=COLORS["card"],
                activeforeground=COLORS["text"],
                anchor="w")
            cb.pack(fill="x", padx=5, pady=2)

        # 全选/取消按钮
        tk.Button(self.select_btns, text="全选",
                  font=("Microsoft YaHei UI", 8),
                  bg=COLORS["input_bg"], fg=COLORS["text"], bd=0,
                  command=lambda: [v.set(True) for v, _ in self.course_vars]
                  ).pack(side="left", padx=(0, 5))

        tk.Button(self.select_btns, text="取消全选",
                  font=("Microsoft YaHei UI", 8),
                  bg=COLORS["input_bg"], fg=COLORS["text"], bd=0,
                  command=lambda: [v.set(False) for v, _ in self.course_vars]
                  ).pack(side="left")

    def _on_start(self):
        if not self.page:
            messagebox.showwarning("提示", "请先登录并检测课程")
            return

        selected = [c for v, c in self.course_vars if v.get()]
        if not selected:
            messagebox.showwarning("提示", "请至少选择一门课程")
            return

        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._log(f"🚀 开始刷课，已选择 {len(selected)} 门课程")

        # 更新配置
        api_key = self.api_key_entry.get().strip()
        CONFIG["deepseek"]["api_key"] = api_key
        CONFIG["deepseek"]["enabled"] = bool(api_key)
        CONFIG["schedule"]["start_hour"] = int(self.start_hour.get())
        CONFIG["schedule"]["end_hour"] = int(self.end_hour.get())
        CONFIG["schedule"]["max_daily_hours"] = int(self.max_hours.get())

        self._save_config()

        threading.Thread(target=self._run_thread, args=(selected,),
                         daemon=True).start()

    def _run_thread(self, selected_courses):
        try:
            from core.course import CourseManager
            from core.player import VideoPlayer
            from core.answer import AIAnswerer
            from core.anti_detect import inject_on_new_page
            from scheduler.human_scheduler import HumanScheduler
            from utils.random_delay import human_delay

            scheduler = HumanScheduler(CONFIG.get("schedule", {}))
            answerer = AIAnswerer(CONFIG.get("deepseek", {}))
            player = VideoPlayer(self.page, CONFIG.get("safety", {}))
            course_mgr = CourseManager(self.page, [])

            for idx, course in enumerate(selected_courses):
                if not self.running:
                    break

                if not scheduler.can_study_now():
                    self.after(0, lambda: self._log("⏰ 不在学习时段，等待中..."))
                    scheduler.wait_until_next_day()

                self.after(0, lambda n=course['name'], i=idx: self._log(
                    f"\n📚 [{i+1}/{len(selected_courses)}] {n}"))

                chapters = course_mgr.get_chapters(course["url"])
                if not chapters:
                    self.after(0, lambda: self._log("⚠️ 无章节，跳过"))
                    continue

                scheduler.start_session()

                for ch_idx, ch in enumerate(chapters):
                    if not self.running:
                        break
                    if ch.get("completed"):
                        continue

                    if scheduler.should_take_break():
                        self.after(0, lambda: self._log("☕ 休息中..."))
                        scheduler.take_break()
                        scheduler.start_session()
                        if not scheduler.can_study_now():
                            break

                    self.after(0, lambda n=ch['name'], i=ch_idx: self._log(
                        f"  📖 [{i+1}/{len(chapters)}] {n}"))

                    if course_mgr.navigate_to_chapter(ch):
                        t0 = time.time()
                        player.play_current_page()
                        scheduler.record_study_time(time.time() - t0)
                        answerer.handle_quiz(self.page)
                        human_delay(
                            CONFIG["safety"]["chapter_switch_delay_min"],
                            CONFIG["safety"]["chapter_switch_delay_max"])

            self.after(0, lambda: self._log("\n🎉 所有选中课程处理完成！"))
            self.after(0, lambda: self._log(f"📊 {answerer.get_token_summary()}"))

        except Exception as e:
            self.after(0, lambda: self._log(f"❌ 运行错误: {e}"))

        finally:
            self.running = False
            self.after(0, lambda: self.start_btn.config(state="normal"))
            self.after(0, lambda: self.stop_btn.config(state="disabled"))

    def _on_stop(self):
        self.running = False
        self._log("🛑 正在停止...")
        self.stop_btn.config(state="disabled")

    # ============================================================
    # 配置持久化
    # ============================================================
    def _save_config(self):
        cfg_path = os.path.join(os.path.dirname(__file__), "saved_config.json")
        data = {
            "phone": self.phone_entry.get().strip(),
            "password": self.pwd_entry.get().strip(),
            "api_key": self.api_key_entry.get().strip(),
            "start_hour": self.start_hour.get(),
            "end_hour": self.end_hour.get(),
            "max_hours": self.max_hours.get(),
        }
        try:
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_saved_config(self):
        cfg_path = os.path.join(os.path.dirname(__file__), "saved_config.json")
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("phone"):
                self.phone_entry.insert(0, data["phone"])
            if data.get("password"):
                self.pwd_entry.insert(0, data["password"])
            if data.get("api_key"):
                self.api_key_entry.insert(0, data["api_key"])
            if data.get("start_hour"):
                self.start_hour.delete(0, "end")
                self.start_hour.insert(0, data["start_hour"])
            if data.get("end_hour"):
                self.end_hour.delete(0, "end")
                self.end_hour.insert(0, data["end_hour"])
            if data.get("max_hours"):
                self.max_hours.delete(0, "end")
                self.max_hours.insert(0, data["max_hours"])
        except Exception:
            pass

    def _load_env_api_key(self):
        """从 .env / CONFIG 自动填入 API Key"""
        if not self.api_key_entry.get().strip():
            env_key = CONFIG.get("deepseek", {}).get("api_key", "")
            if env_key:
                self.api_key_entry.insert(0, env_key)
                self._log("[OK] DeepSeek API Key loaded from .env")

    def _update_progress(self, done, total, label=""):
        """更新进度条"""
        pct = int(done / total * 100) if total > 0 else 0
        self.progress_bar["value"] = pct
        self.progress_pct.config(text=f"{pct}%")
        if label:
            self.progress_label.config(text=label)

    def on_closing(self):
        if self.browser_mgr:
            try:
                self.browser_mgr.quit()
            except Exception:
                pass
        self.destroy()


def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
