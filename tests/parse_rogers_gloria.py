"""
Parse Rogers-Gloria transcript into proper turn-by-turn format.

The JSON has the entire session in one text block with embedded turn markers (T1, C2, T2, C3...).
We need to split it into individual turns.
"""

import json
import re

def parse_rogers_transcript(text):
    """
    Parse Rogers-Gloria transcript with T/C turn markers.

    Format in text:
    T1 (Rogers stands...) Good morning...
    C2 Yes, I am.
    T2 Won't you have a chair?...
    """
    turns = []

    # Pattern: T or C followed by number, then text until next marker
    # Use lookahead to split but keep markers
    pattern = r'(?=[TC]\d+)'

    segments = re.split(pattern, text)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        # Extract turn marker (T12 or C5)
        match = re.match(r'^([TC])(\d+)\s+(.+)', segment, re.DOTALL)
        if not match:
            continue

        role_marker, turn_num, text_content = match.groups()

        # Map T/C to speaker names
        speaker = "THERAPIST" if role_marker == 'T' else "CLIENT"

        # Clean up text
        text_content = text_content.strip()

        # Remove stage directions in parentheses at start
        text_content = re.sub(r'^\([^)]+\)\s*', '', text_content)

        # Remove page number references
        text_content = re.sub(r'Rogers\' Transcripts.*?page \d+', '', text_content)

        # Skip very short turns (likely artifacts)
        if len(text_content) < 10:
            continue

        turns.append({
            "speaker": speaker,
            "turn_number": int(turn_num),
            "text": text_content.strip()
        })

    return turns


def main():
    # Load original
    with open('D:\\AxiomicAgent\\reports\\transciption rogers- Gloria.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find the main transcript block (should be in turn 43 based on structure)
    main_text = None
    for turn in data['transcript']:
        if 'T1' in turn['text'] and 'C2' in turn['text']:
            main_text = turn['text']
            break

    if not main_text:
        print("[!] Could not find main transcript block")
        return

    # Parse into turns
    turns = parse_rogers_transcript(main_text)

    print(f"Parsed {len(turns)} turns")
    print("\nFirst 5 turns:")
    for i, turn in enumerate(turns[:5]):
        print(f"\nTurn {i+1} ({turn['speaker']}, #{turn['turn_number']}):")
        print(f"  {turn['text'][:100]}...")

    # Create cleaned version
    output = {
        "source": data.get('source_file', 'unknown'),
        "title": "Carl Rogers Therapy Session with Gloria",
        "context": "Client-centered therapy demonstration, 1965",
        "actors": ["THERAPIST (Carl Rogers)", "CLIENT (Gloria)"],
        "turns": turns
    }

    # Save
    outfile = 'D:\\AxiomicAgent\\reports\\rogers_gloria_parsed.json'
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"\n[+] Saved parsed transcript to {outfile}")
    print(f"    Total turns: {len(turns)}")
    print(f"    Therapist turns: {sum(1 for t in turns if t['speaker'] == 'THERAPIST')}")
    print(f"    Client turns: {sum(1 for t in turns if t['speaker'] == 'CLIENT')}")


if __name__ == "__main__":
    main()
