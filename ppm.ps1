[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$Command,
    
    [Parameter(Position=1)]
    [string]$SubCommand,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$RootDir = $PSScriptRoot

if (Test-Path (Join-Path $RootDir "backend\.venv\Scripts\python.exe")) {
    $VenvPython = Join-Path $RootDir "backend\.venv\Scripts\python.exe"
    $ManagePy = Join-Path $RootDir "backend\manage.py"
    $BackendDir = Join-Path $RootDir "backend"
} elseif (Test-Path (Join-Path $RootDir ".venv\Scripts\python.exe")) {
    $VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
    $ManagePy = Join-Path $RootDir "manage.py"
    $BackendDir = $RootDir
} else {
    Write-Host "[PPM Error] Python virtual environment not found in .venv or backend\.venv" -ForegroundColor Red
    exit 1
}

if ($Command -eq "run") {
    switch ($SubCommand) {
        "dev" {
            Write-Host "[PPM] Starting Django backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
            & $VenvPython $ManagePy runserver @RemainingArgs
            return
        }
        "test" {
            Write-Host "[PPM] Running backend test suite..." -ForegroundColor Cyan
            & $VenvPython -m pytest $BackendDir @RemainingArgs
            return
        }
        "migrate" {
            Write-Host "[PPM] Applying database migrations..." -ForegroundColor Cyan
            & $VenvPython $ManagePy migrate @RemainingArgs
            return
        }
        "makemigrations" {
            Write-Host "[PPM] Creating database migrations..." -ForegroundColor Cyan
            & $VenvPython $ManagePy makemigrations @RemainingArgs
            return
        }
        "shell" {
            & $VenvPython $ManagePy shell @RemainingArgs
            return
        }
        default {
            & $VenvPython $ManagePy $SubCommand @RemainingArgs
            return
        }
    }
}

if ($Command -eq "dev") {
    Write-Host "[PPM] Starting Django backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
    & $VenvPython $ManagePy runserver @RemainingArgs
    return
}

if ($Command -eq "test") {
    Write-Host "[PPM] Running backend test suite..." -ForegroundColor Cyan
    & $VenvPython -m pytest $BackendDir @RemainingArgs
    return
}

if ([string]::IsNullOrWhiteSpace($Command)) {
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host " PPM - Python Portfolio Manager (Django Task Runner)" -ForegroundColor Green
    Write-Host "===================================================" -ForegroundColor Green
    Write-Host " Usage:"
    Write-Host "   .\ppm run dev           - Start Django development server"
    Write-Host "   .\ppm run test          - Run backend test suite"
    Write-Host "   .\ppm run migrate       - Apply database migrations"
    Write-Host "   .\ppm run makemigrations- Create migrations"
    Write-Host "   .\ppm [command]         - Forward command directly to Django manage.py"
    Write-Host "===================================================" -ForegroundColor Green
    return
}

& $VenvPython $ManagePy $Command $SubCommand @RemainingArgs
