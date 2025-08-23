import json
import os
from pathlib import Path

def analyze_voice_files():
    # Define paths
    json_path = Path('KuroTools v1.3/scripts&tables/t_voice.json')
    wav_dir = Path('kuro_mdl_tool/misc/voice/wav')

    # 1. Read filenames from t_voice.json
    print(f"Loading JSON from: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            voice_data = json.load(f)
        # Extract filenames from the nested structure
        json_filenames = {Path(item['filename']).stem for item in voice_data['data'][0]['data'] if 'filename' in item}
        print(f"Found {len(json_filenames)} unique filenames in {json_path.name}")
    except FileNotFoundError:
        print(f"Error: {json_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}.")
        return

    # 2. List .wav files from the directory
    print(f"Scanning for .wav files in: {wav_dir}")
    if not wav_dir.is_dir():
        print(f"Error: Directory {wav_dir} not found.")
        return
    
    wav_filenames = {p.stem for p in wav_dir.rglob('*.wav')}
    print(f"Found {len(wav_filenames)} .wav files in the directory.")

    # 3. Compare the two sets of filenames
    print("\n--- Analysis Report ---")
    wav_only = wav_filenames - json_filenames
    json_only = json_filenames - wav_filenames

    if not wav_only:
        print("\n[SUCCESS] All .wav files in the directory are present in t_voice.json.")
    else:
        print(f"\n[WARNING] Found {len(wav_only)} .wav files that are NOT in t_voice.json:")
        for filename in sorted(list(wav_only))[:20]: # Print a sample
            print(f"  - {filename}")
        if len(wav_only) > 20:
            print(f"  ... and {len(wav_only) - 20} more.")

    if not json_only:
        print("\n[SUCCESS] All filenames in t_voice.json correspond to a .wav file.")
    else:
        print(f"\n[WARNING] Found {len(json_only)} filenames in t_voice.json that do NOT have a matching .wav file:")
        for filename in sorted(list(json_only))[:20]: # Print a sample
            print(f"  - {filename}")
        if len(json_only) > 20:
            print(f"  ... and {len(json_only) - 20} more.")

if __name__ == "__main__":
    analyze_voice_files()
