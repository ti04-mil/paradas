@echo off
setlocal

set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_EXE%" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist "%ISCC_EXE%" (
  echo Inno Setup nao encontrado.
  echo Instale o Inno Setup 6 e execute novamente este arquivo.
  pause
  exit /b 1
)

echo Gerando instalador...
"%ISCC_EXE%" "%BASE_DIR%instalador_sistema.iss"
if errorlevel 1 (
  echo Falha ao gerar o instalador.
  pause
  exit /b 1
)

echo Instalador gerado com sucesso:
echo "%BASE_DIR%Instalador_Sistema_Paradas.exe"
pause
exit /b 0

