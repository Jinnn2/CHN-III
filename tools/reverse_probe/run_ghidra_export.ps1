param(
    [string]$Exe = "China2EX_fontfix8.exe",
    [string]$OutDir = "reverse\ghidra_export",
    [switch]$AllFunctions
)

$ErrorActionPreference = "Stop"

function Test-Jdk21Home {
    param([string]$JdkPath)
    if (-not $JdkPath) {
        return $false
    }
    if (-not (Test-Path (Join-Path $JdkPath "bin\java.exe"))) {
        return $false
    }
    $ReleaseFile = Join-Path $JdkPath "release"
    if (-not (Test-Path $ReleaseFile)) {
        return $false
    }
    return [bool](Get-Content $ReleaseFile | Select-String -Pattern 'JAVA_VERSION="(2[1-9]|[3-9][0-9])\.')
}

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$DecompilerRoot = Join-Path $Root "tools\decompiler"
$Jdk = Get-ChildItem $DecompilerRoot -Directory -Filter "jdk-*" | Select-Object -First 1
if ($Jdk) {
    $env:JAVA_HOME = $Jdk.FullName
    $env:PATH = (Join-Path $env:JAVA_HOME "bin") + ";" + $env:PATH
}
else {
    $JdkCandidates = @(
        "C:\Program Files\Microsoft\jdk-21.0.7.6-hotspot",
        "C:\Program Files\Java\jdk-21",
        "C:\Program Files\Eclipse Adoptium\jdk-21*",
        $env:JAVA_HOME
    ) | Where-Object { $_ }
    $JdkHome = $null
    foreach ($Candidate in $JdkCandidates) {
        $Matches = Get-ChildItem $Candidate -Directory -ErrorAction SilentlyContinue
        if (Test-Jdk21Home $Candidate) {
            $JdkHome = $Candidate
            break
        }
        foreach ($Match in $Matches) {
            if (Test-Jdk21Home $Match.FullName) {
                $JdkHome = $Match.FullName
                break
            }
        }
        if ($JdkHome) {
            break
        }
    }
    if ($JdkHome) {
        $env:JAVA_HOME = $JdkHome
        $env:PATH = (Join-Path $env:JAVA_HOME "bin") + ";" + $env:PATH
    }
    elseif (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        throw "No portable JDK under $DecompilerRoot and java.exe is not on PATH"
    }
}

$Ghidra = Join-Path $DecompilerRoot "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
if (!(Test-Path $Ghidra)) {
    throw "Ghidra analyzeHeadless not found: $Ghidra"
}

if ($env:JAVA_HOME) {
    $LaunchProperties = Join-Path $DecompilerRoot "ghidra_12.1.2_PUBLIC\support\launch.properties"
    if (Test-Path $LaunchProperties) {
        $JavaHomeOverride = $env:JAVA_HOME.Replace('\', '/')
        $LaunchConfig = Get-Content $LaunchProperties
        $LaunchConfig = $LaunchConfig | ForEach-Object {
            if ($_ -match '^JAVA_HOME_OVERRIDE=') {
                "JAVA_HOME_OVERRIDE=$JavaHomeOverride"
            }
            else {
                $_
            }
        }
        Set-Content -Path $LaunchProperties -Value $LaunchConfig -Encoding ASCII
    }
}

$ProjectRoot = Join-Path $DecompilerRoot "ghidra_projects"
$ProjectName = "CHNIII"
$Output = Join-Path $Root $OutDir
$ScriptPath = Join-Path $Root "tools\reverse_probe"
$ExePath = Join-Path $Root $Exe

New-Item -ItemType Directory -Force $ProjectRoot, $Output | Out-Null

$ExportArgs = @($Output)
if ($AllFunctions) {
    $ExportArgs += "--all-functions"
}

if (Test-Path (Join-Path $ProjectRoot "$ProjectName.gpr")) {
    & $Ghidra $ProjectRoot $ProjectName -process (Split-Path $ExePath -Leaf) -noanalysis `
        -scriptPath $ScriptPath -postScript GhidraSemanticAnnotate.java
    & $Ghidra $ProjectRoot $ProjectName -process (Split-Path $ExePath -Leaf) -noanalysis `
        -scriptPath $ScriptPath -postScript GhidraExport.java $ExportArgs
}
else {
    & $Ghidra $ProjectRoot $ProjectName -import $ExePath `
        -scriptPath $ScriptPath -postScript GhidraSemanticAnnotate.java -postScript GhidraExport.java $ExportArgs -overwrite
}
