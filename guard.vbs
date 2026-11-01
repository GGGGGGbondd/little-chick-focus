' 小鸡专注守护 VBS 包装：以隐藏窗口方式运行 guard.ps1（任务计划程序直接跑 powershell 会闪窗）
Set sh = CreateObject("WScript.Shell")
sh.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Users\33155\Documents\Codex\2026-10-06\ban\outputs\guard.ps1""", 0, True
