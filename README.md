# 🐣 Little Chick Focus · 小鸡专注

> 一只戴圆框眼镜、捧着数学书的小鸡，陪你守住每一段完整的时间。
> A small Windows desk buddy that keeps you company through every uninterrupted stretch of work — and never asks for your account.

本地优先、零联网的 Windows 桌面计时器：没有账号，没有云端，没有偷偷上传的统计。
A local-first Windows desktop timer: no account, no cloud, no quiet analytics upload.

## ✨ 亮点 / Highlights

- **截止优先的倒计时 / Deadline-first countdown** — 填一个时刻（`21:00`）是在追截止，填一段时长（`45`、`1.5h`）是在守一段完整时间；实心黑环随时间融化，过点后自动切成正计时，每 20 分钟轻推一次。
  Type a target time (`21:00`) to race a deadline, or a duration (`45` / `1.5h`) to protect a block. A solid black ring melts away as time runs out; past the deadline it flips into overtime counting with a nudge every 20 minutes.
- **走神提醒 / Wander nudge** — 专注中键鼠空闲满 1 分钟，屏幕正中弹出一张卡：「走神啦！记录存档稍后再想吧」。写一句刚去哪儿了存档，或者直接跳过；计时一秒都没停。
  During a session, one minute without keyboard or mouse brings up a centered card. Jot down where your mind went, or skip it — the clock never pauses.
- **悬浮小鸡 / Floating chick companion** — 开始专注就收成一枚透明贴纸小鸡，倒计时胶囊贴在它头顶，可以拖到屏幕任何角落。
  Start a session and the app folds into a transparent sticker chick; the countdown pill rides on its head and drags anywhere.
- **诚实的微信提醒 / Honest WeChat nudge** — 微信停在前台超过 1 分钟就居中提醒一次；算的是每一次，不累计。
  If WeChat stays in the foreground for over a minute, a centered pop-up reminds you — per occurrence, never cumulative.
- **熄屏自动保存 / Sleep-safe saving** — 屏幕一灭就存盘；单次超过 10 小时自动按最后一次操作时间截断，睡一觉不会污染统计。
  Saves the moment the screen goes dark, and trims any session past 10 hours back to your last input so a nap can't poison the numbers.
- **自愈的小鸡 / Self-healing daemon** — 计划任务每 5 分钟巡查一次，进程没了就拉起来；单实例锁保证任何时候只有一只小鸡。
  A Windows scheduled task checks every 5 minutes and revives the app if it dies; a single-instance lock guarantees one chick and one only.
- **本地记录页 / Local records page** — 内嵌 HTTP 服务在 `127.0.0.1` 上渲染每日事项、专注明细和走神记录。
  An embedded HTTP server renders daily tasks, session details and wander notes on `127.0.0.1`.

## 🛠 技术栈 / Tech stack

- Python 3 + Tkinter —— 纯标准库，零第三方依赖 / pure standard library, zero third-party dependencies
- 内嵌 HTTP 服务（`http.server`）承载记录页 / embedded HTTP server for the records page
- Win32 API —— DPI 感知缩放、键鼠空闲检测（`GetLastInputInfo`）、单实例锁（`OpenProcess`）/ DPI-aware scaling, idle detection, single-instance lock
- Windows 集成 —— 启动文件夹自启 + 计划任务守护 / auto-start via Startup folder plus a scheduled-task watchdog

## 🔧 工程细节 / Engineering details

- 「截止」输入双通道解析：12/24 小时智能推断（晚上说 `9:00` 就是 21:00）、过点自动顺延到明天、支持 `45` / `45min` / `1.5h` / `2小时`
  Dual-mode deadline parser: smart 12/24-hour inference, auto-rollover to tomorrow once the time has passed, and duration forms.
- 填充式圆环：转一整圈 = 1 小时，剩余越少黑色越少；过点显示 `+HH:MM:SS`
  Fill-style ring: one full turn equals one hour, emptying as time runs out; overtime shows `+HH:MM:SS`.
- PID 锁 + `OpenProcess` 存活检测，从源头掐掉「两只小鸡」
  Single-instance PID lock with a liveness check — kills the double-chick problem at the source.
- 走神检测靠 `GetLastInputInfo` 取最后一次键鼠操作，配合开机锚点抵消睡眠漂移；同一段空闲只提醒一次，回来碰键鼠后重新计
  Idle detection derives the last input time from `GetLastInputInfo`, anchored to boot time so sleep drift can't break it; each idle stretch nudges you once and restarts after you come back.
- 熄屏边缘触发自动保存 + 10 小时上限，全部按真实操作时间校准
  Edge-triggered screen-off auto-save plus a 10-hour cap, both calibrated against real input time.
- 全局异常钩子把崩溃写进 `error.log`，`pythonw` 静默退出也留痕
  A global exception hook writes to `error.log`, so a silent `pythonw` crash never loses its trail.

## 🚀 快速开始 / Quick start

1. 双击 `start.bat`（用 `pythonw` 启动，不弹黑框）/ Double-click `start.bat` (launches via `pythonw`, no console flash)
2. 需要 Windows + Python 3（自带 Tkinter）/ Requires Windows + Python 3 (Tkinter included)

## 🔒 数据与隐私 / Data & privacy

所有记录都在 `%LOCALAPPDATA%\LittleChickFocus\`：`sessions.json` 存专注记录，`wander.json` 存走神存档，`focus.lock` 存进程号。一个字都不出本机。
Everything lives in `%LOCALAPPDATA%\LittleChickFocus\`: `sessions.json` for sessions, `wander.json` for wander notes, `focus.lock` for the PID. Nothing leaves your machine.

## ⌨️ 快捷键 / Shortcuts

| 操作 / Action | 效果 / Does |
|---|---|
| `Esc` | 收成悬浮小鸡 / Fold to the floating chick |
| 左键点小鸡 / Left-click chick | 展开主窗 / Expand the main window |
| 右键点小鸡 / Right-click chick | 打开每日记录页 / Open the daily records page |

## 📜 更新日志 / Changelog

See [CHANGELOG.md](CHANGELOG.md) — v1.0 首次孵化 / first hatch → v1.1 截止重写 / deadline rewrite → v1.2 自愈小鸡 / self-healing chick → v1.3 走神提醒 / wander nudge.
