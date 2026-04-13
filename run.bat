@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

set "VENV_DIR=%ROOT_DIR%.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "REQ_FILE=%ROOT_DIR%requirements.txt"
set "REQ_STAMP=%VENV_DIR%\.requirements.sha256"
set "DB_FILE=%ROOT_DIR%data\behaviour_ai.db"
set "APP_FILE=%ROOT_DIR%app.py"
set "INIT_DB_FILE=%ROOT_DIR%scripts\init_db.py"

echo ==================================================
echo BehaviourAI Windows Bootstrap
echo ==================================================

call :ResolvePython || goto :fail
call :CheckPythonVersion || goto :fail
call :EnsureVenv || goto :fail
call :InstallDependencies || goto :fail
call :InitializeDatabase || goto :fail

echo.
echo [START] Launching BehaviourAI...
"%VENV_PYTHON%" "%APP_FILE%"
if errorlevel 1 goto :fail

goto :success

:ResolvePython
set "PYTHON_EXE="
set "PYTHON_ARGS="

where py >nul 2>&1 && (
	py -3.11 -c "import sys" >nul 2>&1 && (
		set "PYTHON_EXE=py"
		set "PYTHON_ARGS=-3.11"
	)
)

if not defined PYTHON_EXE (
	where python >nul 2>&1 && (
		set "PYTHON_EXE=python"
		set "PYTHON_ARGS="
	)
)

if not defined PYTHON_EXE (
	echo [ERROR] Python was not found on PATH.
	exit /b 1
)

exit /b 0

:CheckPythonVersion
set "PY_MAJOR="
set "PY_MINOR="

for /f "tokens=1,2 delims=." %%A in ('%PYTHON_EXE% %PYTHON_ARGS% -c "import sys; print(str(sys.version_info.major) + chr(46) + str(sys.version_info.minor))"') do (
	set "PY_MAJOR=%%A"
	set "PY_MINOR=%%B"
)

if not defined PY_MAJOR (
	echo [ERROR] Could not determine the Python version.
	exit /b 1
)

echo [INFO] Using Python !PY_MAJOR!.!PY_MINOR!

if !PY_MAJOR! LSS 3 (
	echo [ERROR] Python 3.11 or newer is required.
	exit /b 1
)

if !PY_MAJOR! EQU 3 if !PY_MINOR! LSS 11 (
	echo [ERROR] Python 3.11 or newer is required.
	exit /b 1
)

exit /b 0

:EnsureVenv
set "VENV_CREATED=0"
if exist "%VENV_PYTHON%" (
	if exist "%VENV_DIR%\pyvenv.cfg" (
		findstr /C:"version = !PY_MAJOR!.!PY_MINOR!" "%VENV_DIR%\pyvenv.cfg" >nul 2>&1
		if errorlevel 1 (
			echo [INFO] Recreating virtual environment for Python !PY_MAJOR!.!PY_MINOR!...
			rmdir /s /q "%VENV_DIR%"
		)
	)
)

if not exist "%VENV_PYTHON%" (
	echo [INFO] Creating virtual environment...
	"%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%VENV_DIR%"
	if errorlevel 1 exit /b 1
	set "VENV_CREATED=1"
)

exit /b 0

:InstallDependencies
call :GetRequirementsHash || exit /b 1

set "CURRENT_REQ_HASH="
if exist "%REQ_STAMP%" (
	set /p CURRENT_REQ_HASH=<"%REQ_STAMP%"
)

if not "%VENV_CREATED%"=="1" if /i "%CURRENT_REQ_HASH%"=="%REQ_HASH%" (
	echo [INFO] Dependencies are up to date.
	goto :CheckDependencies
)

set "WRITE_REQ_STAMP=1"

echo [INFO] Upgrading pip tooling...
"%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

echo [INFO] Installing project dependencies...
"%VENV_PYTHON%" -m pip install --upgrade --upgrade-strategy only-if-needed -r "%REQ_FILE%"
if errorlevel 1 exit /b 1

:CheckDependencies

echo [INFO] Checking dependency health...
"%VENV_PYTHON%" -m pip check
if errorlevel 1 (
	echo [ERROR] Dependency conflicts were detected.
	exit /b 1
)

if defined WRITE_REQ_STAMP (
	>"%REQ_STAMP%" echo %REQ_HASH%
)

exit /b 0

:GetRequirementsHash
set "REQ_HASH="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -Path '%REQ_FILE%').Hash"`) do (
	set "REQ_HASH=%%H"
	goto :gotRequirementsHash
)

:gotRequirementsHash
if not defined REQ_HASH (
	echo [ERROR] Failed to calculate requirements hash.
	exit /b 1
)

exit /b 0

:InitializeDatabase
if not exist "%INIT_DB_FILE%" (
	echo [ERROR] Missing database init script: %INIT_DB_FILE%
	exit /b 1
)

if exist "%DB_FILE%" (
	echo [INFO] Database already initialized.
	exit /b 0
)

echo [INFO] Initializing database...
"%VENV_PYTHON%" "%INIT_DB_FILE%"
if errorlevel 1 exit /b 1

exit /b 0

:success
echo.
echo [DONE] BehaviourAI stopped.
endlocal
exit /b 0

:fail
echo.
echo [ERROR] BehaviourAI bootstrap failed.
endlocal
exit /b 1
