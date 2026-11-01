# Changelog

All the notable changes to Little Chick Focus — how the chick grew up, version by version.

## [v1.2.0] — 2026-10-30 · The self-healing chick

### Added
- **Single-instance lock** — PID lock file + `OpenProcess` liveness check. No matter how many times you double-click `start.bat`, only one chick ever hatches. (Kills the infamous "double-chick chaos" at the source.)
- **Watchdog dedup** — the 5-minute guardian now keeps the oldest chick and cleans up extras, so the flock never grows by accident.
- Deadline nudges at **1h / 30min / 15min** before the deadline, and **every 20min** once you're past it.

### Changed
- The ring stays invisible until a deadline is set — then it melts from a full black ring to empty as time runs out; overtime keeps it empty while showing `+HH:MM:SS`.
- Window height adapts to content, so the fold-to-chick button is never clipped off-screen.
- Launch now shows the main window immediately, centered and always-on-top.

### Fixed
- PowerShell 5.1 misreading BOM-less UTF-8 (the source of garbled guardian logs).
- Deadline "already passed → roll to tomorrow" silently failing due to a `timedelta` typo.

## [v1.1.0] — 2026-10-20 · The deadline rewrite

### Added
- **Deadline-first countdown** — set a target time (`21:00`) or a duration (`45min` / `1.5h`); count down to it, then flip into overtime tracking.
- **Smart 12/24-hour inference** — `9:00` in the evening means 21:00; a time that already passed rolls to tomorrow automatically.
- Floating chick sticker (two feather tufts, round glasses, blue book — marker-sketch style), draggable anywhere.
- Time pill rides right on the chick's head.
- **Honest WeChat nudge** — a centered popup for *every* foreground minute over 60s (per occurrence, never cumulative).
- Fold-to-chick on start; `Esc` to fold; pause / resume with a state-switching button row.

### Changed
- Black & white UI, no greys.
- Fill-style hour ring: full when you start, empty after one hour.

## [v1.0.0] — 2026-10-07 · First hatch

### Added
- First working Windows Tkinter timer: write a task → start / stop, log WeChat minutes, browse a daily records page served by an embedded HTTP server.
- Sessions stored locally in `%LOCALAPPDATA%\LittleChickFocus\sessions.json` — zero network, zero telemetry.
- Auto-start via the Startup folder; daily records page with totals, filters and history.
- Global exception handler writes to `error.log` so a silent `pythonw` crash never loses its trail.
