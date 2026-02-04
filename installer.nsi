; 视频转9:16工具 - NSIS 安装脚本
; 使用方法: 在 Windows 上运行 build_installer.bat

!include "MUI2.nsh"

; ----------------------
; 基本信息
; ----------------------
Name "视频转9:16工具"
OutFile "dist\视频转9:16工具-安装版.exe"
InstallDir "$PROGRAMFILES\视频转9:16工具"
InstallDirRegKey HKLM "Software\视频转9:16工具" "InstallDir"

; ----------------------
; 版本信息
; ----------------------
VIProductVersion "1.0.0.0"
VIAddVersionKey "CompanyName" "Video Resize Processor"
VIAddVersionKey "FileDescription" "视频转9:16工具 - 一键将视频转换为9:16竖屏格式"
VIAddVersionKey "FileVersion" "1.0.0.0"
VIAddVersionKey "LegalCopyright" "© 2025 Video Resize Processor"
VIAddVersionKey "ProductName" "视频转9:16工具"

; ----------------------
; 界面设置
; ----------------------
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_NOAUTOCLOSE

; ----------------------
; 页面
; ----------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "SimplifiedChinese"

; ----------------------
; 安装逻辑
; ----------------------
Section "Install" SecMain
    SetOutPath "$INSTDIR"

    ; 复制所有文件
    File /r "dist\*.*"

    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\视频转9:16工具"
    CreateShortCut "$SMPROGRAMS\视频转9:16工具\视频转9:16工具.lnk" "$INSTDIR\视频转9:16工具.exe"

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\视频转9:16工具.lnk" "$INSTDIR\视频转9:16工具.exe"

    ; 注册卸载信息
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\视频转9:16工具" \
                     "DisplayName" "视频转9:16工具"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\视频转9:16工具" \
                     "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\视频转9:16工具" \
                     "InstallLocation" "$INSTDIR"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\视频转9:16工具" \
                      "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\视频转9:16工具" \
                      "NoRepair" 1

    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; 显示完成信息
    MessageBox MB_ICONINFORMATION|MB_OK \
        "安装完成！$\n$\n点击 '完成' 后可在开始菜单或桌面找到 '视频转9:16工具'$\n$\n提示：首次运行时可能会遇到 Windows SmartScreen 提示，点击 '更多信息' 然后选择 '仍要运行' 即可。"

SectionEnd

; ----------------------
; 卸载逻辑
; ----------------------
Section "Uninstall"

    ; 删除快捷方式
    Delete "$SMPROGRAMS\视频转9:16工具\视频转9:16工具.lnk"
    RMDir "$SMPROGRAMS\视频转9:16工具"
    Delete "$DESKTOP\视频转9:16工具.lnk"

    ; 删除安装目录
    Delete "$INSTDIR\*.*"
    RMDir "$INSTDIR"

    ; 删除注册表
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\视频转9:16工具"
    DeleteRegKey HKLM "Software\视频转9:16工具"

SectionEnd
