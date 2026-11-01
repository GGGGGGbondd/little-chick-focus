# -*- coding: utf-8 -*-
"""小鸡专注计时器（新版 UI）
- 浮窗：透明小鸡贴纸（chick.png，圆眼镜+蓝书，无问号），可拖动、单击展开、右键打开记录；
- 主窗：计时卡片 + 黑色进度环 + 微信前台时长统计；
- 记录仍保存在 %LOCALAPPDATA%\\LittleChickFocus\\sessions.json。
"""
import json, os, threading, time, webbrowser, http.server, sys
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, font as tkfont
import ctypes
from ctypes import wintypes

# ---- DPI 感知（100% 缩放时无影响；高 DPI 下保证清晰） ----
SCALE = 1.0
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    hdc = ctypes.windll.user32.GetDC(0)
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
    ctypes.windll.user32.ReleaseDC(0, hdc)
    SCALE = max(1.0, dpi / 96.0)
except Exception:
    pass

def sp(v):
    return max(1, round(v * SCALE))

APP_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'LittleChickFocus'
APP_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = APP_DIR / 'sessions.json'
ERROR_LOG = APP_DIR / 'error.log'
HTML_FILE = Path(__file__).with_name('index.html')
CHICK_PNG = Path(__file__).with_name('chick.png')
CHICK_SMALL = Path(__file__).with_name('chick_small.png')
PORT = 0


# ---- 全局异常兜底：pythonw 无控制台，未捕获异常会无声退出，这里落盘日志 ----
def _log_exception(exc_type, exc, tb):
    try:
        with open(ERROR_LOG, 'a', encoding='utf-8') as f:
            f.write('\n=== %s ===\n' % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            traceback.print_exception(exc_type, exc, tb, file=f)
    except Exception:
        pass


import traceback
sys.excepthook = _log_exception

# Tk 回调内的异常同样记录（默认只打印到 stderr，pythonw 下 sys.stderr 为 None 会二次崩溃）
_orig_report = tk.Tk.report_callback_exception
def _report_callback_exception(self, exc, val, tb):
    _log_exception(exc, val, tb)
    try:
        _orig_report(self, exc, val, tb)
    except Exception:
        pass  # pythonw 无 stderr 时原始实现会抛 AttributeError，吞掉即可，绝不终止进程
tk.Tk.report_callback_exception = _report_callback_exception

# ---- 配色（方案3：黑白框架 + 淡黄点缀；GOLD 沿用旧名，实际为黑色主色） ----
BG    = '#ffffff'
CARD  = '#ffffff'
INK   = '#111111'
MUTED = '#111111'
GOLD  = '#111111'
GOLD_D = '#222222'
LINE  = '#111111'
SOFT  = '#111111'          # 悬停底色：黑（悬停统一黑底白字）
DISABLED_BG = CARD        # 禁用态：白底（界面已无淡黄）
DISABLED_TX = INK          # 禁用态文字：黑
MAGENTA = '#ff00ff'

F_TITLE = ('Microsoft YaHei UI', 16, 'bold')
F_SUB   = ('Microsoft YaHei UI', 9)
F_SMALL = ('Microsoft YaHei UI', 8)
F_BODY  = ('Microsoft YaHei UI', 10)
F_BTN   = ('Microsoft YaHei UI', 10, 'bold')
F_CLOCK = ('Consolas', 22, 'bold')
F_ENTRY = ('Microsoft YaHei UI', 13)
F_PILL  = ('Microsoft YaHei UI', 9, 'bold')


def load_sessions():
    try:
        return json.loads(DATA_FILE.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return []


def save_sessions(items):
    DATA_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/sessions'):
            body = json.dumps(load_sessions(), ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body)
            return
        try:
            body = HTML_FILE.read_bytes()
        except OSError:
            body = b'App file missing'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def start_server():
    global PORT
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    PORT = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()


class RoundedButton(tk.Canvas):
    """圆角按钮（Canvas 绘制，支持悬停、禁用、自适应拉伸）"""

    def __init__(self, master, text, command=None, *, font=None, fg=INK, bg=CARD,
                 hover=SOFT, border=LINE, accent=False, hover_fg='#ffffff', padx=16, pady=10, radius=16,
                 stretch=False):
        f = font or F_BODY
        tf = tkfont.Font(root=master, font=f)
        width = tf.measure(text) + padx * 2
        height = tf.metrics('linespace') + pady * 2
        super().__init__(master, width=width, height=height, bg=master.cget('bg'),
                         highlightthickness=0, bd=0, cursor='hand2')
        self._text = text
        self._command = command
        self._font = f
        self._radius = radius
        self._stretch = stretch
        self._state = 'normal'
        self._fill = GOLD if accent else bg
        self._outline = GOLD_D if accent else border
        self._text_fill = '#ffffff' if accent else fg
        self._hover_fg = hover_fg if hover_fg is not None else ('#ffffff' if accent else INK)
        self._hover_fill = GOLD_D if accent else hover
        self._hover_outline = GOLD_D if accent else border
        self._rect = None
        self._draw()
        if stretch:
            self.bind('<Configure>', lambda e: self._draw())
        self.bind('<Button-1>', lambda e: self._click())
        self.bind('<Enter>', lambda e: self._set_hover(True))
        self.bind('<Leave>', lambda e: self._set_hover(False))

    def _draw(self):
        self.delete('all')
        w = self.winfo_width()
        if w <= 1:
            w = int(self['width'])
        h = self.winfo_height()
        if h <= 1:
            h = int(self['height'])
        if self._state == 'normal':
            fill, outline = self._fill, self._outline
        else:
            fill, outline = DISABLED_BG, self._outline
        # 规矩的直角矩形：填充 + 完整矩形描边
        self._rect = self.create_rectangle(1, 1, w - 2, h - 2, fill=fill, outline=outline, width=2)
        self.create_text(w / 2, h / 2, text=self._text,
                         fill=self._text_fill if self._state == 'normal' else DISABLED_TX,
                         font=self._font, tags='txt')

    def _set_hover(self, on):
        if self._state != 'normal' or self._rect is None:
            return
        self.itemconfigure(self._rect,
                           fill=self._hover_fill if on else self._fill,
                           outline=self._hover_outline if on else self._outline)
        self.itemconfigure('txt', fill=self._hover_fg if on else self._text_fill)

    def set_text(self, text):
        self._text = text
        self.itemconfigure('txt', text=text)

    def _click(self):
        if self._state == 'normal' and self._command:
            self._command()

    def set_state(self, state):
        self._state = state
        self.configure(cursor='arrow' if state != 'normal' else 'hand2')
        self._draw()


class App:
    def __init__(self, root):
        self.root = root
        root.title('小鸡专注')
        root.geometry(f'{sp(380)}x{sp(612)}')
        root.resizable(False, False)
        root.configure(bg=BG)
        root.attributes('-topmost', True)
        self.started = None
        self.session_start = None
        self.elapsed = 0
        self.running = False
        self.paused = False
        self.wechat_seconds = 0
        self.last_sample = None
        self.deadline = None            # 截止时刻 epoch；None = 纯正向计时
        self._deadline_warned = set()   # 已提醒的截止标记（1h/30m/15m）
        self._ot_warned = 0             # 超时后已提醒的 20min 档数
        self._dl_placeholder = True
        self._tick_count = 0
        self._display_was_off = False   # 屏幕状态边沿检测：上一次是否已熄屏
        self._boot_wall = None          # 系统启动的墙钟锚点（睡眠自愈用）
        self._last_dw = 0               # 上一次 GetLastInputInfo dwTime（回绕补偿用）
        self._wx_active = False    # 当前是否处于微信前台
        self._wx_since = 0.0       # 本次进入微信前台的时间
        self._wx_warned = False    # 本次会话是否已提醒过 1 分钟
        self.bubble = None
        self._drag_origin = None
        self._chick_img = None
        self._placeholder = True
        self.task_text = None
        self._build_ui()
        self.create_bubble()
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        w = sp(420)
        h = self.root.winfo_reqheight()
        self.root.geometry(f'{w}x{h}+{(sw - w) // 2}+60')
        self.root.deiconify()
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.tick()

    # ---------- 主窗口 UI ----------
    def _build_ui(self):
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill='both', expand=True, padx=sp(20), pady=sp(20))

        # 头部（无小鸡，纯标题）
        header = tk.Frame(shell, bg=BG)
        header.pack(fill='x', pady=(0, sp(12)))
        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side='left')
        tk.Label(title_box, text='专注一下', font=F_TITLE, bg=BG, fg=INK).pack(anchor='w')
        tk.Label(title_box, text='给重要的事留一点完整时间', font=F_SUB, bg=BG, fg=MUTED).pack(anchor='w', pady=(sp(2), 0))

        # 计时卡片
        card = tk.Frame(shell, bg=CARD, highlightthickness=2, highlightbackground=LINE, highlightcolor=LINE)
        card.pack(fill='x')
        tk.Label(card, text='正在专注', font=F_SMALL, bg=CARD, fg=MUTED).pack(anchor='w', padx=sp(18), pady=(sp(15), sp(5)))
        self.task = tk.Entry(card, font=F_ENTRY, relief='flat', bg=CARD, fg=INK,
                             insertbackground=GOLD, highlightthickness=2, highlightbackground=LINE,
                             highlightcolor=GOLD)
        self.task.insert(0, '例如：阅读、写作、学习')
        self.task.configure(fg=MUTED)
        self.task.pack(fill='x', padx=sp(18), pady=(0, sp(10)), ipady=sp(7))
        self.task.bind('<FocusIn>', self._clear_placeholder)
        tk.Label(card, text='截止（可选）：填 21:00=到点 / 填 45 或 1.5h=专注多久',
                 font=F_SMALL, bg=CARD, fg=MUTED).pack(anchor='w', padx=sp(18), pady=(0, sp(2)))
        self.deadline_entry = tk.Entry(card, font=F_ENTRY, relief='flat', bg=CARD, fg=MUTED,
                                       insertbackground=GOLD, highlightthickness=2, highlightbackground=LINE,
                                       highlightcolor=GOLD)
        self.deadline_entry.insert(0, '例如 21:00')
        self.deadline_entry.pack(fill='x', padx=sp(18), pady=(0, sp(12)), ipady=sp(5))
        self.deadline_entry.bind('<FocusIn>', self._clear_dl_placeholder)
        tk.Frame(card, bg=LINE, height=2).pack(fill='x', padx=sp(18))

        ring_box = tk.Frame(card, bg=CARD)
        ring_box.pack(pady=(sp(6), sp(2)))
        rs = sp(135)
        self.ring = tk.Canvas(ring_box, width=rs, height=rs, bg=CARD, highlightthickness=0)
        self.ring.pack()
        pad = sp(10)
        bbox = (pad, pad, rs - pad, rs - pad)
        self.arc = self.ring.create_arc(*bbox, start=-90, extent=0, style='arc', outline=INK, width=sp(6))
        self.clock = tk.Label(ring_box, text='00:00:00', font=F_CLOCK, bg=CARD, fg=INK)
        self.clock.place(relx=0.5, rely=0.5, anchor='center')
        self.status = tk.Label(card, text='写好事项，点「开始专注」', font=F_SMALL, bg=CARD, fg=MUTED)
        self.status.pack(pady=(0, sp(12)))

        # 主按钮（开始 / 暂停·继续 / 结束）
        self.btns = tk.Frame(shell, bg=BG)
        self.btns.pack(fill='x', pady=(sp(12), sp(6)))
        self.go = RoundedButton(self.btns, '开始专注', command=self.start, accent=True,
                                font=F_BTN, padx=sp(10), pady=sp(11), stretch=True)
        self.go.pack(side='left', fill='x', expand=True, padx=0)
        self.pause_btn = RoundedButton(self.btns, '暂停', command=self.toggle_pause,
                                       font=F_BTN, padx=sp(10), pady=sp(11), stretch=True)
        self.stop = RoundedButton(self.btns, '结束并保存', command=self.finish,
                                  font=F_BTN, padx=sp(10), pady=sp(11), stretch=True)

        # 微信统计
        status = tk.Frame(shell, bg=CARD, highlightthickness=2, highlightbackground=LINE, highlightcolor=LINE)
        status.pack(fill='x', pady=(sp(6), sp(10)))
        tk.Label(status, text='本次微信前台时间', font=F_SMALL, bg=CARD, fg=MUTED).pack(side='left', padx=sp(14), pady=sp(10))
        self.wechat_status = tk.Label(status, text='00:00:00', font=('Consolas', 11, 'bold'), bg=CARD, fg='#111111')
        self.wechat_status.pack(side='right', padx=sp(14))

        # 底部（悬停恢复黑底白字）
        RoundedButton(shell, '打开每日专注记录', command=self.open_page, font=F_BODY,
                      padx=sp(12), pady=sp(9), stretch=True, hover=INK, hover_fg='#ffffff').pack(fill='x', pady=(0, sp(6)))
        RoundedButton(shell, '收起到小鸡球，继续计时', command=self.collapse, font=F_BODY,
                      padx=sp(12), pady=sp(9), stretch=True, hover=INK, hover_fg='#ffffff').pack(fill='x')

        self.root.bind('<Escape>', lambda e: self.collapse())
        self.root.protocol('WM_DELETE_WINDOW', self.collapse)

    def _clear_placeholder(self, event=None):
        if self._placeholder:
            self.task.delete(0, 'end')
            self.task.configure(fg=INK)
            self._placeholder = False

    def _clear_dl_placeholder(self, event=None):
        if self._dl_placeholder:
            self.deadline_entry.delete(0, 'end')
            self.deadline_entry.configure(fg=INK)
            self._dl_placeholder = False

    def _parse_deadline(self):
        """解析截止：'HH:MM'=截止时刻；'45'/'45min'=分钟；'1.5h'=小时。空/非法 → None"""
        try:
            if self._dl_placeholder:
                return None
            s = self.deadline_entry.get().strip()
            if not s:
                return None
            import re
            # 1) HH:MM → 截止时刻
            m = re.match(r'^(\d{1,2}):(\d{1,2})$', s)
            if m:
                hh, mm = int(m.group(1)), int(m.group(2))
                if not (0 <= hh < 24 and 0 <= mm < 60):
                    return None
                now = datetime.now()
                hh24 = hh
                if hh < 12 and now.hour >= 12:
                    hh24 = hh + 12      # 现在是下午/晚上：9:00 自动理解为晚上 21:00
                dl = now.replace(hour=hh24, minute=mm, second=0, microsecond=0)
                if dl <= now:
                    dl = dl + timedelta(days=1)   # 该时刻已过 → 视为明天
                return dl.timestamp()
            # 2) 小时：1.5h / 2小时
            m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:h|hr|小时)$', s, re.I)
            if m:
                return time.time() + float(m.group(1)) * 3600
            # 3) 分钟：45min / 45分钟；纯数字 45 也按分钟
            m = re.match(r'^(\d+(?:\.\d+)?)\s*(?:min|m|分钟)?$', s, re.I)
            if m:
                return time.time() + float(m.group(1)) * 60
            return None
        except Exception:
            return None

    # ---------- 浮窗小鸡 ----------
    def create_bubble(self):
        self.bubble = tk.Toplevel(self.root)
        self.bubble.overrideredirect(True)
        self.bubble.attributes('-topmost', True)
        self.bubble.attributes('-transparentcolor', MAGENTA)
        self.bubble.configure(bg=MAGENTA)
        W, H = sp(116), sp(126)
        self.bubble.geometry(f'{W}x{H}+{sp(80)}+{sp(180)}')
        canvas = tk.Canvas(self.bubble, width=W, height=H, bg=MAGENTA, highlightthickness=0)
        canvas.pack()
        self._bubble_canvas = canvas
        if CHICK_PNG.exists():
            try:
                self._chick_img = tk.PhotoImage(file=str(CHICK_PNG))
                canvas.create_image(W / 2, sp(90), image=self._chick_img)
            except Exception:
                self._chick_img = None
        if self._chick_img is None:
            self._draw_chick(canvas)
        self._pill = canvas.create_oval(0, 0, 0, 0, fill=CARD, outline=LINE, width=2, state='hidden')
        self._bubble_time = canvas.create_text(W / 2, sp(48), text='', fill=INK, font=F_PILL, state='hidden')
        for widget in (self.bubble, canvas):
            widget.bind('<ButtonPress-1>', self.bubble_press)
            widget.bind('<B1-Motion>', self.bubble_drag)
            widget.bind('<ButtonRelease-1>', self.bubble_release)
            widget.bind('<Button-3>', lambda e: self.open_page())

    def _draw_chick(self, c):
        """chick.png 缺失时的兜底画法"""
        brown, yellow, orange, blue, white, gray = ('#85473d', '#ffd42c', '#f68a25',
                                                    '#3192ec', '#fff4dc', '#9a9690')
        c.create_oval(11, 8, 59, 58, fill=yellow, outline=brown, width=3)
        c.create_oval(6, 31, 20, 48, fill=yellow, outline=brown, width=3)
        c.create_oval(51, 31, 65, 48, fill=yellow, outline=brown, width=3)
        c.create_polygon(32, 29, 40, 29, 36, 35, fill=orange, outline=brown, width=1)
        c.create_polygon(16, 39, 36, 42, 36, 64, 16, 61, fill=blue, outline=brown, width=2)
        c.create_polygon(36, 42, 58, 38, 58, 61, 36, 64, fill='#2781dc', outline=brown, width=2)
        c.create_line(36, 43, 36, 63, fill=brown, width=1)
        c.create_text(36, 49, text='M', fill=white, font=('Segoe UI', 7, 'bold'))
        c.create_oval(13, 17, 34, 38, outline=gray, width=1)
        c.create_oval(37, 17, 58, 38, outline=gray, width=1)
        c.create_line(34, 23, 37, 23, fill=gray, width=1)
        c.create_line(13, 22, 8, 20, fill=gray, width=1)
        c.create_line(58, 22, 63, 20, fill=gray, width=1)
        c.create_oval(21, 25, 27, 29, fill=brown, outline=brown)
        c.create_oval(44, 25, 50, 29, fill=brown, outline=brown)
        c.create_line(22, 20, 27, 19, fill=brown, width=2, capstyle='round')
        c.create_line(44, 19, 49, 20, fill=brown, width=2, capstyle='round')

    def update_bubble(self):
        c = self._bubble_canvas
        if self.running:
            now_ts = time.time()
            if self.deadline:
                remaining = self.deadline - now_ts
                t = self.fmt_short(max(0, remaining)) if remaining >= 0 else '+' + self.fmt_short(int(-remaining))
            else:
                total = self.elapsed + (int(now_ts - self.started) if not self.paused else 0)
                t = self.fmt_short(total)
            w = tkfont.Font(font=F_PILL).measure(t) + sp(22)
            c.coords(self._pill, sp(58) - w / 2, sp(36), sp(58) + w / 2, sp(60))
            c.itemconfigure(self._pill, state='normal')
            c.itemconfigure(self._bubble_time, state='normal', text=t)
        else:
            c.itemconfigure(self._pill, state='hidden')
            c.itemconfigure(self._bubble_time, state='hidden')

    def bubble_press(self, e):
        self._drag_origin = (e.x_root, e.y_root, self.bubble.winfo_x(), self.bubble.winfo_y())

    def bubble_drag(self, e):
        if self._drag_origin:
            sx, sy, wx, wy = self._drag_origin
            self.bubble.geometry(f'+{wx + e.x_root - sx}+{wy + e.y_root - sy}')

    def bubble_release(self, e):
        if self._drag_origin and abs(e.x_root - self._drag_origin[0]) + abs(e.y_root - self._drag_origin[1]) < 6:
            self.expand()
        self._drag_origin = None

    def expand(self):
        self.root.deiconify()
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.task.focus_set()

    def collapse(self):
        self.root.withdraw()
        self.bubble.deiconify()
        self.bubble.lift()

    # ---------- 计时逻辑 ----------
    def start(self):
        if self.running:
            return
        if self._placeholder or not self.task.get().strip():
            messagebox.showinfo('写下专注事项', '先写下你现在想专注的事情。')
            return
        self.task_text = self.task.get().strip()
        self.task.configure(state='disabled')
        self.elapsed = 0
        self.paused = False
        self.started = time.time()
        self.session_start = self.started
        self.running = True
        self.wechat_seconds = 0
        self.last_sample = time.monotonic()
        self.deadline = self._parse_deadline()
        self._deadline_warned = set()
        self._ot_warned = 0
        # 有截止时间：初始满黑圈（=全部剩余时间），随倒计时越变越少
        self.ring.itemconfigure(self.arc, extent=359 if self.deadline else 0)
        self.deadline_entry.configure(state='disabled')
        self._wx_active = False
        self._wx_since = 0.0
        self._wx_warned = False
        self._apply_controls()
        self.collapse()   # 开始后自动退到小鸡球：隐藏主窗、显示浮窗，计时照常

    def _apply_controls(self):
        """按状态刷新按钮与提示文字：空闲 / 专注中 / 已暂停"""
        if not self.running:
            self.go.pack(side='left', fill='x', expand=True, padx=0)
            self.pause_btn.pack_forget()
            self.stop.pack_forget()
            self.go.set_state('normal')
            self.status.configure(text='写好事项，点「开始专注」')
        elif self.paused:
            self.go.pack_forget()
            self.pause_btn.pack(side='left', fill='x', expand=True, padx=(sp(5), sp(5)))
            self.stop.pack(side='left', fill='x', expand=True, padx=(sp(5), 0))
            self.pause_btn.set_state('normal')
            self.pause_btn.set_text('继续')
            self.stop.set_state('normal')
            self.status.configure(text='已暂停，点「继续」接着专注')
        else:
            self.go.pack_forget()
            self.pause_btn.pack(side='left', fill='x', expand=True, padx=(sp(5), sp(5)))
            self.stop.pack(side='left', fill='x', expand=True, padx=(sp(5), 0))
            self.pause_btn.set_state('normal')
            self.pause_btn.set_text('暂停')
            self.stop.set_state('normal')
            self.status.configure(text='专注中，小鸡在旁边安静陪着你')

    def toggle_pause(self):
        if not self.running:
            return
        if self.paused:
            self.resume()
        else:
            self.pause()

    def pause(self):
        if not self.running or self.paused:
            return
        self.elapsed += int(time.time() - self.started)
        self.started = None
        self.paused = True
        self.clock.configure(text=self.fmt(self.elapsed))
        self._apply_controls()
        self.update_bubble()

    def resume(self):
        if not self.running or not self.paused:
            return
        self.started = time.time()
        self.last_sample = time.monotonic()
        self.paused = False
        self._apply_controls()

    def finish(self, ended_at=None, quiet=False, note=''):
        """结束本次专注并保存。ended_at: 自定义结束时间戳(秒)；quiet: 不弹提示框；note: 附加备注"""
        if not self.running:
            return
        end_ts = int(ended_at) if ended_at else int(time.time())
        seconds = self.elapsed
        if not self.paused:
            seconds += max(0, end_ts - int(self.started))
        self.elapsed = seconds
        self.running = False
        self.paused = False
        self.started = None
        self.task.configure(state='normal')
        self.deadline = None
        self._deadline_warned = set()
        self._ot_warned = 0
        self.deadline_entry.configure(state='normal')
        self._apply_controls()
        self.status.configure(text='记好啦，休息一下 🐣')
        items = load_sessions()
        rec = {
            'task': self.task_text or '',
            'start': datetime.fromtimestamp(self.session_start).isoformat(timespec='seconds'),
            'end': datetime.fromtimestamp(end_ts).isoformat(timespec='seconds'),
            'seconds': seconds,
            'wechat_seconds': self.wechat_seconds,
            'wechat_minutes': round(self.wechat_seconds / 60, 1),
            'wechat_tracking': 'foreground-window',
        }
        if note:
            rec['note'] = note
        items.append(rec)
        save_sessions(items)
        self.started = None
        self.clock.configure(text=self.fmt(self.elapsed))
        self.ring.itemconfigure(self.arc, extent=0)
        self.update_bubble()
        if not quiet:
            messagebox.showinfo('本次已记录', f'专注 {self.fmt(seconds)}，检测到微信在前台 {self.fmt(self.wechat_seconds)}。')
        self.collapse()

    @staticmethod
    def fmt(n):
        n = int(n)
        return f'{n // 3600:02d}:{n % 3600 // 60:02d}:{n % 60:02d}'

    @staticmethod
    def fmt_short(n):
        n = max(0, int(n))
        h, m, s = n // 3600, n % 3600 // 60, n % 60
        return f'{h}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'

    def tick(self):
        if self.running and not self.paused:
            now = time.monotonic()
            self._tick_count += 1
            if self._tick_count % 4 == 0:   # 每 4 次 tick（约 1 秒）检测一次微信，减少高频子进程
                wx = self._wechat_is_foreground()
                if wx:
                    # 每次打开微信：新会话开始计时，连续满 60 秒提醒一次
                    if not self._wx_active:
                        self._wx_active = True
                        self._wx_since = now
                        self._wx_warned = False
                    elif not self._wx_warned and now - self._wx_since >= 60:
                        self._wx_warned = True
                        self._show_wx_warning()
                    if self.last_sample is not None:
                        self.wechat_seconds += min(now - self.last_sample, 2.0)
                else:
                    self._wx_active = False
                    self._wx_warned = False
                self.last_sample = now
            total = self.elapsed + int(time.time() - self.started)
            # 兜底：单次专注超过 10 小时 → 自动结束，截断到最后一次操作电脑的时间
            if total >= 10 * 3600:
                last = self._last_input_time()
                ended = None
                if last is not None:
                    ended = max(int(last), int(self.session_start))
                self.finish(ended_at=ended, quiet=True, note='超过10小时自动截断')
                self.root.after(250, self.tick)
                return
            # 屏幕熄灭（约每 40 次 tick = 10 秒检查一次）→ 自动停止并保存
            if self._tick_count % 40 == 0:
                off = self._display_is_off()
                if off and not self._display_was_off:
                    self._display_was_off = True
                    if self.running and not self.paused:
                        self.finish(quiet=True, note='屏幕熄灭自动保存')
                        self.root.after(250, self.tick)
                        return
                elif not off:
                    self._display_was_off = False
            now_ts = time.time()
            if self.deadline:
                remaining = self.deadline - now_ts
                if remaining >= 0:
                    clock_text = self.fmt(remaining)
                    for name, sec in (('1h', 3600), ('30m', 1800), ('15m', 900)):
                        if name not in self._deadline_warned and remaining <= sec:
                            self._deadline_warned.add(name)
                            self._show_deadline_warning(f'离截止还有 {self.fmt_short(remaining)}')
                    span = max(1, self.deadline - self.session_start)
                    frac = min(1.0, max(0.0, (now_ts - self.session_start) / span))
                    arc_extent = (1 - frac) * 359   # 满圈=剩余时间，随时间越变越少
                else:
                    over = int(-remaining)
                    clock_text = '+' + self.fmt_short(over)
                    ticks = over // 1200   # 每超时 20 分钟提醒一次
                    if ticks > self._ot_warned:
                        self._ot_warned = ticks
                        self._show_deadline_warning(f'已超时 {self.fmt_short(over)}，该收尾啦')
                    arc_extent = 0   # 超时：圈已空
            else:
                clock_text = self.fmt(total)
                arc_extent = (total % 3600) * 0.1
            self.clock.configure(text=clock_text)
            self.wechat_status.configure(text=self.fmt(int(self.wechat_seconds)))
            self.ring.itemconfigure(self.arc, extent=arc_extent)
            self.update_bubble()
        elif self.running and self.paused:
            self.clock.configure(text=self.fmt(self.elapsed))
        self.root.after(250, self.tick)

    def _show_wx_warning(self):
        """每次微信前台连续超过 1 分钟：居中弹提醒浮窗（非累计）"""
        try:
            top = tk.Toplevel(self.root)
            top.overrideredirect(True)
            top.attributes('-topmost', True)
            w, h = sp(320), sp(96)
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            top.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
            c = tk.Canvas(top, width=w, height=h, bg=CARD,
                          highlightthickness=2, highlightbackground=LINE, highlightcolor=LINE)
            c.pack(fill='both', expand=True)
            c.create_text(w / 2, h / 2 - sp(12), text='用微信超过 1 分钟啦', font=F_BTN, fill=INK)
            c.create_text(w / 2, h / 2 + sp(14), text='点一下关闭，回去专注吧', font=F_SMALL, fill=INK)
            c.bind('<Button-1>', lambda e: top.destroy())
            top.after(10000, top.destroy)
        except Exception:
            pass

    def _show_deadline_warning(self, msg):
        """截止倒计时提醒：居中弹窗，点击或 10 秒自动关闭"""
        try:
            top = tk.Toplevel(self.root)
            top.overrideredirect(True)
            top.attributes('-topmost', True)
            w, h = sp(380), sp(110)
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            top.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
            c = tk.Canvas(top, width=w, height=h, bg=CARD,
                          highlightthickness=2, highlightbackground=LINE, highlightcolor=LINE)
            c.pack(fill='both', expand=True)
            c.create_text(w / 2, h / 2 - sp(14), text=msg, font=F_BTN, fill=INK)
            c.create_text(w / 2, h / 2 + sp(16), text='点一下关闭', font=F_SMALL, fill=MUTED)
            c.bind('<Button-1>', lambda e: top.destroy())
            top.after(10000, top.destroy)
        except Exception:
            pass

    def _wechat_is_foreground(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            import subprocess
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid.value}', '/FO', 'CSV', '/NH'],
                                    capture_output=True, text=True, encoding='mbcs',
                                    creationflags=0x08000000, timeout=1)
            name = result.stdout.split(',')[0].strip('"').lower()
            return name in ('weixin.exe', 'wechat.exe')
        except Exception:
            return False

    def _display_is_off(self):
        """查询物理显示器电源状态：所有显示器都未激活(Active=False) = 屏幕已熄灭"""
        try:
            import subprocess
            ps = ("$m = Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness; "
                  "if ($m -eq $null) { 'unknown' } "
                  "elseif (@($m | Where-Object { $_.Active }).Count -eq 0) { 'off' } else { 'on' }")
            r = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                               capture_output=True, text=True, encoding='utf-8', errors='replace',
                               timeout=8, creationflags=0x08000000)
            lines = [l.strip().lower() for l in r.stdout.splitlines() if l.strip()]
            return bool(lines) and lines[-1] == 'off'
        except Exception:
            return False

    def _last_input_time(self):
        """最后一次键盘/鼠标输入的时刻（epoch 秒）；失败返回 None。
        用系统启动的墙钟锚点换算：睡眠(S3)时 GetTickCount 停走而墙钟继续，
        直接 time.time()-idle 会在唤醒后失准，故锚点取历史最小值自愈。"""
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [('cbSize', wintypes.UINT), ('dwTime', wintypes.DWORD)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                return None
            dw = lii.dwTime
            if self._last_dw is not None and dw < self._last_dw:
                dw += 2 ** 32   # GetTickCount 49.7 天回绕补偿
            self._last_dw = dw
            boot = time.time() - ctypes.windll.kernel32.GetTickCount64() / 1000.0
            if self._boot_wall is None or boot < self._boot_wall:
                self._boot_wall = boot  # 取最小锚点：睡眠唤醒后 uptime 停滞会算出偏晚的 boot，丢弃
            return self._boot_wall + dw / 1000.0
        except Exception:
            return None

    def open_page(self):
        webbrowser.open(f'http://127.0.0.1:{PORT}/')


def _single_instance_lock():
    """单实例锁：已有 focus.py 在运行则返回 False，本进程应直接退出。
    用 PID 锁文件 + OpenProcess 存活检测，防止双击/守护拉起多个实例互相打架。"""
    try:
        lock = APP_DIR / 'focus.lock'
        if lock.exists():
            old = int(lock.read_text().strip())
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, old)  # PROCESS_QUERY_LIMITED_INFORMATION
            if h:
                code = ctypes.c_ulong()
                ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
                ctypes.windll.kernel32.CloseHandle(h)
                if code.value == 259:  # STILL_ACTIVE
                    return False
        lock.write_text(str(os.getpid()))
        return True
    except Exception:
        return True  # 锁机制异常时放行，不让正常功能被锁误伤


if __name__ == '__main__':
    if not _single_instance_lock():
        sys.exit(0)  # 已有实例在运行，本实例直接退出
    start_server()
    root = tk.Tk()
    app = App(root)
    if '--show' in sys.argv:
        root.after(400, app.expand)
    root.mainloop()
