param(
    [string]$Exe = "China2EX_fontfix8.exe",
    [string]$OutDir = "reverse\ghidra_export"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$DecompilerRoot = Join-Path $Root "tools\decompiler"
$Jdk = Get-ChildItem $DecompilerRoot -Directory -Filter "jdk-*" | Select-Object -First 1
if (-not $Jdk) {
    throw "Portable JDK not found under $DecompilerRoot"
}

$env:JAVA_HOME = $Jdk.FullName
$env:PATH = (Join-Path $env:JAVA_HOME "bin") + ";" + $env:PATH

$Ghidra = Join-Path $DecompilerRoot "ghidra_12.1.2_PUBLIC\support\analyzeHeadless.bat"
if (!(Test-Path $Ghidra)) {
    throw "Ghidra analyzeHeadless not found: $Ghidra"
}

$ProjectRoot = Join-Path $DecompilerRoot "ghidra_projects"
$ProjectName = "CHNIII"
$Output = Join-Path $Root $OutDir
$ScriptPath = Join-Path $Root "tools\reverse_probe"
$ExePath = Join-Path $Root $Exe

New-Item -ItemType Directory -Force $ProjectRoot, $Output | Out-Null

if (Test-Path (Join-Path $ProjectRoot "$ProjectName.gpr")) {
    & $Ghidra $ProjectRoot $ProjectName -process (Split-Path $ExePath -Leaf) -noanalysis `
        -scriptPath $ScriptPath -postScript GhidraSemanticAnnotate.java
    & $Ghidra $ProjectRoot $ProjectName -process (Split-Path $ExePath -Leaf) -noanalysis `
        -scriptPath $ScriptPath -postScript GhidraExport.java $Output
}
else {
    & $Ghidra $ProjectRoot $ProjectName -import $ExePath `
        -scriptPath $ScriptPath -postScript GhidraSemanticAnnotate.java -postScript GhidraExport.java $Output -overwrite
}
