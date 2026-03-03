@echo off
setlocal EnableExtensions

set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

set "PYTHON_GLOBAL=C:\Program Files\Python313\python.exe"
set "PYTHON_CMD="
set "PYTHON_INSTALL_DIR=C:\Program Files\Python313"

if exist "%PYTHON_GLOBAL%" (
  set "PYTHON_CMD=%PYTHON_GLOBAL%"
  goto :PY_READY
)

where py >nul 2>&1
if not errorlevel 1 set "PYTHON_CMD=py"
if "%PYTHON_CMD%"=="" (
  where python >nul 2>&1
  if not errorlevel 1 set "PYTHON_CMD=python"
)

if "%PYTHON_CMD%"=="" (
  echo Python nao encontrado. Tentando instalar Python 3.13...
  where winget >nul 2>&1
  if errorlevel 1 (
    echo Winget nao encontrado neste servidor.
    echo Instale manualmente Python 3.13 em: %PYTHON_INSTALL_DIR%
    pause
    exit /b 1
  )

  echo Solicitando instalacao (pode pedir permissao de administrador)...
  winget install -e --id Python.Python.3.13 --scope machine --location "%PYTHON_INSTALL_DIR%" --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo Falha na instalacao automatica do Python.
    echo Instale manualmente Python 3.13 em: %PYTHON_INSTALL_DIR%
    pause
    exit /b 1
  )

  if exist "%PYTHON_GLOBAL%" (
    set "PYTHON_CMD=%PYTHON_GLOBAL%"
  ) else (
    where py >nul 2>&1
    if not errorlevel 1 set "PYTHON_CMD=py"
    if "%PYTHON_CMD%"=="" (
      where python >nul 2>&1
      if not errorlevel 1 set "PYTHON_CMD=python"
    )
  )
)

if "%PYTHON_CMD%"=="" (
  echo Python nao encontrado.
  echo Instale Python 3.13 e execute novamente este arquivo.
  pause
  exit /b 1
)

:PY_READY
echo Usando Python: %PYTHON_CMD%
echo Criando ambiente virtual...
"%PYTHON_CMD%" -m venv .venv
if errorlevel 1 (
  echo Falha ao criar .venv
  pause
  exit /b 1
)

echo Atualizando pip...
".\.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
  echo Falha ao atualizar pip.
  pause
  exit /b 1
)

echo Instalando dependencias...
".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias.
  pause
  exit /b 1
)

echo.
echo Instalacao concluida com sucesso.
echo Execute monitorar_app.bat para iniciar/verificar o sistema.
pause
exit /b 0
