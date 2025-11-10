"""
Quick quality check for parsed conversation files.
"""
import json
from pathlib import Path

def main():
    parsed_dir = Path(r"D:\AxiomicAgent\RAWDATA\ConversationParsed")

    print("PARSED CONVERSATION FILES - QUALITY REPORT")
    print("=" * 100)
    print(f"{'File':<60} | {'Total':>5} | {'Non-Narr':>8} | {'Speakers':>8} | {'Speaker Names'}")
    print("=" * 100)

    for fpath in sorted(parsed_dir.glob("*.json")):
        try:
            data = json.load(open(fpath, encoding='utf-8'))
            turns = data.get('turns', [])

            speakers = set([t['speaker'] for t in turns])
            non_narr = [t for t in turns if t['speaker'] not in ['NARRATION', 'NARRATOR']]

            # Truncate speaker list for display
            speaker_names = ', '.join(sorted(speakers)[:4])
            if len(speakers) > 4:
                speaker_names += f", ... ({len(speakers)} total)"

            fname = fpath.name[:58]
            print(f"{fname:<60} | {len(turns):5} | {len(non_narr):8} | {len(speakers):8} | {speaker_names}")

        except Exception as e:
            print(f"{fpath.name:<60} | ERROR: {str(e)}")

    print("=" * 100)
    print("\nNOTES:")
    print("- Files with only NARRATION speaker may need re-parsing or have speaker names embedded in text")
    print("- Files with very few non-narration turns may be metadata-heavy")
    print("- Good files should have multiple speakers and high non-narration count")

if __name__ == "__main__":
    main()
