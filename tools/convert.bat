@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title PDF/A-3 -^> PDF/A-1 конвертер

echo ==================================================
echo   PDF/A-3 -^> PDF/A-1  (сложные случаи)
echo   ставит Python и зависимости при необходимости
echo ==================================================
echo.

REM ---------- 1. найти Python ----------
set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY ( where python >nul 2>&1 && set "PY=python" )

if not defined PY (
    echo Python не найден. Пробую установить...
    where winget >nul 2>&1
    if !errorlevel! == 0 (
        echo   - ставлю через winget...
        winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    ) else (
        echo   - winget нет, качаю установщик с python.org...
        set "PYURL=https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
        set "PYEXE=%TEMP%\python-setup.exe"
        curl -L -o "!PYEXE!" "!PYURL!"
        if not exist "!PYEXE!" ( echo Не удалось скачать Python. & pause & exit /b 1 )
        echo   - устанавливаю Python (тихо, в профиль пользователя)...
        "!PYEXE!" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
    )
    where py >nul 2>&1 && set "PY=py"
    if not defined PY ( where python >nul 2>&1 && set "PY=python" )
)

if not defined PY (
    echo.
    echo Python установлен, но ещё не виден в этом окне ^(не обновился PATH^).
    echo Закрой окно и запусти convert.bat ещё раз.
    pause
    exit /b 1
)

echo - Python:
%PY% --version
echo.

REM ---------- 2. зависимости ----------
echo - обновляю pip и ставлю pikepdf...
%PY% -m pip install --upgrade pip >nul 2>&1
%PY% -m pip install --upgrade pikepdf
if !errorlevel! neq 0 ( echo Не удалось установить pikepdf. & pause & exit /b 1 )
echo.

REM ---------- 3. сам скрипт ----------
set "SCRIPT=%~dp0pdfa_downgrade.py"
if not exist "%SCRIPT%" (
    echo - качаю pdfa_downgrade.py...
    curl -L -o "%SCRIPT%" https://raw.githubusercontent.com/FLEXIY0/PDFka/main/tools/pdfa_downgrade.py
    if not exist "%SCRIPT%" ( echo Не удалось скачать скрипт конвертации. & pause & exit /b 1 )
)

REM ---------- 4. файл для конвертации ----------
set "INPUT=%~1"
if "%INPUT%"=="" (
    set /p "INPUT=Перетащи PDF в это окно и нажми Enter: "
)
set "INPUT=%INPUT:"=%"
if not exist "%INPUT%" ( echo Файл не найден: "%INPUT%" & pause & exit /b 1 )

echo.
echo - конвертирую "%INPUT%" ...
echo.
%PY% "%SCRIPT%" "%INPUT%"

echo.
echo Готово. Перед сдачей в архив прогони результат через veraPDF.
pause
