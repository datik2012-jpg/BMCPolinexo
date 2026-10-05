param(
    [ValidatePattern('^\d+\.\d+\.\d+$')][string]$Version = '1.2.1',
    [string]$Python = 'python',
    [string]$Iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
Push-Location $repo
try {
    if (-not (Test-Path -LiteralPath $Iscc)) { throw 'Install Inno Setup 6.5.4 or supply -Iscc with its ISCC.exe path.' }
    & $Python -c "import sys,struct; assert sys.version_info[:2] == (3,12) and struct.calcsize('P') == 8, 'Python 3.12 x64 required'"
    if ($LASTEXITCODE) { throw 'Python prerequisite check failed.' }
    $nodeVersion = & node --version
    if ($nodeVersion -notlike 'v22.*') { throw 'Node.js 22 is required on the build machine.' }
    & $Python packaging/windows/audit_excel.py
    if ($LASTEXITCODE) { throw 'Excel Git audit failed.' }
    & $Python -m venv .build-venv
    if ($LASTEXITCODE) { throw 'Failed to create build environment.' }
    $buildPython = Join-Path $repo '.build-venv/Scripts/python.exe'
    & $buildPython -m pip install -r packaging/windows/requirements-build.txt
    if ($LASTEXITCODE) { throw 'Build dependency installation failed.' }
    Push-Location frontend
    try {
        & npm.cmd ci
        if ($LASTEXITCODE) { throw 'npm ci failed.' }
        & npm.cmd run build
        if ($LASTEXITCODE) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
    # Compare built public files to a fixed, reviewed asset manifest.
    & $buildPython packaging/windows/verify_bundle.py --web frontend/dist
    if ($LASTEXITCODE) { throw 'Frontend artifact audit failed.' }
    & $buildPython -m PyInstaller --noconfirm --clean --distpath dist/windows --workpath build/windows packaging/windows/BMCPolinexo.spec
    if ($LASTEXITCODE) { throw 'PyInstaller failed.' }
    & $buildPython packaging/windows/verify_bundle.py --bundle dist/windows/BMCPolinexo
    if ($LASTEXITCODE) { throw 'Bundle audit failed.' }
    $bundle = Join-Path $repo 'dist/windows/BMCPolinexo'
    $output = Join-Path $repo "dist/releases/$Version"
    & $Iscc /Q "/DAppVersion=$Version" "/DBundleDir=$bundle" "/DOutputDirPath=$output" packaging/windows/installer.iss
    if ($LASTEXITCODE) { throw 'Installer compilation failed.' }
    Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $output 'BMCPolinexo-Setup.exe')
} finally { Pop-Location }
