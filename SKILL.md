---
name: video-resize-processor
description: A skill for resizing videos to 9:16 aspect ratio with black padding (letterboxing) for TikTok, Instagram Reels, and YouTube Shorts. Supports single or batch processing while preserving original quality.
---

# Video Resize Processor

A skill for converting videos to 9:16 aspect ratio with automatic black padding.

## Purpose

This skill provides a reliable way to convert videos of any aspect ratio to the 9:16 vertical format at a fixed resolution of 1080×1920 pixels. It automatically calculates the required scaling and padding to maintain the original video content without distortion.

## When to Use

Use this skill when:
- Converting landscape or square videos to 9:16 vertical format
- Preparing videos for TikTok, Instagram Reels, or YouTube Shorts
- Batch processing multiple videos with the same aspect ratio requirements
- Maintaining original video quality while changing dimensions

## Usage Workflow

### Step 1: Identify Input Videos

Determine the video file(s) to process:
- Single video: `/path/to/video.mp4`
- Multiple videos: List of file paths or directory containing videos

### Step 2: Execute Video Processing

Run the processing script with the appropriate parameters:

```bash
python3 scripts/resize_video.py <input_path> [--output-subdir <name>]
```

Parameters:
- `input_path`: Path to a video file or directory containing videos
- `--output-subdir`: (Optional) Name of the subdirectory created in the input video's location. Defaults to `9x16_output`

### Step 3: Review Output

Processed videos are saved in a subdirectory next to the original video:
- **Location**: `{video_parent_dir}/9x16_output/`
- **Filename**: Same as original (unchanged)

Example:
- Input: `/Users/videos/myvideo.mp4`
- Output: `/Users/videos/9x16_output/myvideo.mp4`

## For Claude: How to Process User Requests

When a user asks to resize video(s) to 9:16 format:

1. **Check Prerequisites**: Verify ffmpeg is installed by running `ffmpeg -version`

2. **Execute Processing**: Use the resize_video.py script with the provided video path:
   ```bash
   python3 /Users/jam/Desktop/.codebuddy/skills/video-resize-processor/scripts/resize_video.py <video_path>
   ```

3. **Handle Multiple Videos**: If user provides multiple videos or a directory, the script will process all supported video files automatically.

4. **Report Results**: After processing, inform the user:
   - How many videos were processed
   - Output file locations
   - Any errors that occurred

### Example User Requests and Responses

**User**: "帮我把这个视频转成 9:16 比例"
**Action**: Execute script with provided video path. Output will be in `9x16_output/` subdirectory with same filename.

**User**: "批量处理这个文件夹里的所有视频，改成竖屏 9:16"
**Action**: Execute script with directory path. Each video will be processed and saved in its respective `9x16_output/` subdirectory.

**User**: "我有一个 1:1 的正方形视频，想变成 9:16 发抖音"
**Action**: Execute script and explain that black padding will be added to top/bottom, with output in `9x16_output/` folder next to the original.

## Technical Details

### Supported Formats

Input formats: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`
Output format: `.mp4` (H.264 codec)

### Processing Logic

1. **Auto-detect video rotation** from metadata (common in mobile videos)
   - Automatically swaps dimensions for 90°/270° rotated videos
   - Uses visual dimensions for correct aspect ratio calculation
2. Calculate target 9:16 dimensions:
   - If video is wider than 9:16: Add black bars to top and bottom
   - If video is narrower than 9:16: Add black bars to left and right
3. Use ffmpeg with **fast_bilinear scaling** for quick resizing
4. **Parallel processing** for multiple videos (uses all CPU cores)
5. **Fast encoding preset** (`veryfast`) for speed optimization
6. **Preserve ALL original video parameters:**
   - Frame rate (FPS)
   - Bitrate
   - Pixel format (yuv420p, etc.)
   - Color space, range, transfer, primaries
   - Audio stream (direct copy, no re-encoding)

### Example Transformations

| Original Ratio | Original Size | Output Size | Scaling & Padding |
|----------------|---------------|-------------|-------------------|
| 1:1 (Square) | 1080×1080 | 1080×1920 | Scale to 1080×1080, add 420px black bars (top/bottom) |
| 16:9 (Landscape) | 1920×1080 | 1080×1920 | Scale to 1080×607, add 656px black bars (top/bottom) |
| 4:3 | 1440×1080 | 1080×1920 | Scale to 1080×810, add 555px black bars (top/bottom) |
| 4:5 (Portrait) | 1080×1350 | 1080×1920 | Scale to 1080×1350, add 285px black bars (top/bottom) |

## Requirements

- ffmpeg must be installed and available in PATH
- Python 3.7+
- Sufficient disk space for output files
