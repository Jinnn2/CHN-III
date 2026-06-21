param(
    [ValidateSet("", "Keep4x3", "Fill", "Windowed")]
    [string]$LaunchMode = "",
    [string]$GameExeName = "China2EX_fontfix8.exe"
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$gameExe = Join-Path $root $GameExeName
$configPath = Join-Path $root "dgVoodoo.conf"
$saveDir = Join-Path $root "Save"
$backupDir = Join-Path $root "ModernBackups"

function Assert-GameReady {
    param([string]$SelectedGameExe)

    if (!(Test-Path $SelectedGameExe)) {
        throw "Missing $(Split-Path -Leaf $SelectedGameExe)."
    }
    if (!(Test-Path $configPath)) {
        throw "Missing dgVoodoo.conf. The modern graphics wrapper is not installed."
    }
}

function Set-ConfigValue {
    param(
        [string[]]$Lines,
        [string]$Name,
        [string]$Value
    )

    $pattern = "^\s*" + [regex]::Escape($Name) + "\s*="
    $replacement = "{0,-36}= {1}" -f $Name, $Value
    $changed = $false

    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match $pattern) {
            $Lines[$i] = $replacement
            $changed = $true
        }
    }

    if (!$changed) {
        $Lines += $replacement
    }

    return $Lines
}

function Get-DesktopResolution {
    $display = Get-CimInstance Win32_VideoController |
        Where-Object { $_.CurrentHorizontalResolution -and $_.CurrentVerticalResolution } |
        Sort-Object @{ Expression = { $_.CurrentHorizontalResolution * $_.CurrentVerticalResolution }; Descending = $true } |
        Select-Object -First 1

    if ($display) {
        return ("{0}x{1}" -f $display.CurrentHorizontalResolution, $display.CurrentVerticalResolution)
    }

    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    return ("{0}x{1}" -f $bounds.Width, $bounds.Height)
}

function Get-4x3Resolution {
    param([string]$DesktopResolution)

    if ($DesktopResolution -match "^(\d+)x(\d+)$") {
        $width = [int]$Matches[1]
        $height = [int]$Matches[2]

        if (($width / $height) -gt (4 / 3)) {
            $targetHeight = $height
            $targetWidth = [int][Math]::Floor($height * 4 / 3)
        }
        else {
            $targetWidth = $width
            $targetHeight = [int][Math]::Floor($width * 3 / 4)
        }

        return ("{0}x{1}" -f $targetWidth, $targetHeight)
    }

    return "max_4_3"
}

function Set-Mode {
    param(
        [ValidateSet("Keep4x3", "Fill", "Windowed")] [string]$Mode,
        [string]$SelectedGameExe = $gameExe
    )

    Assert-GameReady $SelectedGameExe

    $desktop = Get-DesktopResolution
    $resolution4x3 = Get-4x3Resolution $desktop
    $lines = [System.IO.File]::ReadAllLines($configPath)

    $lines = Set-ConfigValue $lines "OutputAPI" "d3d11_fl11_0"
    $lines = Set-ConfigValue $lines "DesktopResolution" $desktop
    $lines = Set-ConfigValue $lines "VRAM" "1024"
    $lines = Set-ConfigValue $lines "dgVoodooWatermark" "false"
    $lines = Set-ConfigValue $lines "DefaultEnumeratedResolutions" "classics"
    $lines = Set-ConfigValue $lines "ExtraEnumeratedResolutions" ""

    if ($Mode -eq "Keep4x3") {
        $lines = Set-ConfigValue $lines "FullScreenMode" "true"
        $lines = Set-ConfigValue $lines "ScalingMode" "stretched_4_3"
        $lines = Set-ConfigValue $lines "FullscreenAttributes" "fake"
        $lines = Set-ConfigValue $lines "WindowedAttributes" ""
        $lines = Set-ConfigValue $lines "Resolution" $resolution4x3
        $lines = Set-ConfigValue $lines "KeepWindowAspectRatio" "true"
        $lines = Set-ConfigValue $lines "CenterAppWindow" "false"
        $lines = Set-ConfigValue $lines "ExtraEnumeratedResolutions" $resolution4x3
    }
    elseif ($Mode -eq "Fill") {
        $lines = Set-ConfigValue $lines "FullScreenMode" "true"
        $lines = Set-ConfigValue $lines "ScalingMode" "stretched"
        $lines = Set-ConfigValue $lines "FullscreenAttributes" "fake"
        $lines = Set-ConfigValue $lines "WindowedAttributes" ""
        $lines = Set-ConfigValue $lines "Resolution" "desktop"
        $lines = Set-ConfigValue $lines "KeepWindowAspectRatio" "false"
        $lines = Set-ConfigValue $lines "CenterAppWindow" "false"
    }
    else {
        $lines = Set-ConfigValue $lines "FullScreenMode" "false"
        $lines = Set-ConfigValue $lines "ScalingMode" "centered"
        $lines = Set-ConfigValue $lines "FullscreenAttributes" ""
        $lines = Set-ConfigValue $lines "WindowedAttributes" ""
        $lines = Set-ConfigValue $lines "Resolution" "unforced"
        $lines = Set-ConfigValue $lines "KeepWindowAspectRatio" "true"
        $lines = Set-ConfigValue $lines "CenterAppWindow" "true"
    }

    [System.IO.File]::WriteAllLines($configPath, $lines, [System.Text.Encoding]::ASCII)
}

function Start-Game {
    param(
        [ValidateSet("Keep4x3", "Fill", "Windowed")] [string]$Mode,
        [string]$SelectedGameExe = $gameExe
    )

    Set-Mode $Mode $SelectedGameExe
    Start-Process -FilePath $SelectedGameExe -WorkingDirectory $root
}

if ($LaunchMode) {
    Start-Game $LaunchMode
    return
}

function Backup-Saves {
    if (!(Test-Path $saveDir)) {
        throw "Save folder was not found."
    }

    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $zipPath = Join-Path $backupDir ("Save-{0}.zip" -f $stamp)
    Compress-Archive -Path (Join-Path $saveDir "*") -DestinationPath $zipPath -Force
    return $zipPath
}

function Show-Error {
    param([string]$Message)
    [System.Windows.Forms.MessageBox]::Show($Message, "China2 Modern Launcher", "OK", "Error") | Out-Null
}

function New-Button {
    param(
        [string]$Text,
        [int]$Top,
        [scriptblock]$OnClick
    )

    $button = New-Object System.Windows.Forms.Button
    $button.Text = $Text
    $button.Left = 18
    $button.Top = $Top
    $button.Width = 344
    $button.Height = 38
    $button.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)
    $button.Add_Click($OnClick)
    return $button
}

$form = New-Object System.Windows.Forms.Form
$form.Text = "China2 Modern Launcher"
$form.ClientSize = New-Object System.Drawing.Size(380, 408)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)

$title = New-Object System.Windows.Forms.Label
$title.Text = "China II - Modern Launcher"
$title.Left = 18
$title.Top = 16
$title.Width = 344
$title.Height = 24
$title.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 11, [System.Drawing.FontStyle]::Bold)
$form.Controls.Add($title)

$subtitle = New-Object System.Windows.Forms.Label
$subtitle.Text = "Choose a display mode. 4:3 aspect mode is recommended."
$subtitle.Left = 18
$subtitle.Top = 44
$subtitle.Width = 344
$subtitle.Height = 22
$subtitle.ForeColor = [System.Drawing.Color]::DimGray
$form.Controls.Add($subtitle)

$form.Controls.Add((New-Button "Launch - force 4:3 aspect ratio (recommended)" 78 {
    try { Start-Game "Keep4x3"; $form.Close() } catch { Show-Error $_.Exception.Message }
}))

$form.Controls.Add((New-Button "Launch - fill screen (stretched)" 122 {
    try { Start-Game "Fill"; $form.Close() } catch { Show-Error $_.Exception.Message }
}))

$form.Controls.Add((New-Button "Launch - windowed mode" 166 {
    try { Start-Game "Windowed"; $form.Close() } catch { Show-Error $_.Exception.Message }
}))

$form.Controls.Add((New-Button "Launch modtest - internal 1280x1024" 210 {
    try {
        $modtestExe = Join-Path $root "China2EX_modtest.exe"
        Start-Game "Windowed" $modtestExe
        $form.Close()
    } catch { Show-Error $_.Exception.Message }
}))

$form.Controls.Add((New-Button "Launch modtest - internal 1600x1200" 254 {
    try {
        $modtestExe = Join-Path $root "China2EX_modtest_1600x1200.exe"
        Start-Game "Windowed" $modtestExe
        $form.Close()
    } catch { Show-Error $_.Exception.Message }
}))

$form.Controls.Add((New-Button "Backup saves" 298 {
    try {
        $zipPath = Backup-Saves
        [System.Windows.Forms.MessageBox]::Show("Save files backed up to:`r`n$zipPath", "China2 Modern Launcher", "OK", "Information") | Out-Null
    }
    catch { Show-Error $_.Exception.Message }
}))

$form.Controls.Add((New-Button "Open dgVoodoo settings" 342 {
    try {
        $cpl = Join-Path $root "dgVoodooCpl.exe"
        if (!(Test-Path $cpl)) { throw "Missing dgVoodooCpl.exe." }
        Start-Process -FilePath $cpl -WorkingDirectory $root
    }
    catch { Show-Error $_.Exception.Message }
}))

[void]$form.ShowDialog()
