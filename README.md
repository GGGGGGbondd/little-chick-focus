# 🐣 Little Chick Focus · 小鸡专注

> 一只戴圆框眼镜、捧着数学书的小鸡，陪你守住每一段完整的时间。
> A tiny Windows desk buddy that turns "I should focus" into a habit — with a hand-drawn chick that keeps you company while you work. Local-first, zero telemetry, quietly resilient.

## ✨ Highlights

- **Deadline-first countdown** — set a target time (`21:00`) or a duration (`45min` / `1.5h`); a solid black ring melts away as time runs out, then flips into overtime tracking with a nudge every 20 minutes.
- **Floating chick companion** — start a session and the app folds into a transparent sticker chick; the countdown pill rides right on its head, draggable anywhere on screen.
- **Self-healing daemon** — a Windows scheduled task checks every 5 minutes and revives the app if it ever dies; a single-instance lock guarantees only one chick exists at a time.
- **Honest WeChat nudge** — if WeChat stays in the foreground for over a minute, a centered pop-up reminds you *this time* (per occurrence, not cumulative).
- **Sleep-safe saving** — auto-saves when the screen goes dark, and truncates any session beyond 10 hours so a nap can't poison your stats.
- **Zero telemetry** — every session lives in a local JSON file. No cloud, no account, no network.

## 🛠 Tech stack

- **Python 3 + Tkinter** — pure standard library, zero third-party dependencies
- **Embedded HTTP server** (`http.server`) — serves the daily records page on `127.0.0.1`
- **Win32 API** — DPI-aware scaling, screen-off detection (WMI), single-instance lock (`OpenProcess`)
- **Windows integration** — auto-start via Startup folder, scheduled-task watchdog

## 🔧 Engineering details

- Dual-mode deadline parser: smart 12/24-hour inference (`9:00` in the evening → 21:00), auto-rollover to tomorrow when the time has passed, and duration forms (`45`, `45min`, `1.5h`, `2小时`)
- Fill-style countdown ring: full ring = all remaining time, shrinking to zero at the deadline; overtime switches to `+HH:MM:SS`
- Single-instance PID lock + `OpenProcess` liveness check — kills the double-chick problem at the source
- Edge-triggered screen-off auto-save + 10-hour cap with a boot-time anchor to survive sleep/wake clock drift
- Global exception handler writes to `error.log` so a silent `pythonw` crash never loses its trail

## 🚀 Quick start

1. Double-click `start.bat` (launches via `pythonw`, no console flash)
2. Requires Windows + Python 3 (Tkinter included)

## 🔒 Data & privacy

Sessions are stored locally at `%LOCALAPPDATA%\LittleChickFocus\sessions.json`. Nothing ever leaves your machine.

## ⌨️ Shortcuts

| Key / action | Does |
|---|---|
| `Esc` | Fold to the floating chick |
| Left-click chick | Expand the main window |
| Right-click chick | Open the daily records page |
