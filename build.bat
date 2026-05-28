@echo off
chcp 65001 >nul
echo ==========================================
echo   智能剪贴板翻译器 - PyInstaller 打包脚本
echo ==========================================
echo.

REM 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 依赖安装失败！
    pause
    exit /b 1
)

REM 清理旧的构建
echo [2/3] 清理旧构建...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM PyInstaller 打包
echo [3/3] 开始打包...
pyinstaller --noconsole --onefile --name "智能剪贴板翻译器" ^
  --hidden-import customtkinter ^
  --hidden-import win32clipboard ^
  --hidden-import win32gui ^
  --hidden-import win32api ^
  --add-data "config_manager.py;." ^
  --add-data "language_detector.py;." ^
  --add-data "translator.py;." ^
  --add-data "clipboard_monitor.py;." ^
  --add-data "db.py;." ^
  --add-data "toast.py;." ^
  main.py

if %errorlevel% neq 0 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   打包完成！
echo   输出文件: dist\智能剪贴板翻译器.exe
echo ==========================================
pause
