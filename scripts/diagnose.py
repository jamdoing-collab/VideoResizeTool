#!/usr/bin/env python3
"""
Comprehensive diagnostic script for video processing issues.

Usage:
    python3 diagnose.py <input_path>

Arguments:
    input_path: Path to the video file to diagnose

Example:
    python3 diagnose.py /path/to/video.mp4
"""

import os
import sys
import json
import subprocess
import argparse

def run_cmd(cmd):
    """Run command and return output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e}\nstderr: {e.stderr}"
    except FileNotFoundError:
        return "ERROR: Command not found"

def get_detailed_info(video_path):
    """Get comprehensive video information."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,bit_rate,r_frame_rate,codec_name,pix_fmt,sample_aspect_ratio,display_aspect_ratio,side_data_list',
        '-show_entries', 'format=duration,size,bit_rate,format_name',
        '-of', 'json',
        video_path
    ]
    result = run_cmd(cmd)
    if result.startswith("ERROR"):
        return None, result
    
    try:
        data = json.loads(result)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}\nRaw output: {result}"

def print_section(title):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")

def main():
    parser = argparse.ArgumentParser(
        description='Diagnose video processing issues and analyze video metadata'
    )
    parser.add_argument(
        'input_path',
        help='Path to the video file to diagnose'
    )
    
    args = parser.parse_args()
    
    input_path = args.input_path
    output_dir = os.path.join(os.path.dirname(input_path), "9x16_output")
    output_path = os.path.join(output_dir, os.path.basename(input_path))
    
    print_section("VIDEO PROCESSING DIAGNOSTIC")
    
    # Check file existence
    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"Input file: {input_path}")
    print(f"File size: {os.path.getsize(input_path)} bytes")
    
    # Get detailed video info
    print_section("1. VIDEO METADATA ANALYSIS")
    data, error = get_detailed_info(input_path)
    
    if error:
        print(f"❌ Failed to get video info: {error}")
        sys.exit(1)
    
    # Parse stream info
    if 'streams' in data and data['streams']:
        stream = data['streams'][0]
        
        raw_width = int(stream['width'])
        raw_height = int(stream['height'])
        sar_str = stream.get('sample_aspect_ratio', '1:1')
        dar_str = stream.get('display_aspect_ratio', 'N/A')
        codec = stream.get('codec_name', 'N/A')
        pix_fmt = stream.get('pix_fmt', 'N/A')
        fps_str = stream.get('r_frame_rate', 'N/A')
        
        # Parse SAR
        if ':' in sar_str:
            sar_num, sar_den = sar_str.split(':')
            sar = float(sar_num) / float(sar_den)
        else:
            sar = 1.0
        
        # Check for rotation
        rotation = 0
        rotation_found = False
        side_data = stream.get('side_data_list', [])
        for side in side_data:
            if side.get('side_data_type') == 'Display Matrix':
                rotation = side.get('rotation', 0)
                rotation_found = True
                break
        
        print(f"📐 Dimensions (storage): {raw_width}×{raw_height}")
        print(f"🔄 Rotation metadata: {rotation}° {'(found)' if rotation_found else '(none)'}")
        print(f"📏 SAR (Sample Aspect Ratio): {sar_str} = {sar:.3f}")
        print(f"📐 DAR (Display Aspect Ratio): {dar_str}")
        print(f"🎞️  Codec: {codec}")
        print(f"🎨 Pixel format: {pix_fmt}")
        print(f"⏱️  Frame rate: {fps_str}")
        
        # Calculate display dimensions
        display_width = raw_width * sar
        display_height = raw_height
        display_ratio = display_width / display_height
        
        print(f"\n📊 Display calculations:")
        print(f"  Display width = {raw_width} × {sar:.3f} = {display_width:.1f}")
        print(f"  Display height = {raw_height}")
        print(f"  Display aspect ratio = {display_width:.1f} / {display_height} = {display_ratio:.4f}")
    
    # Format info
    if 'format' in data:
        format_info = data['format']
        print(f"\n📦 Format: {format_info.get('format_name', 'N/A')}")
        print(f"⏱️  Duration: {format_info.get('duration', 'N/A')} seconds")
        print(f"💾 Size: {format_info.get('size', 'N/A')} bytes")
        print(f"📶 Bitrate: {format_info.get('bit_rate', 'N/A')} bps")
    
    # Simulate current processing logic
    print_section("2. CURRENT PROCESSING LOGIC SIMULATION")
    
    raw_width = int(stream['width'])
    raw_height = int(stream['height'])
    rotation = rotation  # from above
    sar = sar  # from above
    
    print(f"Input parameters:")
    print(f"  raw_width: {raw_width}")
    print(f"  raw_height: {raw_height}")
    print(f"  rotation: {rotation}°")
    print(f"  sar: {sar:.3f}")
    
    # Determine final rotation
    final_rotation = rotation % 360
    if final_rotation not in [0, 90, 180, 270]:
        final_rotation = round(final_rotation / 90) * 90 % 360
    
    print(f"\nStep 1: Determine final rotation = {final_rotation}°")
    
    # Calculate dimensions after rotation
    if final_rotation in [90, 270]:
        rotated_width = raw_height
        rotated_height = raw_width
        print(f"  Rotated 90/270°: dimensions swap")
        print(f"  rotated_width = raw_height = {raw_height}")
        print(f"  rotated_height = raw_width = {raw_width}")
    else:
        rotated_width = raw_width
        rotated_height = raw_height
        print(f"  No rotation: dimensions unchanged")
    
    # Calculate aspect ratio considering SAR
    rotated_ratio = (rotated_width * sar) / rotated_height
    target_width = 1080
    target_height = 1920
    target_ratio = target_width / target_height
    
    print(f"\nStep 2: Calculate aspect ratio with SAR")
    print(f"  rotated_width × sar = {rotated_width} × {sar:.3f} = {rotated_width * sar:.1f}")
    print(f"  rotated_ratio = {rotated_width * sar:.1f} / {rotated_height} = {rotated_ratio:.4f}")
    print(f"  target_ratio (9:16) = 1080 / 1920 = {target_ratio:.4f}")
    
    # Calculate display dimensions for scaling
    display_width = rotated_width * sar
    display_height = rotated_height
    
    print(f"\nStep 3: Calculate display dimensions for scaling")
    print(f"  display_width = {display_width:.1f}")
    print(f"  display_height = {display_height}")
    
    # Simulate calculate_scale_and_padding
    print_section("3. SCALE AND PADDING CALCULATION")
    
    current_ratio = display_width / display_height
    
    print(f"Current ratio (display): {current_ratio:.4f}")
    print(f"Target ratio (9:16): {target_ratio:.4f}")
    print(f"Comparison: current_ratio > target_ratio? {current_ratio > target_ratio}")
    
    if current_ratio > target_ratio:
        # Wider than 9:16 - fit to width
        scaled_width = target_width
        scaled_height = int(target_width / current_ratio)
        pad_left = 0
        pad_top = (target_height - scaled_height) // 2
        print(f"  → WIDER than 9:16 → Fit to width (1080)")
        print(f"  → Scale to: {scaled_width}×{scaled_height}")
        print(f"  → Add top/bottom padding: {pad_top}px")
    else:
        # Taller than 9:16 - fit to height
        scaled_height = target_height
        scaled_width = int(target_height * current_ratio)
        pad_left = (target_width - scaled_width) // 2
        pad_top = 0
        print(f"  → TALLER than 9:16 → Fit to height (1920)")
        print(f"  → Scale to: {scaled_width}×{scaled_height}")
        print(f"  → Add left/right padding: {pad_left}px")
    
    # Safety checks
    print(f"\nStep 4: Safety checks")
    
    if scaled_width > target_width:
        print(f"  ❌ scaled_width ({scaled_width}) > target_width ({target_width})")
        scale_factor = target_width / display_width
        scaled_width = target_width
        scaled_height = int(display_height * scale_factor)
        pad_left = 0
        pad_top = (target_height - scaled_height) // 2
        print(f"  → Recalculated: Scale to {scaled_width}×{scaled_height}")
        print(f"  → Padding: left={pad_left}, top={pad_top}")
    else:
        print(f"  ✓ scaled_width ({scaled_width}) ≤ target_width ({target_width})")
    
    if scaled_height > target_height:
        print(f"  ❌ scaled_height ({scaled_height}) > target_height ({target_height})")
        scale_factor = target_height / display_height
        scaled_height = target_height
        scaled_width = int(display_width * scale_factor)
        pad_top = 0
        pad_left = (target_width - scaled_width) // 2
        print(f"  → Recalculated: Scale to {scaled_width}×{scaled_height}")
        print(f"  → Padding: left={pad_left}, top={pad_top}")
    else:
        print(f"  ✓ scaled_height ({scaled_height}) ≤ target_height ({target_height})")
    
    print(f"\n🎯 FINAL CALCULATION:")
    print(f"  Scale to: {scaled_width}×{scaled_height}")
    print(f"  Pad to: {target_width}×{target_height}")
    print(f"  Padding: left={pad_left}, top={pad_top}")
    
    # Check existing output
    print_section("4. EXISTING OUTPUT ANALYSIS")
    
    if os.path.exists(output_path):
        print(f"✅ Output file exists: {output_path}")
        print(f"   Size: {os.path.getsize(output_path)} bytes")
        
        # Get output dimensions
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            output_path
        ]
        result = run_cmd(cmd)
        if not result.startswith("ERROR"):
            print(f"   Dimensions: {result}")
            
            if result == "1080x1920":
                print("   ✅ Output has correct target dimensions")
            else:
                print(f"   ❌ Output dimensions incorrect (expected 1080x1920)")
                
                # Try to understand why
                try:
                    w, h = map(int, result.split('x'))
                    actual_ratio = w / h
                    print(f"   📐 Actual ratio: {actual_ratio:.4f}")
                    print(f"   📐 Expected ratio: {current_ratio:.4f}")
                    
                    if abs(actual_ratio - current_ratio) > 0.01:
                        print(f"   ⚠️  Aspect ratio mismatch!")
                except:
                    pass
        else:
            print(f"   ❌ Could not get output dimensions: {result}")
    else:
        print(f"📭 No existing output found at: {output_path}")
        print(f"   Expected path: {output_path}")
    
    # Recommendations
    print_section("5. RECOMMENDATIONS")
    
    print("1. Run the processing script and share the FULL output:")
    print(f"   cd \"/Users/jam/Desktop/.codebuddy/skills/video-resize-processor/scripts\"")
    print(f"   python3 resize_video.py \"{input_path}\"")
    print()
    print("2. If still not working, try forcing rotation:")
    print(f"   python3 resize_video.py \"{input_path}\" --rotate 90")
    print()
    print("3. Check the actual visual result:")
    print(f"   Open the output file at: {output_path}")
    print(f"   Verify if content is stretched or correctly proportioned")
    print()
    print("4. Share the following information:")
    print("   - The complete log from running the script")
    print("   - The actual output dimensions (from media player)")
    print("   - Whether the video content looks correct or stretched")

if __name__ == '__main__':
    main()