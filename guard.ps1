# 小鸡专注守护脚本：检测 focus.py 进程，不存在则自动拉起；存在多个则只保留最早一个
# 由 Windows 任务计划程序每 5 分钟调用一次
$ErrorActionPreference = 'SilentlyContinue'
$out = "C:\Users\33155\Documents\Codex\2026-10-06\ban\outputs"
$pyw = "C:\Program Files\Python312\pythonw.exe"
$log = Join-Path $env:LOCALAPPDATA 'LittleChickFocus\guard.log'

function Get-FocusProcs {
    Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -like '*focus.py*' }
}

$procs = @(Get-FocusProcs)

# 去重：发现多个实例 → 保留创建最早的一个，杀掉其余
if ($procs.Count -gt 1) {
    $keep = $procs | Sort-Object CreationDate | Select-Object -First 1
    $dead = $procs | Where-Object { $_.ProcessId -ne $keep.ProcessId }
    foreach ($p in $dead) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Add-Content -Encoding UTF8 $log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 检测到 $($procs.Count) 个实例，保留 PID $($keep.ProcessId)，清理 $($dead.ProcessId -join ',')"
    $procs = @($keep)
}

if ($procs.Count -eq 0) {
    try {
        Start-Process $pyw -ArgumentList 'focus.py' -WorkingDirectory $out
        Start-Sleep -Seconds 2
        $check = @(Get-FocusProcs)
        if ($check.Count -gt 0) {
            Add-Content -Encoding UTF8 $log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 已自动拉起 PID $($check.ProcessId -join ',')"
        } else {
            Add-Content -Encoding UTF8 $log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 拉起失败"
        }
    } catch {
        Add-Content -Encoding UTF8 $log "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') 守护脚本异常: $_"
    }
}
