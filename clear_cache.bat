@echo off
chcp 65001 >nul
echo ========================================
echo 清理服务器缓存
echo ========================================
echo.

echo [1/3] 清理Python缓存...
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo ✓ 已删除 __pycache__
)
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul
echo ✓ Python缓存已清理

echo.
echo [2/3] 清理Flask会话...
if exist flask_session (
    rmdir /s /q flask_session
    echo ✓ 已删除 flask_session
)

echo.
echo [3/3] 清理浏览器缓存提示...
echo ✓ 请在浏览器中按 Ctrl+Shift+Delete 清理缓存
echo   或使用 Ctrl+F5 强制刷新页面

echo.
echo ========================================
echo 缓存清理完成！
echo ========================================
echo.
echo 提示：
echo 1. 重启服务器: python server.py
echo 2. 浏览器强制刷新: Ctrl+F5
echo 3. 或清理浏览器缓存后重新访问
echo.
pause
