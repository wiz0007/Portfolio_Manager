@echo off
setlocal enabledelayedexpansion

set "CURR_DIR=%~dp0"
if "%CURR_DIR:~-1%"=="\" set "CURR_DIR=%CURR_DIR:~0,-1%"

if exist "%CURR_DIR%\backend\.venv\Scripts\python.exe" (
    set "VENV_PYTHON=%CURR_DIR%\backend\.venv\Scripts\python.exe"
    set "MANAGE_PY=%CURR_DIR%\backend\manage.py"
    set "BACKEND_DIR=%CURR_DIR%\backend"
) else if exist "%CURR_DIR%\.venv\Scripts\python.exe" (
    set "VENV_PYTHON=%CURR_DIR%\.venv\Scripts\python.exe"
    set "MANAGE_PY=%CURR_DIR%\manage.py"
    set "BACKEND_DIR=%CURR_DIR%"
) else (
    echo [PPM Error] Python virtual environment not found in .venv or backend\.venv
    exit /b 1
)

set "CMD=%~1"
set "SUBCMD=%~2"

set "REST_ARGS="
set "ARG_IDX=0"
for %%A in (%*) do (
    set /a "ARG_IDX+=1"
    if !ARG_IDX! gtr 2 (
        set "REST_ARGS=!REST_ARGS! %%A"
    )
)

if /i "%CMD%"=="run" (
    if /i "%SUBCMD%"=="dev" (
        echo [PPM] Starting Django backend on http://127.0.0.1:8000 ...
        "%VENV_PYTHON%" "%MANAGE_PY%" runserver !REST_ARGS!
        exit /b %ERRORLEVEL%
    )
    if /i "%SUBCMD%"=="test" (
        echo [PPM] Running backend test suite...
        "%VENV_PYTHON%" -m pytest "%BACKEND_DIR%" !REST_ARGS!
        exit /b %ERRORLEVEL%
    )
    if /i "%SUBCMD%"=="migrate" (
        echo [PPM] Applying database migrations...
        "%VENV_PYTHON%" "%MANAGE_PY%" migrate !REST_ARGS!
        exit /b %ERRORLEVEL%
    )
    if /i "%SUBCMD%"=="makemigrations" (
        echo [PPM] Creating database migrations...
        "%VENV_PYTHON%" "%MANAGE_PY%" makemigrations !REST_ARGS!
        exit /b %ERRORLEVEL%
    )
    if /i "%SUBCMD%"=="shell" (
        "%VENV_PYTHON%" "%MANAGE_PY%" shell !REST_ARGS!
        exit /b %ERRORLEVEL%
    )
    "%VENV_PYTHON%" "%MANAGE_PY%" %SUBCMD% !REST_ARGS!
    exit /b %ERRORLEVEL%
)

if /i "%CMD%"=="dev" (
    echo [PPM] Starting Django backend on http://127.0.0.1:8000 ...
    "%VENV_PYTHON%" "%MANAGE_PY%" runserver %SUBCMD% !REST_ARGS!
    exit /b %ERRORLEVEL%
)

if /i "%CMD%"=="test" (
    echo [PPM] Running backend test suite...
    "%VENV_PYTHON%" -m pytest "%BACKEND_DIR%" %SUBCMD% !REST_ARGS!
    exit /b %ERRORLEVEL%
)

if "%CMD%"=="" (
    echo ===================================================
    echo  PPM - Python Portfolio Manager ^(Django Task Runner^)
    echo ===================================================
    echo  Usage:
    echo    .\ppm run dev            - Start Django development server
    echo    .\ppm run test           - Run backend test suite
    echo    .\ppm run migrate        - Apply database migrations
    echo    .\ppm run makemigrations - Create migrations
    echo    .\ppm [command]          - Forward command directly to Django manage.py
    echo ===================================================
    exit /b 0
)

"%VENV_PYTHON%" "%MANAGE_PY%" %*
exit /b %ERRORLEVEL%
