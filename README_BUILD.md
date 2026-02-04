# 视频转 9:16 工具 - 打包指南

## 完整安装包（包含 FFmpeg）

---

## GitHub Actions 自动打包（推荐）

无需本地环境，一键打包 Windows + macOS 应用！

### 使用方法

**1. 推送代码到 GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
# 在 GitHub 创建仓库后
git remote add origin https://github.com/你的用户名/video-resize-processor.git
git push -u origin main
```

**2. 创建 Release 触发自动打包**

进入 GitHub 仓库页面：
1. 点击 **Releases** → **Draft a new release**
2. 填写版本号（如 `v1.0.0`）
3. 点击 **Publish release**

**3. 下载打包好的文件**

GitHub Actions 会自动构建，完成后：
- **Windows**: 下载 `Windows/视频转9:16工具.exe`
- **macOS**: 下载 `macOS/视频转9:16工具.dmg` 或 `.app`

---

## 本地打包

### macOS 打包步骤

```bash
# 1. 进入项目目录
cd video-resize-processor

# 2. 运行打包脚本
./build_app.sh
```

打包完成后，会生成 DMG 文件，可**直接发送给用户**。

### macOS 打包要求

- macOS 系统
- Python 3.9+
- FFmpeg 已安装 (`brew install ffmpeg`)
- 约 150MB 磁盘空间

### macOS 分享方式

**一键打包为 DMG：**
```bash
./build_app.sh
```
生成 `视频转9:16工具-xxx.dmg`，双击挂载后将 `.app` 拖到 Applications 即可。

### Windows 打包步骤

```bash
# 1. 进入项目目录
cd video-resize-processor

# 2. 运行打包脚本
build_exe.bat
```

打包完成后，会生成 `视频转9:16工具-安装版.exe`，可**直接发送给用户**。

### Windows 打包要求

- Windows 10/11
- Python 3.9+
- FFmpeg 已安装 (`winget install FFmpeg`)
- NSIS（打包脚本会自动安装）
- 约 200MB 磁盘空间

### Windows 分享方式

**一键打包为安装程序：**
```bash
build_exe.bat
```
生成 `视频转9:16工具-安装版.exe`，双击运行按提示安装即可。

打包完成后，会在 `dist/` 目录生成 `视频转9:16工具.app`，可以直接分享给其他人使用。

### 打包要求

- macOS 系统
- Python 3.9+
- FFmpeg 已安装 (`brew install ffmpeg`)
- 约 150MB 磁盘空间

### 分享方式

1. **直接发送 .app 文件**
   - 将 `视频转9:16工具.app` 压缩为 zip
   - 发送给对方
   - 对方解压后双击运行

2. **制作 DMG 安装包**（更专业）
   ```bash
   # 创建 DMG
   hdiutil create -srcfolder "dist/视频转9:16工具.app" -volname "视频转9:16工具" "视频转9:16工具.dmg"
   ```

### 首次运行注意事项

由于应用未经过 Apple 公证，首次运行时可能会出现安全提示：

1. 前往 **系统偏好设置 > 安全性与隐私**
2. 点击下方的 **"仍要打开"**
3. 之后即可正常使用

### Windows 打包步骤

```bash
# 1. 进入项目目录
cd video-resize-processor

# 2. 运行打包脚本
build_exe.bat
```

打包完成后，会在 `dist/` 目录生成 `视频转9:16工具.exe`，可以直接分享。

### Windows 打包要求

- Windows 10/11
- Python 3.9+
- FFmpeg 已安装 (`winget install FFmpeg`)
- 约 200MB 磁盘空间

### Windows 分享方式

1. **直接发送 exe 文件**
   - 将 `dist/` 文件夹压缩为 zip
   - 发送给对方
   - 对方解压后双击运行

2. **制作安装包**（更专业，可选）
   - 使用 NSIS 或 Inno Setup
   ```bash
   # 安装 Inno Setup
   winget install JRSoftware.InnoSetup

   # 使用脚本创建安装包
   iscc installer.iss
   ```

### 首次运行注意事项

Windows 可能会出现 SmartScreen 筛选器警告：

1. 点击 **"更多信息"**
2. 点击 **"仍要运行"** 或 **"运行"**
3. 之后即可正常使用

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `video_resize_gui.py` | GUI 主程序 |
| `scripts/resize_video.py` | 命令行版本 |
| `setup.py` | macOS 打包配置 |
| `build_app.sh` | macOS 一键打包脚本（生成 DMG） |
| `video_resize_gui.spec` | Windows PyInstaller 配置 |
| `build_exe.bat` | Windows 一键打包脚本（生成安装包） |
| `installer.nsi` | Windows NSIS 安装脚本 |

### 功能特性

- ✅ 拖拽添加视频
- ✅ 批量处理
- ✅ 自动旋转检测
- ✅ 保持比例 + 黑边填充
- ✅ 实时进度显示
- ✅ 无需额外安装 FFmpeg
- ✅ 支持 macOS 和 Windows
