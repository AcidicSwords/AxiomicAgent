"""
Fix speaker extraction for Oprah-Harry-Meghan interview.
Speakers are embedded in text like "Oprah: ..." - extract them properly.
"""
import json
import re
from pathlib import Path

def extract_speaker(text):
    """Extract speaker from text if present in format 'Speaker: text'."""
    # Match pattern: Word(s) followed by colon at start
    match = re.match(r'^([A-Z][a-zA-Z\s]+?):\s*(.+)$', text.strip())
    if match:
        speaker = match.group(1).strip()
        content = match.group(2).strip()
        # Common speakers in this interview
        valid_speakers = ['Oprah', 'Meghan', 'Harry', 'Prince Harry', 'Meghan Markle']
        if speaker in valid_speakers or speaker.startswith('Oprah') or speaker.startswith('Meghan') or speaker.startswith('Harry'):
            return speaker, content
    return None, text

def fix_oprah_transcript():
    """Fix the Oprah interview speaker extraction."""
    input_path = Path(r"D:\AxiomicAgent\RAWDATA\ConversationParsed\Oprah with Prince Harry and Meghan Markle — Interview Transcript _ by Kate Shaw _ Medium_parsed.json")

    print("Loading Oprah transcript...")
    data = json.load(open(input_path, encoding='utf-8'))

    original_turns = data['turns']
    fixed_turns = []

    stats = {
        'total': len(original_turns),
        'extracted': 0,
        'narration': 0,
        'speakers': set()
    }

    print(f"Processing {len(original_turns)} turns...")

    for turn in original_turns:
        speaker, content = extract_speaker(turn['text'])

        if speaker:
            fixed_turns.append({
                'speaker': speaker,
                'text': content
            })
            stats['extracted'] += 1
            stats['speakers'].add(speaker)
        else:
            # Keep as narration
            fixed_turns.append({
                'speaker': 'NARRATION',
                'text': turn['text']
            })
            stats['narration'] += 1

    print(f"\nExtraction results:")
    print(f"  Total turns: {stats['total']}")
    print(f"  Extracted speakers: {stats['extracted']}")
    print(f"  Narration kept: {stats['narration']}")
    print(f"  Unique speakers: {sorted(stats['speakers'])}")

    # Update data
    data['turns'] = fixed_turns

    # Save fixed version
    output_path = input_path.parent / (input_path.stem + '_fixed.json')
    print(f"\nSaving fixed version to: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\n✓ Fixed transcript saved!")

    # Show sample
    print("\nSample dialogue turns:")
    dialogue = [t for t in fixed_turns if t['speaker'] not in ['NARRATION', 'NARRATOR']][:10]
    for i, turn in enumerate(dialogue):
        print(f"  {turn['speaker']}: {turn['text'][:60]}...")

    return output_path

if __name__ == "__main__":
    fix_oprah_transcript()
