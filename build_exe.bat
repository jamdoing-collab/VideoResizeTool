@echo off
chcp 65001 >nul
echo.
echo ========================================
echo     视频转9:16工具 - Windows 完整打包
echo ========================================
echo.

REM 检查 FFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 ffmpeg
    echo 请先安装 ffmpeg: winget install FFmpeg
    goto :eof
)

where ffprobe >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 ffprobe
    echo 请先安装 ffmpeg: winget install FFmpeg
    goto :eof
)

echo [✓] 找到 FFmpeg

REM 复制 FFmpeg 到项目目录
echo [📦] 复制 FFmpeg 二进制文件...
for /f "delims=" %%i in ('where ffmpeg') do copy /y "%%i" .\ffmpeg.exe >nul
for /f "delims=" %%i in ('where ffprobe') do copy /y "%%i" .\ffprobe.exe >nul
echo [✓] 复制完成

REM 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [📥] 安装 PyInstaller...
    pip install pyinstaller
)

REM 检查 NSIS（用于创建安装包）
where makensis >nul 2>&1
if errorlevel 1 (
    echo [📥] 安装 NSIS（用于创建安装包）...
    winget install -e --id NSIS.NSIS
)

REM 清理旧构建
echo [🧹] 清理旧构建...
rmdir /s /q build dist 2>nul

REM ========== 第一步：打包 exe ==========
echo.
echo [1/2] 🔨 打包 exe...
pyinstaller --clean video_resize_gui.spec

if not exist "dist\视频转9:16工具.exe" (
    echo [错误] exe 打包失败
    del /q ffmpeg.exe ffprobe.exe 2>nul
    goto :eof
)
echo [✓] exe 打包成功

REM 清理临时文件
del /q ffmpeg.exe ffprobe.exe 2>nul

REM ========== 第二步：创建安装包 ==========
echo.
echo [2/2] 📦 创建安装包...

if not exist "makensis.exe" (
    echo [⚠]  未安装 NSIS，跳过安装包创建
    echo [✓] 完成！
    echo.
    echo 📁 可执行文件: dist\视频转9:16工具.exe
    echo.
    echo 请安装 NSIS 后运行以下命令创建安装包:
    echo   makensis installer.nsi
    pause
    goto :eof
)

makensis installer.nsi

if exist "dist\视频转9:16工具-安装版.exe" (
    echo.
    echo [✓] 安装包创建成功！
    echo.
    echo ════════════════════════════════════════
    echo   ✅ 打包完成！
    echo ════════════════════════════════════════
    echo.
    echo 📦 可发送文件: dist\视频转9:16工具-安装版.exe
    echo 📦 文件大小: %~z1
    echo.
    echo 使用方法:
    echo   1. 将安装版 exe 发送给用户
    echo   2. 用户双击运行安装程序
    echo   3. 按提示完成安装即可使用
    echo.
) else (
    echo [⚠] 安装包创建失败，但 exe 已可用
    echo 📁 可执行文件: dist\视频转9:16工具.exe
)

echo [✓] 完成！
pause
