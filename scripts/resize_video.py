#!/usr/bin/env python3
"""
Video Resize Processor - Converts videos to 9:16 aspect ratio with black padding.

Usage:
    python3 resize_video.py <input_paths...> [--output-subdir <name>] [--codec <codec>]

Arguments:
    input_paths: One or more paths to video files or directories containing videos
    --output-subdir: (Optional) Name of output subdirectory (default: 9x16_output)
    --codec: (Optional) Video codec: h264 (default), hevc (H.265), av1 (smaller size)
    --crf: (Optional) Quality setting (18-35), lower is better quality (default: 23 for h264, 28 for hevc/av1)

Examples:
    python3 resize_video.py video.mp4
    python3 resize_video.py video1.mp4 video2.mp4 --codec hevc
    python3 resize_video.py /path/to/folder/ --codec av1 --crf 30
    python3 resize_video.py video.mp4 --output-subdir converted
"""

import os
import sys
import json
import subprocess
import argparse
import multiprocessing
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed


def get_video_info(video_path: str) -> Optional[dict]:
    """Get video dimensions, bitrate, fps, codec info using ffprobe."""
    try:
        # Get raw dimensions without autorotation
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,bit_rate,r_frame_rate,pix_fmt,sample_aspect_ratio,side_data_list',
            '-of', 'json',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        stream = data['streams'][0]
        
        # Parse frame rate (may be in format "30000/1001")
        fps_str = stream.get('r_frame_rate', '30/1')
        if '/' in fps_str:
            num, den = fps_str.split('/')
            fps = float(num) / float(den)
        else:
            fps = float(fps_str)
        
        # Parse SAR (Sample Aspect Ratio)
        sar_str = stream.get('sample_aspect_ratio', '1:1')
        if sar_str and ':' in sar_str:
            sar_num, sar_den = sar_str.split(':')
            sar = float(sar_num) / float(sar_den)
        else:
            sar = 1.0
        
        # Get raw dimensions
        raw_width = int(stream['width'])
        raw_height = int(stream['height'])
        
        # Check for rotation metadata
        rotation = 0
        for side in stream.get('side_data_list', []):
            if side.get('side_data_type') == 'Display Matrix':
                rotation = side.get('rotation', 0)
                break
        
        # If no stream-level rotation, check first frame
        if rotation == 0:
            try:
                frame_cmd = [
                    'ffprobe', '-v', 'error', '-select_streams', 'v:0',
                    '-show_frames', '-read_intervals', '%+#1',
                    '-show_entries', 'frame=side_data_list',
                    '-of', 'json', video_path
                ]
                frame_result = subprocess.run(frame_cmd, capture_output=True, text=True, timeout=5)
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
            except Exception:
                pass
        
        is_rotated = rotation in [90, -90, 270, -270]
        
        return {
            'width': raw_width,
            'height': raw_height,
            'is_rotated': is_rotated,
            'sar': sar,
            'rotation': rotation,
            'bitrate': int(stream.get('bit_rate', 0)) if stream.get('bit_rate') else 0,
            'fps': fps,
            'pix_fmt': stream.get('pix_fmt', 'yuv420p'),
        }
    except subprocess.CalledProcessError as e:
        print(f"Error getting info for {video_path}: {e}")
        if e.stderr:
            print(f"  ffprobe stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"Error getting info for {video_path}: {e}")
        return None


# Target dimensions
PORTRAIT_WIDTH, PORTRAIT_HEIGHT = 1080, 1920


def calculate_scale_and_padding(width: int, height: int, target_width: int, target_height: int) -> Tuple[int, int, int, int]:
    """
    Calculate scale dimensions and padding for target output dimensions.
    Returns: (scaled_width, scaled_height, pad_left, pad_top)
    """
    current_ratio = width / height
    target_ratio = target_width / target_height
    
    if current_ratio > target_ratio:
        # Input is WIDER than target - fit to width, pad top/bottom
        scaled_width = target_width
        scaled_height = int(target_width / current_ratio)
        pad_left = 0
        pad_top = (target_height - scaled_height) // 2
    else:
        # Input is TALLER than target - fit to height, pad left/right
        scaled_height = target_height
        scaled_width = int(target_height * current_ratio)
        pad_left = (target_width - scaled_width) // 2
        pad_top = 0
    
    return scaled_width, scaled_height, pad_left, pad_top


def process_video(input_path: str, output_path: str, quiet: bool = False, rotate: int = 0, codec: str = 'h264', crf: Optional[int] = None) -> Tuple[str, bool]:
    """
    Process a single video to 9:16 aspect ratio (1080x1920) with fast encoding.
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        quiet: If True, suppress print statements (for parallel processing)
        rotate: Rotation angle (0, 90, 180, 270) to apply before processing
        codec: Video codec ('h264', 'hevc', 'av1')
        crf: Quality setting (18-35), None for auto-select
    
    Returns:
        Tuple of (input_path, success_boolean)
    """
    if not quiet:
        print(f"Processing: {input_path}")
    
    # Get original video info (all parameters)
    info = get_video_info(input_path)
    if not info:
        return input_path, False
    
    raw_width, raw_height = info['width'], info['height']
    sar = info['sar']
    
    # Apply manual rotation if specified
    if rotate in [90, 270]:
        source_width, source_height = raw_height, raw_width
    elif rotate == 180:
        source_width, source_height = raw_width, raw_height
    elif info['is_rotated'] and info['rotation'] in [-90, 270, 90, -270]:
        # FFmpeg auto-rotates when -noautorotate is not used
        source_width, source_height = raw_height, raw_width
    else:
        source_width, source_height = raw_width, raw_height
    
    # Determine output orientation
    if source_height > source_width:
        target_width, target_height = PORTRAIT_WIDTH, PORTRAIT_HEIGHT
    else:
        target_width, target_height = 1920, 1080  # Landscape
    target_ratio = target_width / target_height
    
    source_ratio = (source_width * sar) / source_height
    
    if not quiet:
        print(f"  Source: {source_width}×{source_height}, SAR: {sar:.3f}")
        if rotate:
            print(f"  [Manual rotation: {rotate}°]")
        elif info['is_rotated']:
            print(f"  [Auto-rotation: {info['rotation']}°]")
        print(f"  Target: {target_width}×{target_height}")
        if info['bitrate'] > 0:
            print(f"  Bitrate: {info['bitrate'] // 1000} kbps")
    
    # Calculate scale and padding
    display_width = int(source_width * sar)
    scaled_width, scaled_height, pad_left, pad_top = calculate_scale_and_padding(
        display_width, source_height, target_width, target_height
    )
    
    if not quiet:
        mode = "fit width" if source_ratio > target_ratio else "fit height"
        print(f"  Scale: {scaled_width}×{scaled_height} → {target_width}×{target_height} ({mode})")
    
    # Build filter chain
    filter_complex = f"setsar=1,scale={scaled_width}:{scaled_height}:flags=fast_bilinear,pad={target_width}:{target_height}:{pad_left}:{pad_top}:black,setsar=1"
    
    # Configure codec-specific settings
    codec_settings = {
        'h264': {
            'encoder': 'libx264',
            'preset': 'veryfast',
            'tune': 'fastdecode',
            'profile': 'high',
            'level': '4.2',
            'bsf': 'h264_metadata=rotate=0',
            'default_crf': 23,
        },
        'hevc': {
            'encoder': 'libx265',
            'preset': 'fast',
            'tune': 'fastdecode',
            'profile': 'main',
            'level': None,
            'bsf': 'hevc_metadata=rotate=0',
            'default_crf': 28,
        },
        'av1': {
            'encoder': 'libsvtav1',
            'preset': '8',  # 0-13, higher is faster
            'tune': None,
            'profile': None,
            'level': None,
            'bsf': None,  # AV1 doesn't have rotation bsf
            'default_crf': 28,
        },
    }
    
    if codec not in codec_settings:
        codec = 'h264'
    
    settings = codec_settings[codec]
    crf_value = crf if crf is not None else settings['default_crf']
    
    cmd = [
        'ffmpeg', '-y', '-i', input_path,
        '-vf', filter_complex,
        '-c:v', settings['encoder'],
        '-preset', settings['preset'],
        '-pix_fmt', info['pix_fmt'],
        '-r', str(info['fps']),
        '-threads', '0',
        '-c:a', 'copy',
        '-movflags', '+faststart',
    ]
    
    # Add codec-specific options
    for key, value in [('tune', settings['tune']), ('profile:v', settings['profile']), 
                       ('level', settings['level']), ('bsf:v', settings['bsf'])]:
        if value:
            cmd.extend([f'-{key}', value])
    
    cmd.extend(['-crf', str(crf_value), '-metadata', 'rotate=0'])
    
    if codec == 'hevc':
        cmd.extend(['-tag:v', 'hvc1'])
    
    cmd.append(output_path)
    
    # Debug: print full command
    if not quiet:
        print(f"  FFmpeg command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Verify output dimensions
        verify_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            output_path
        ]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True)
        if verify_result.returncode == 0:
            dims = verify_result.stdout.strip()
            if not quiet:
                print(f"  Output verified: {dims} (should be 1080x1920)")
        
        if not quiet:
            orig_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            print(f"  ✓ Done - Original: {orig_size / 1024 / 1024:.1f}MB, Output: {output_size / 1024 / 1024:.1f}MB")
        
        return input_path, True
    except subprocess.CalledProcessError as e:
        if not quiet:
            print(f"  ✗ Error: {e}")
            if e.stderr:
                print(f"    ffmpeg error: {e.stderr}")
        return input_path, False


def process_video_worker(args_tuple) -> Tuple[str, bool]:
    """Worker function for parallel processing."""
    input_path, output_path, rotate, codec, crf = args_tuple
    return process_video(input_path, output_path, quiet=True, rotate=rotate, codec=codec, crf=crf)


def get_video_files(path: str) -> List[str]:
    """Get list of video files from path (file or directory)."""
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.flv', '.wmv'}
    
    if os.path.isfile(path):
        if Path(path).suffix.lower() in video_extensions:
            return [path]
        else:
            print(f"Warning: {path} is not a supported video file")
            return []
    
    elif os.path.isdir(path):
        video_files = []
        for root, _, files in os.walk(path):
            for file in files:
                if Path(file).suffix.lower() in video_extensions:
                    video_files.append(os.path.join(root, file))
        return video_files
    
    else:
        print(f"Error: {path} is not a valid file or directory")
        return []


def generate_output_path(input_path: str, output_subdir: str = "9x16_output") -> str:
    """
    Generate output file path in a subdirectory of the input video's location.
    Keeps original filename unchanged.
    
    Args:
        input_path: Path to the input video file
        output_subdir: Name of the subdirectory to create (default: 9x16_output)
    
    Returns:
        Full path for the output video file
    """
    input_path_obj = Path(input_path)
    
    # Get the directory containing the input video
    input_dir = input_path_obj.parent
    
    # Create output subdirectory in the same location as input video
    output_dir = input_dir / output_subdir
    output_dir.mkdir(exist_ok=True)
    
    # Keep original filename (including extension)
    output_name = input_path_obj.name
    
    return str(output_dir / output_name)


def main():
    parser = argparse.ArgumentParser(
        description='Convert videos to 9:16 aspect ratio with black padding while preserving all quality parameters'
    )
    parser.add_argument(
        'input_paths',
        nargs='+',
        help='Path(s) to video file(s) or directory/ies containing videos'
    )
    parser.add_argument(
        '--output-subdir',
        default='9x16_output',
        help='Name of the output subdirectory created in the input video location (default: 9x16_output)'
    )
    parser.add_argument(
        '--rotate',
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help='Rotate video by specified degrees (90, 180, 270) before processing. Use 90 to convert landscape to portrait'
    )
    parser.add_argument(
        '--codec',
        type=str,
        choices=['h264', 'hevc', 'av1'],
        default='h264',
        help='Video codec: h264 (default, best compatibility), hevc (H.265, smaller files), av1 (smallest files, slower)'
    )
    parser.add_argument(
        '--crf',
        type=int,
        default=None,
        help='Quality setting (18-35), lower is better quality. Default: 23 for h264, 28 for hevc/av1'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of parallel workers (default: auto-detect CPU cores)'
    )
    
    args = parser.parse_args()
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not in PATH")
        print("Please install ffmpeg: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # Collect video files from all input paths
    video_files = []
    for path in args.input_paths:
        video_files.extend(get_video_files(path))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_videos = []
    for v in video_files:
        if v not in seen:
            seen.add(v)
            unique_videos.append(v)
    video_files = unique_videos
    
    if not video_files:
        print("No video files found to process")
        sys.exit(1)
    
    print(f"Found {len(video_files)} video(s) to process\n")
    print(f"Output subdirectory: {args.output_subdir}")
    print(f"Codec: {args.codec}")
    if args.crf:
        print(f"CRF: {args.crf}")
    print()
    
    # Prepare video processing tasks
    video_tasks = []
    output_dirs = set()
    for video_path in video_files:
        output_path = generate_output_path(video_path, args.output_subdir)
        output_dirs.add(os.path.dirname(output_path))
        video_tasks.append((video_path, output_path, args.rotate, args.codec, args.crf))
    
    # Process videos
    success_count = 0
    failed_count = 0
    
    # Use parallel processing for multiple videos
    cpu_count = multiprocessing.cpu_count()
    max_workers = args.workers if args.workers else min(len(video_tasks), cpu_count)
    
    if len(video_tasks) > 1 and max_workers > 1:
        print(f"Using {max_workers} parallel workers ({cpu_count} CPU cores available)...\n")
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_video_worker, task): task for task in video_tasks}
            
            for future in as_completed(futures):
                input_path, success = future.result()
                if success:
                    success_count += 1
                    print(f"  ✓ Completed: {os.path.basename(input_path)}")
                else:
                    failed_count += 1
                    print(f"  ✗ Failed: {os.path.basename(input_path)}")
    else:
        # Single video - process directly with all parameters
        for video_path, output_path, rotate, codec, crf in video_tasks:
            _, success = process_video(video_path, output_path, quiet=False, rotate=rotate, codec=codec, crf=crf)
            if success:
                success_count += 1
            else:
                failed_count += 1
            print()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Processing complete!")
    print(f"  Success: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Output location(s):")
    for output_dir in sorted(output_dirs):
        print(f"    - {output_dir}")


if __name__ == '__main__':
    main()
