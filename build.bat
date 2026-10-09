@echo off
chcp 65001 >nul
setlocal

REM ==== Переходим в папку проекта ====
cd /d "%~dp0"

REM ==== Проверка Python ====
where python >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден в PATH.
    pause
    exit /b 1
)

REM ==== Проверка PyInstaller ====
python -c "import PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] PyInstaller не установлен. Установите: pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Сборка Webber
echo ============================================================
echo.

REM ==== Очистка прошлых сборок ====
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Webber.spec del /q Webber.spec

REM ==== Сборка ====
python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --name Webber ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --collect-all qtawesome ^
    --collect-all PyQt6.QtWebEngineCore ^
    --collect-all PyQt6.QtWebEngineWidgets ^
    --hidden-import PyQt6.QtWebEngineCore ^
    --hidden-import PyQt6.QtWebEngineWidgets ^
    --hidden-import PyQt6.QtWebChannel ^
    --hidden-import PyQt6.QtNetwork ^
    --hidden-import PyQt6.QtPrintSupport ^
    --hidden-import PyQt6.QtQml ^
    --hidden-import PyQt6.QtQuick ^
    --hidden-import PyQt6.QtQuickWidgets ^
    --hidden-import PyQt6.QtSvg ^
    --hidden-import PyQt6.QtSvgWidgets ^
    --exclude-module PyQt5 ^
    --exclude-module PySide6 ^
    --exclude-module tkinter ^
    --exclude-module matplotlib ^
    --exclude-module torch ^
    --exclude-module torchvision ^
    --exclude-module numpy ^
    --exclude-module scipy ^
    --exclude-module cv2 ^
    --exclude-module transformers ^
    --exclude-module numba ^
    --exclude-module llvmlite ^
    main.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Сборка завершилась с ошибкой.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Готово!
echo   Папка: %cd%\dist\Webber
echo   Запуск: dist\Webber\Webber.exe
echo ============================================================
echo.

REM ==== Открываем папку с результатом ====
if exist "dist\Webber" explorer "dist\Webber"

endlocal
pause