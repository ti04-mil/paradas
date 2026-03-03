@echo off
setlocal EnableExtensions

set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"
set "PARADAS_DB_PATH=\\server\TI\Temp\Paradas\Sistema\Paradas.db"
if not exist "%PARADAS_DB_PATH%" (
  set "PARADAS_DB_PATH=%BASE_DIR%Paradas.db"
)

set "PYTHON_EXE=%BASE_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
  if exist "C:\Program Files\Python313\python.exe" (
    set "PYTHON_EXE=C:\Program Files\Python313\python.exe"
  ) else (
    where py >nul 2>&1
    if not errorlevel 1 (
      set "PYTHON_EXE=py"
    ) else (
      where python >nul 2>&1
      if not errorlevel 1 set "PYTHON_EXE=python"
    )
  )
)
set "LOG_OUT=%BASE_DIR%run5000.out.log"
set "LOG_ERR=%BASE_DIR%run5000.err.log"

if "%PYTHON_EXE%"=="" (
  echo Python nao encontrado.
  pause
  exit /b 1
)

if not exist "%PARADAS_DB_PATH%" (
  echo Banco de dados nao encontrado:
  echo %PARADAS_DB_PATH%
  pause
  exit /b 1
)

if /I "%PYTHON_EXE%"=="py" (
  py -m pip show flask >nul 2>&1
  if errorlevel 1 (
    echo Flask nao encontrado no Python do servidor.
    echo Rode instalar_servidor.bat antes de usar este arquivo.
    pause
    exit /b 1
  )
) else if /I "%PYTHON_EXE%"=="python" (
  python -m pip show flask >nul 2>&1
  if errorlevel 1 (
    echo Flask nao encontrado no Python do servidor.
    echo Rode instalar_servidor.bat antes de usar este arquivo.
    pause
    exit /b 1
  )
) else (
  "%PYTHON_EXE%" -m pip show flask >nul 2>&1
  if errorlevel 1 (
    echo Flask nao encontrado no Python do servidor.
    echo Rode instalar_servidor.bat antes de usar este arquivo.
    pause
    exit /b 1
  )
)

echo Verificando sistema em http://127.0.0.1:5000/login ...
powershell -NoProfile -Command ^
  "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000/login' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"

if %ERRORLEVEL% EQU 0 (
  echo Sistema ja esta em execucao.
  exit /b 0
)

echo Sistema parado. Iniciando...
powershell -NoProfile -Command ^
  "$env:PARADAS_DB_PATH='%PARADAS_DB_PATH%'; Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList 'app.py' -WorkingDirectory '%BASE_DIR%' -RedirectStandardOutput '%LOG_OUT%' -RedirectStandardError '%LOG_ERR%'"

set "STARTED=0"
for /l %%i in (1,1,30) do (
  powershell -NoProfile -Command "Start-Sleep -Seconds 1"
  powershell -NoProfile -Command ^
    "try { $r = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:5000/login' -TimeoutSec 3; if ($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }"
  if not errorlevel 1 (
    set "STARTED=1"
    goto :AFTERCHECK
  )
)

:AFTERCHECK
if "%STARTED%"=="1" (
  echo Sistema iniciado com sucesso.
  exit /b 0
)

echo Falha ao iniciar o sistema.
echo.
echo Ultimas linhas de erro:
powershell -NoProfile -Command "if (Test-Path '%LOG_ERR%') { Get-Content '%LOG_ERR%' -Tail 25 } else { 'Sem log de erro.' }"
echo.
echo Ultimas linhas de saida:
powershell -NoProfile -Command "if (Test-Path '%LOG_OUT%') { Get-Content '%LOG_OUT%' -Tail 25 } else { 'Sem log de saida.' }"
echo.
echo Tente iniciar manualmente para validar:
echo %PYTHON_EXE% app.py
pause
exit /b 1
