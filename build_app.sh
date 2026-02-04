#!/bin/bash
# Build script for Video Resize Processor - macOS DMG package

set -e

echo "🎬 视频转9:16工具 - 打包脚本"
echo "=============================="

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ 错误: 未找到 ffmpeg"
    echo "请先安装 ffmpeg: brew install ffmpeg"
    exit 1
fi

if ! command -v ffprobe &> /dev/null; then
    echo "❌ 错误: 未找到 ffprobe"
    echo "请先安装 ffmpeg: brew install ffmpeg"
    exit 1
fi

echo "✓ 找到 ffmpeg"

# Copy ffmpeg binaries to current directory
echo "📦 复制 ffmpeg 到项目目录..."
FFMPEG_PATH=$(which ffmpeg)
FFPROBE_PATH=$(which ffprobe)

echo "  ffmpeg: $FFMPEG_PATH"
echo "  ffprobe: $FFPROBE_PATH"

cp -L "$FFMPEG_PATH" ./ffmpeg
cp -L "$FFPROBE_PATH" ./ffprobe
chmod +x ./ffmpeg ./ffprobe

echo "✓ 复制完成"

# Check if py2app is installed
if ! python3 -c "import py2app" 2>/dev/null; then
    echo "📥 安装 py2app..."
    pip3 install py2app
fi

# Clean previous builds
echo "🧹 清理旧构建..."
rm -rf build dist

# Build the app
echo "🔨 开始打包..."
python3 setup.py py2app

# Check if build succeeded
if [ -d "dist/视频转9:16工具.app" ]; then
    echo ""
    echo "✅ 打包成功!"
    echo ""
else
    echo "❌ 打包失败"
    rm -f ./ffmpeg ./ffprobe
    exit 1
fi

# Cleanup temp files
rm -f ./ffmpeg ./ffprobe

# Create DMG
echo ""
echo "📦 创建 DMG 安装包..."

# Create a temporary directory for DMG contents
TEMP_DIR="temp_dmg_$$"
mkdir -p "$TEMP_DIR"

# Copy app to temp directory
cp -R "dist/视频转9:16工具.app" "$TEMP_DIR/"

# Get app size
APP_SIZE=$(du -sh "dist/视频转9:16工具.app" | cut -f1)

# Create DMG
DMG_NAME="视频转9:16工具-${APP_SIZE}.dmg"
hdiutil create -srcfolder "$TEMP_DIR" -volname "视频转9:16工具" -format UDBZ "$DMG_NAME"

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "✅ 完成!"
echo ""
echo "📁 文件: $DMG_NAME"
echo "📦 大小: $(du -h "$DMG_NAME" | cut -f1)"
echo ""
echo "使用方法:"
echo "  1. 将 $DMG_NAME 发送给用户"
echo "  2. 用户双击挂载 DMG"
echo "  3. 将 '视频转9:16工具.app' 拖到 Applications 文件夹"
echo ""
echo "⚠️  注意: 首次运行可能需要在 系统偏好设置 > 安全性与隐私 中允许"
