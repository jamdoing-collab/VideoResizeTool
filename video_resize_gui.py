#!/usr/bin/env python3
"""
Video Resize Processor GUI - PyQt6 Version
A beautiful, user-friendly interface for video resizing.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QProgressBar, QMessageBox, QFrame, QScrollArea
)


def get_subprocess_kwargs():
    """Get subprocess kwargs to hide console window on Windows."""
    kwargs = {}
    if sys.platform == 'win32':
        # Hide console window on Windows
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    return kwargs
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QColor


def get_ffmpeg_path():
    """Get FFmpeg executable path (bundled or system)."""
    # Check if bundled in app
    if getattr(sys, 'frozen', False):
        # Running in a bundle
        bundle_dir = Path(sys.executable).parent
        if sys.platform == 'darwin':
            # macOS .app bundle
            ffmpeg_path = bundle_dir / '..' / 'Resources' / 'ffmpeg'
            ffprobe_path = bundle_dir / '..' / 'Resources' / 'ffprobe'
        else:
            ffmpeg_path = bundle_dir / 'ffmpeg'
            ffprobe_path = bundle_dir / 'ffprobe'
        
        if ffmpeg_path.exists():
            return str(ffmpeg_path), str(ffprobe_path)
    
    # Fallback to system FFmpeg
    return 'ffmpeg', 'ffprobe'


class VideoProcessor(QThread):
    """Worker thread for processing videos."""
    progress = pyqtSignal(str, int, int)  # filename, current, total
    file_progress = pyqtSignal(int)  # percentage 0-100
    finished_signal = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, video_files: List[str], output_dir: str):
        super().__init__()
        self.video_files = video_files
        self.output_dir = output_dir
        self.is_running = True
        self.ffmpeg_path, self.ffprobe_path = get_ffmpeg_path()
    
    def run(self):
        total = len(self.video_files)
        
        for idx, video_path in enumerate(self.video_files, 1):
            if not self.is_running:
                break
            
            filename = Path(video_path).name
            self.progress.emit(filename, idx, total)
            
            # Generate output path
            output_path = Path(self.output_dir) / filename
            
            # Process video using ffmpeg
            success = self._process_video(video_path, str(output_path))
            
            if not success:
                self.finished_signal.emit(False, f"处理失败: {filename}")
                return
        
        self.finished_signal.emit(True, f"成功处理 {total} 个视频")
    
    def _process_video(self, input_path: str, output_path: str) -> bool:
        """Process single video with ffmpeg."""
        try:
            # Get video info for correct scaling
            info = self._get_video_info(input_path)
            if not info:
                return False
            
            # Calculate dimensions
            raw_width, raw_height = info['width'], info['height']
            sar = info['sar']
            
            # Handle rotation
            if info['is_rotated'] and info['rotation'] in [-90, 270, 90, -270]:
                source_width, source_height = raw_height, raw_width
            else:
                source_width, source_height = raw_width, raw_height
            
            # Target dimensions
            if source_height > source_width:
                target_width, target_height = 1080, 1920
            else:
                target_width, target_height = 1920, 1080
            
            # Calculate scale and padding
            display_width = source_width * sar
            source_ratio = display_width / source_height
            target_ratio = target_width / target_height
            
            if source_ratio > target_ratio:
                scaled_width = target_width
                scaled_height = int(target_width / source_ratio)
                pad_left = 0
                pad_top = (target_height - scaled_height) // 2
            else:
                scaled_height = target_height
                scaled_width = int(target_height * source_ratio)
                pad_left = (target_width - scaled_width) // 2
                pad_top = 0
            
            # Build filter chain with correct scaling
            filter_complex = f"setsar=1,scale={scaled_width}:{scaled_height}:flags=fast_bilinear,pad={target_width}:{target_height}:{pad_left}:{pad_top}:black,setsar=1"
            
            cmd = [
                self.ffmpeg_path, '-y', '-i', input_path,
                '-vf', filter_complex,
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'copy',
                '-movflags', '+faststart',
                '-metadata', 'rotate=0',
                output_path
            ]
            
            # Run ffmpeg with progress parsing (hidden console on Windows)
            popen_kwargs = {'stderr': subprocess.PIPE, 'stdout': subprocess.DEVNULL,
                          'universal_newlines': True, 'encoding': 'utf-8', 'errors': 'replace'}
            if sys.platform == 'win32':
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(cmd, **popen_kwargs)
            
            # Get video duration for progress calculation
            duration = self._get_video_duration(input_path)
            
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                
                # Parse progress
                if duration > 0 and 'time=' in line:
                    time_str = self._parse_time(line)
                    if time_str:
                        progress = min(int((time_str / duration) * 100), 99)
                        self.file_progress.emit(progress)
            
            process.wait()
            self.file_progress.emit(100)
            
            return process.returncode == 0
            
        except Exception as e:
            print(f"Error processing video: {e}")
            return False
    
    def _get_video_info(self, video_path: str) -> Optional[dict]:
        """Get video dimensions and rotation info."""
        try:
            import json
            cmd = [
                self.ffprobe_path, '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,sample_aspect_ratio,side_data_list',
                '-of', 'json',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10, **get_subprocess_kwargs())
            if result.returncode != 0:
                return None
            
            data = json.loads(result.stdout)
            stream = data['streams'][0]
            
            # Parse SAR
            sar_str = stream.get('sample_aspect_ratio', '1:1')
            if sar_str and ':' in sar_str:
                sar_num, sar_den = sar_str.split(':')
                sar = float(sar_num) / float(sar_den)
            else:
                sar = 1.0
            
            # Check rotation
            rotation = 0
            for side in stream.get('side_data_list', []):
                if side.get('side_data_type') == 'Display Matrix':
                    rotation = side.get('rotation', 0)
                    break
            
            # Check frame-level if no stream-level rotation
            if rotation == 0:
                try:
                    frame_cmd = [
                        self.ffprobe_path, '-v', 'error', '-select_streams', 'v:0',
                        '-show_frames', '-read_intervals', '%+#1',
                        '-show_entries', 'frame=side_data_list',
                        '-of', 'json', video_path
                    ]
                    frame_result = subprocess.run(frame_cmd, capture_output=True, text=True, timeout=5, **get_subprocess_kwargs())
                    if frame_result.returncode == 0:
                        frame_data = json.loads(frame_result.stdout)
                        for frame in frame_data.get('frames', []):
                            for side in frame.get('side_data_list', []):
                                if side.get('side_data_type') in ['Display Matrix', '3x3 displaymatrix']:
                                    rotation = side.get('rotation', 0)
                                    if rotation != 0:
                                        break
                            if rotation != 0:
                                break
                except:
                    pass
            
            return {
                'width': int(stream['width']),
                'height': int(stream['height']),
                'sar': sar,
                'rotation': rotation,
                'is_rotated': rotation in [90, -90, 270, -270]
            }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            cmd = [
                self.ffprobe_path, '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10, **get_subprocess_kwargs())
            return float(result.stdout.strip()) if result.stdout else 0
        except:
            return 0
    
    def _parse_time(self, line: str) -> Optional[float]:
        """Parse time from ffmpeg output."""
        try:
            if 'time=' in line:
                time_part = line.split('time=')[1].split()[0]
                parts = time_part.split(':')
                if len(parts) == 3:
                    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        except:
            pass
        return None
    
    def stop(self):
        self.is_running = False


class DropArea(QFrame):
    """Custom drop area widget."""
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 48px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.text_label = QLabel("拖拽视频文件到此处")
        self.text_label.setStyleSheet("""
            font-size: 16px;
            color: #6c757d;
            margin-top: 10px;
        """)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.sub_label = QLabel("或点击选择文件")
        self.sub_label.setStyleSheet("""
            font-size: 13px;
            color: #adb5bd;
            margin-top: 5px;
        """)
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addWidget(self.sub_label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #e7f3ff;
                    border: 2px dashed #0066cc;
                    border-radius: 12px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(None)
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv', '.m4v')):
                files.append(path)
        if files:
            self.files_dropped.emit(files)
    
    def mousePressEvent(self, event):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择视频文件", "",
            "视频文件 (*.mp4 *.mov *.avi *.mkv *.m4v);;所有文件 (*.*)"
        )
        if files:
            self.files_dropped.emit(files)


class VideoResizeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_files = []
        self.processor = None
        self.setup_output_dir()
        self.setup_ui()
    
    def setup_output_dir(self):
        """Setup default output directory."""
        try:
            # Try to get Desktop path
            if sys.platform == 'win32':
                # Windows: use USERPROFILE or HOME
                home = Path(os.path.expanduser('~'))
            else:
                home = Path.home()
            
            desktop = home / "Desktop"
            
            # If Desktop doesn't exist, use home directory
            if not desktop.exists():
                desktop = home
            
            self.output_dir = desktop / "9x16_output"
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Fallback to temp directory
            import tempfile
            self.output_dir = Path(tempfile.gettempdir()) / "9x16_output"
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_ui(self):
        self.setWindowTitle("视频转 9:16 工具")
        self.setMinimumSize(600, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("🎬 视频转 9:16 工具")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #212529;
            margin-bottom: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("自动旋转并缩放视频到 9:16 竖屏格式")
        subtitle.setStyleSheet("font-size: 13px; color: #6c757d;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Drop area
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(self.add_files)
        layout.addWidget(self.drop_area)
        
        # File list section
        list_header = QHBoxLayout()
        self.file_count_label = QLabel("已添加的文件 (0)")
        self.file_count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #495057;")
        list_header.addWidget(self.file_count_label)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #dc3545;
                border: none;
                padding: 5px 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f8d7da;
                border-radius: 4px;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_files)
        self.clear_btn.setVisible(False)
        list_header.addStretch()
        list_header.addWidget(self.clear_btn)
        layout.addLayout(list_header)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                min-height: 150px;
            }
            QListWidget::item {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 10px;
                margin: 5px 0;
            }
            QListWidget::item:hover {
                background-color: #f1f3f5;
            }
        """)
        layout.addWidget(self.file_list)
        
        # Progress section
        self.progress_frame = QFrame()
        self.progress_frame.setStyleSheet("""
            QFrame {
                background-color: #e7f3ff;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        self.progress_frame.setVisible(False)
        
        progress_layout = QVBoxLayout(self.progress_frame)
        progress_layout.setSpacing(10)
        
        self.status_label = QLabel("准备处理...")
        self.status_label.setStyleSheet("font-size: 14px; color: #495057;")
        progress_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #dee2e6;
                height: 12px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #0066cc;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.file_progress_label = QLabel("")
        self.file_progress_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        self.file_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.file_progress_label)
        
        layout.addWidget(self.progress_frame)
        
        # Start button
        self.start_btn = QPushButton("开始处理")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #adb5bd;
            }
        """)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)
        
        # Output location
        output_layout = QHBoxLayout()
        self.output_label = QLabel(f"输出位置: {self.output_dir}")
        self.output_label.setStyleSheet("font-size: 12px; color: #6c757d;")
        self.output_label.setWordWrap(True)
        output_layout.addWidget(self.output_label, stretch=1)
        
        open_btn = QPushButton("打开文件夹")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0066cc;
                border: 1px solid #0066cc;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e7f3ff;
            }
        """)
        open_btn.clicked.connect(self.open_output_dir)
        output_layout.addWidget(open_btn)
        layout.addLayout(output_layout)
        
        # Spacer
        layout.addStretch()
    
    def add_files(self, files: List[str]):
        """Add video files to the list."""
        for file in files:
            if file not in self.video_files:
                self.video_files.append(file)
                item = QListWidgetItem(f"  📹 {Path(file).name}")
                item.setToolTip(file)
                self.file_list.addItem(item)
        
        self.update_ui()
    
    def clear_files(self):
        """Clear all files."""
        self.video_files.clear()
        self.file_list.clear()
        self.update_ui()
    
    def update_ui(self):
        """Update UI based on current state."""
        count = len(self.video_files)
        self.file_count_label.setText(f"已添加的文件 ({count})")
        self.clear_btn.setVisible(count > 0)
        self.start_btn.setEnabled(count > 0)
    
    def start_processing(self):
        """Start processing videos."""
        if not self.video_files:
            return
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.start_btn.setText("处理中...")
        self.drop_area.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.progress_frame.setVisible(True)
        
        # Start processor
        self.processor = VideoProcessor(self.video_files, str(self.output_dir))
        self.processor.progress.connect(self.on_progress)
        self.processor.file_progress.connect(self.on_file_progress)
        self.processor.finished_signal.connect(self.on_finished)
        self.processor.start()
    
    def on_progress(self, filename: str, current: int, total: int):
        """Update progress."""
        self.status_label.setText(f"正在处理: {filename} ({current}/{total})")
        self.file_progress_label.setText(f"总进度: {current}/{total}")
        
        # Calculate total progress
        total_progress = int(((current - 1) / total) * 100)
        self.progress_bar.setValue(total_progress)
    
    def on_file_progress(self, percentage: int):
        """Update file progress."""
        # Get current total progress
        current = self.progress_bar.value()
        # Add file progress portion
        self.progress_bar.setValue(min(current + percentage // len(self.video_files), 99))
    
    def on_finished(self, success: bool, message: str):
        """Handle completion."""
        self.progress_bar.setValue(100)
        
        if success:
            QMessageBox.information(self, "完成", message)
            self.open_output_dir()
        else:
            QMessageBox.critical(self, "错误", message)
        
        # Reset UI
        self.start_btn.setEnabled(True)
        self.start_btn.setText("开始处理")
        self.drop_area.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.progress_frame.setVisible(False)
        self.video_files.clear()
        self.file_list.clear()
        self.update_ui()
    
    def open_output_dir(self):
        """Open output directory."""
        if sys.platform == 'darwin':
            subprocess.run(['open', str(self.output_dir)])
        elif sys.platform == 'win32':
            subprocess.run(['explorer', str(self.output_dir)], **get_subprocess_kwargs())
        else:
            subprocess.run(['xdg-open', str(self.output_dir)])
    
    def closeEvent(self, event):
        """Handle window close."""
        if self.processor and self.processor.isRunning():
            self.processor.stop()
            self.processor.wait(2000)
        event.accept()


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        ffmpeg_path, _ = get_ffmpeg_path()
        subprocess.run([ffmpeg_path, '-version'], capture_output=True, check=True, **get_subprocess_kwargs())
        return True
    except:
        return False


def main():
    # Check ffmpeg
    if not check_ffmpeg():
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("错误")
        msg.setText("未检测到 FFmpeg")
        msg.setInformativeText("请先安装 FFmpeg:\nhttps://ffmpeg.org/download.html")
        msg.exec()
        sys.exit(1)
    
    # Run app
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = VideoResizeApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
