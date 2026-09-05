# screen_off.ps1 - ดับจอด้วยซอฟต์แวร์
#
# ต่างจากการกดปุ่มปิดที่ตัวจอ: วิธีนี้แค่สั่งจอดับ ไม่ได้ตัดการเชื่อมต่อ
# Windows ยังเห็นจออยู่ resolution ไม่เปลี่ยน เกมจึงไม่หลุดจาก fullscreen
# -> พิกัดคลิกของบอทไม่เพี้ยน
#
# ขยับเมาส์หรือกดปุ่มใดก็ได้ จอจะกลับมาเอง

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class MonitorPower {
    [DllImport("user32.dll")]
    public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@

$wait = 3
Write-Host ""
Write-Host "  จะดับจอในอีก $wait วินาที" -ForegroundColor Yellow
Write-Host "  อย่าขยับเมาส์/กดปุ่มระหว่างนี้ ไม่งั้นจอจะเด้งกลับมาทันที" -ForegroundColor DarkGray
Write-Host ""
for ($i = $wait; $i -ge 1; $i--) {
    Write-Host "  $i..." -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host ""

$HWND_BROADCAST  = [IntPtr]0xFFFF
$WM_SYSCOMMAND   = 0x0112
$SC_MONITORPOWER = [IntPtr]0xF170
$POWER_OFF       = [IntPtr]2

[MonitorPower]::SendMessage($HWND_BROADCAST, $WM_SYSCOMMAND, $SC_MONITORPOWER, $POWER_OFF) | Out-Null
