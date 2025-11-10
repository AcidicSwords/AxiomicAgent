"""Analyze current state of combined reports."""
import json
from pathlib import Path

def main():
    combined_path = Path(r"D:\AxiomicAgent\reports\comprehensive\combined.json")
    data = json.load(open(combined_path))

    print("="*80)
    print("CURRENT COMBINED.JSON ANALYSIS")
    print("="*80)

    # Curriculum
    curr = data['curriculum']['summary']
    print(f"\nCURRICULUM: {len(curr)} courses")
    print(f"  Quality range: {min(c['avg_q'] for c in curr):.3f} - {max(c['avg_q'] for c in curr):.3f}")
    print(f"  Drift range: {min(c['avg_ted'] for c in curr):.3f} - {max(c['avg_ted'] for c in curr):.3f}")
    print(f"  Steps range: {min(c['steps'] for c in curr)} - {max(c['steps'] for c in curr)}")

    # Conversations
    conv = data['conversation']['summary']
    print(f"\nCONVERSATIONS: {len(conv)} transcripts")
    print(f"  Quality range: {min(c['avg_q'] for c in conv):.3f} - {max(c['avg_q'] for c in conv):.3f}")
    print(f"  Drift range: {min(c['avg_ted'] for c in conv):.3f} - {max(c['avg_ted'] for c in conv):.3f}")
    print(f"  Steps range: {min(c['steps'] for c in conv)} - {max(c['steps'] for c in conv)}")

    print("\n" + "="*80)
    print("KEY OBSERVATIONS")
    print("="*80)

    # Compare parsed vs unparsed
    parsed = [c for c in conv if '_parsed' in c['course']]
    unparsed = [c for c in conv if '_parsed' not in c['course']]

    print(f"\nParsed versions: {len(parsed)}")
    print(f"Unparsed versions: {len(unparsed)}")

    if parsed and unparsed:
        avg_q_parsed = sum(c['avg_q'] for c in parsed) / len(parsed)
        avg_q_unparsed = sum(c['avg_q'] for c in unparsed) / len(unparsed)

        avg_ted_parsed = sum(c['avg_ted'] for c in parsed) / len(parsed)
        avg_ted_unparsed = sum(c['avg_ted'] for c in unparsed) / len(unparsed)

        avg_steps_parsed = sum(c['steps'] for c in parsed) / len(parsed)
        avg_steps_unparsed = sum(c['steps'] for c in unparsed) / len(unparsed)

        print(f"\nPARSED vs UNPARSED comparison:")
        print(f"  Quality:   parsed={avg_q_parsed:.3f}, unparsed={avg_q_unparsed:.3f}")
        print(f"  Drift:     parsed={avg_ted_parsed:.3f}, unparsed={avg_ted_unparsed:.3f}")
        print(f"  Steps:     parsed={avg_steps_parsed:.0f}, unparsed={avg_steps_unparsed:.0f}")

        if avg_q_parsed > avg_q_unparsed:
            print(f"  -> Parsed versions have HIGHER quality (+{avg_q_parsed - avg_q_unparsed:.3f})")
        else:
            print(f"  -> Parsed versions have LOWER quality ({avg_q_parsed - avg_q_unparsed:.3f})")

        if avg_steps_parsed > avg_steps_unparsed:
            print(f"  -> Parsed versions have MORE steps ({avg_steps_parsed/avg_steps_unparsed:.1f}x)")
        else:
            print(f"  -> Parsed versions have FEWER steps ({avg_steps_parsed/avg_steps_unparsed:.1f}x)")

    # Check Oprah specifically
    print("\n" + "="*80)
    print("OPRAH TRANSCRIPT STATUS")
    print("="*80)

    oprah_entries = [c for c in conv if 'oprah' in c['course'].lower() and 'harry' in c['course'].lower()]
    for entry in oprah_entries:
        print(f"\n{entry['course']}")
        print(f"  avg_q: {entry['avg_q']:.3f}")
        print(f"  avg_ted: {entry['avg_ted']:.3f}")
        print(f"  steps: {entry['steps']}")

    # Compare to earlier data
    print("\n" + "="*80)
    print("COMPARISON TO EARLIER ANALYSIS")
    print("="*80)

    print("\nEarlier (from my first analysis):")
    print("  AS13_TEC_parsed: q=0.471, ted=0.719, steps=11,600")
    print("  Rogers-Gloria_parsed: q=0.513, ted=0.727, steps=511")

    print("\nCurrent (from combined.json):")
    as13 = [c for c in conv if 'AS13_TEC_parsed' in c['course']]
    rogers = [c for c in conv if 'rogers' in c['course'].lower() and '_parsed' in c['course']]

    if as13:
        print(f"  AS13_TEC_parsed: q={as13[0]['avg_q']:.3f}, ted={as13[0]['avg_ted']:.3f}, steps={as13[0]['steps']}")
    if rogers:
        print(f"  Rogers-Gloria_parsed: q={rogers[0]['avg_q']:.3f}, ted={rogers[0]['avg_ted']:.3f}, steps={rogers[0]['steps']}")

    print("\n⚠️  DRAMATIC CHANGE DETECTED!")
    print("  Step counts are MUCH LOWER now (174 vs 511 for Rogers, 4156 vs 11,600 for AS13)")
    print("  This suggests the data was regenerated with different extraction settings")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
