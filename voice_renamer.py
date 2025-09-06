import argparse
import pandas as pd
import os
import shutil
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description='Rename and copy voice files based on a match result CSV.')
    parser.add_argument('-f', '--file', default='match_result.csv',
                        help='Path to the match result CSV file (default: match_result.csv)')
    parser.add_argument('--remake-character-ids', nargs='+', type=int,
                        help='A list of character IDs to remake voices for.')
    parser.add_argument('--old-voice-wav', required=True,
                        help='Directory containing the old voice WAV files.')
    parser.add_argument('--output', required=True,
                        help='Output directory for the renamed voice files.')

    args = parser.parse_args()

    # Read the CSV file
    try:
        df = pd.read_csv(args.file)
    except FileNotFoundError:
        print(f"Error: The file {args.file} was not found.")
        return

    # Filter by character IDs if provided
    if args.remake_character_ids:
        df = df[df['RemakeVoiceCharacterId'].isin(args.remake_character_ids)]

    if df.empty:
        print("No matching voice files to process.")
        return

    # Process files
    for index, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing voice files"):
        old_voice_filename = row['OldVoiceFilename']
        if not str(old_voice_filename).lower().endswith('.wav'):
            old_voice_filename += '.wav'
        old_voice_path = os.path.join(args.old_voice_wav, old_voice_filename)

        if not os.path.exists(old_voice_path):
            print(f"Warning: Source file not found, skipping: {old_voice_path}")
            continue

        if args.remake_character_ids:
            output_dir = os.path.join(args.output, str(row['RemakeVoiceCharacterId']), 'wav')
        else:
            output_dir = os.path.join(args.output, 'all', 'wav')

        os.makedirs(output_dir, exist_ok=True)

        remake_voice_filename = row['RemakeVoiceFilename']
        if not str(remake_voice_filename).lower().endswith('.wav'):
            remake_voice_filename += '.wav'
        new_voice_path = os.path.join(output_dir, remake_voice_filename)

        shutil.copy2(old_voice_path, new_voice_path)

    print("\nVoice renaming and copying complete.")

if __name__ == '__main__':
    main()
