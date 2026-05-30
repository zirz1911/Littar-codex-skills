# Auto-reload GemLogin UI after db change
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
using System.Diagnostics;
public class WinAPI {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@

# Match any GemLogin process with a visible window title (main window)
$proc = Get-Process | Where-Object {
    ($_.ProcessName -like '*GemLogin*' -or $_.ProcessName -like '*gemlogin*') -and
    $_.MainWindowTitle -and $_.MainWindowTitle.Trim().Length -gt 0
} | Select-Object -First 1

if (-not $proc) {
    Write-Host 'NOT_FOUND'
    exit 1
}

[WinAPI]::SetForegroundWindow($proc.MainWindowHandle) | Out-Null
Start-Sleep -Milliseconds 500

$zero = [UIntPtr]::Zero
[WinAPI]::keybd_event(0x11, 0, 0, $zero)   # Ctrl down
[WinAPI]::keybd_event(0x52, 0, 0, $zero)   # R down
Start-Sleep -Milliseconds 100
[WinAPI]::keybd_event(0x52, 0, 2, $zero)   # R up
[WinAPI]::keybd_event(0x11, 0, 2, $zero)   # Ctrl up

Write-Host 'OK'
