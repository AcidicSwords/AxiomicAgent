"""
Test conversation adapter on diverse real-world transcripts.

Processes 7 different conversation types:
- Therapy (Rogers-Gloria)
- Formal debate (Bill Nye vs Ken Ham)
- Presidential debate (Kennedy-Nixon 1960)
- Crisis communication (Apollo 13)
- Interview (Oprah with Harry & Meghan)
- Interview under pressure (Prince Andrew)
- Interview/monologue (Bryan Stevenson)

Goal: Calibrate metrics and thresholds across conversation genres.
"""

import sys
sys.path.insert(0, 'D:\\AxiomicAgent')

from adapters.conversation.adapter import ConversationAdapter
from adapters.conversation.regime import RegimeClassifier
import json
import os
from pathlib import Path
from collections import defaultdict


def load_transcript(filepath):
    """Load transcript JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def process_transcript(filepath, max_turns=None):
    """
    Process a transcript file through conversation adapter.

    Args:
        filepath: Path to JSON transcript
        max_turns: Optional limit on turns to process (for performance)

    Returns:
        dict with analysis results
    """
    # Load data
    data = load_transcript(filepath)

    # Extract metadata
    title = data.get('title', Path(filepath).stem)
    context = data.get('context', '')
    actors = data.get('actors', [])

    # Get turns
    turns = data.get('transcript', data.get('turns', []))

    # Filter out NARRATION
    turns = [t for t in turns if t.get('speaker') != 'NARRATION']

    if max_turns:
        turns = turns[:max_turns]

    # Initialize adapter and classifier
    adapter = ConversationAdapter()
    classifier = RegimeClassifier()

    # Process turns
    all_signals = []
    all_regimes = []

    print(f"\n{'='*70}")
    print(f"Processing: {title}")
    print(f"Actors: {', '.join(actors[:3])}{'...' if len(actors) > 3 else ''}")
    print(f"Total turns: {len(turns)}")
    print(f"{'='*70}\n")

    for i, turn in enumerate(turns):
        speaker = turn.get('speaker', 'Unknown')
        text = turn.get('text', '')

        # Determine role (simplified)
        # In real conversations, this is more nuanced
        # For now, alternate or use metadata
        role = "user" if i % 2 == 0 else "assistant"

        if not text or len(text.strip()) < 10:
            continue

        # Process turn
        try:
            signals = adapter.process_turn(role, text)
            all_signals.append(signals)

            # Classify regime
            regime = classifier.classify(signals)
            all_regimes.append(regime)

        except Exception as e:
            print(f"Error processing turn {i}: {e}")
            continue

    # Compute summary statistics
    summary = adapter.get_conversation_summary()

    # Regime distribution
    regime_counts = defaultdict(int)
    for r in all_regimes:
        regime_counts[r.regime] += 1

    # Detect trends
    trends = classifier.detect_trends(all_signals)

    return {
        'title': title,
        'context': context,
        'actors': actors,
        'turn_count': len(turns),
        'processed_count': len(all_signals),
        'summary': summary,
        'signals': all_signals,
        'regimes': all_regimes,
        'regime_distribution': dict(regime_counts),
        'trends': trends
    }


def compare_conversations(results_list):
    """
    Compare metrics across different conversation types.
    """
    print("\n" + "="*70)
    print("COMPARATIVE ANALYSIS ACROSS CONVERSATION TYPES")
    print("="*70 + "\n")

    # Table header
    print(f"{'Conversation':<40} {'Avg q':<8} {'Avg TED':<8} {'Avg Cont':<8} {'Turns':<6}")
    print("-" * 70)

    for result in results_list:
        title = result['title'][:38]
        summary = result['summary']

        print(f"{title:<40} "
              f"{summary['avg_q']:<8.3f} "
              f"{summary['avg_TED']:<8.3f} "
              f"{summary['avg_continuity']:<8.3f} "
              f"{result['processed_count']:<6}")

    print("\n")

    # Regime distribution comparison
    print("="*70)
    print("REGIME DISTRIBUTIONS")
    print("="*70 + "\n")

    all_regimes = set()
    for result in results_list:
        all_regimes.update(result['regime_distribution'].keys())

    # Header
    print(f"{'Conversation':<40}", end='')
    for regime in sorted(all_regimes):
        print(f"{regime[:8]:<9}", end='')
    print()
    print("-" * 70)

    # Data
    for result in results_list:
        title = result['title'][:38]
        print(f"{title:<40}", end='')

        total = result['processed_count']
        for regime in sorted(all_regimes):
            count = result['regime_distribution'].get(regime, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"{pct:>5.1f}%   ", end='')
        print()

    print("\n")

    # Genre insights
    print("="*70)
    print("GENRE-SPECIFIC INSIGHTS")
    print("="*70 + "\n")

    for result in results_list:
        title = result['title']
        summary = result['summary']
        trends = result['trends']

        print(f"{title}:")
        print(f"  Metrics: q={summary['avg_q']:.3f}, TED={summary['avg_TED']:.3f}, cont={summary['avg_continuity']:.3f}")
        print(f"  Trends: {trends.get('pattern', 'unknown')} pattern")

        # Interpret based on genre expectations
        if 'debate' in title.lower():
            if summary['avg_TED'] > 0.4:
                print(f"  [+] High drift typical of adversarial debate")
            if summary['avg_continuity'] < 0.2:
                print(f"  [+] Low continuity expected in competitive format")

        elif 'therapy' in title.lower() or 'rogers' in title.lower():
            if summary['avg_continuity'] > 0.3:
                print(f"  [+] Good continuity shows therapeutic following")
            if summary['avg_q'] > 0.6:
                print(f"  [+] High coherence indicates focused session")

        elif 'interview' in title.lower() or 'oprah' in title.lower():
            if summary['avg_TED'] < 0.3 and summary['avg_continuity'] > 0.3:
                print(f"  [+] Moderate drift + continuity typical of guided interview")

        elif 'apollo' in title.lower() or 'crisis' in title.lower():
            if summary['avg_q'] > 0.7:
                print(f"  [+] High coherence critical in crisis communication")

        print()


def main():
    """Run analysis on all transcripts."""

    transcript_dir = Path("D:\\AxiomicAgent\\reports")

    # Define transcripts to analyze
    transcripts = [
        "rogers_gloria_parsed.json",  # Use parsed version
        "CPD_ September 26, 1960 Debate Transcript.json",
        "prince-andrew-newsnight-interview-with-emily-maitlis-transcript.json",
    ]

    # Add others if they exist and have correct encoding
    optional = [
        "Bill Nye Debates Ken Ham (Full Transcript) — The Singju Post.json",
        "Oprah with Prince Harry and Meghan Markle — Interview Transcript _ by Kate Shaw _ Medium.json",
        "Bryan Stevenson — Finding the Courage for What's Redemptive _ The On Being Project.json",
        "AS13_TEC.json",
    ]

    for fname in optional:
        fpath = transcript_dir / fname
        if fpath.exists():
            transcripts.append(fname)

    # Process each transcript
    results = []

    for fname in transcripts:
        fpath = transcript_dir / fname

        if not fpath.exists():
            print(f"[!] File not found: {fname}")
            continue

        try:
            # Limit turns for performance (Apollo 13 is huge)
            max_turns = 100 if 'AS13' in fname else None

            result = process_transcript(fpath, max_turns=max_turns)
            results.append(result)

        except Exception as e:
            print(f"[!] Error processing {fname}: {e}")
            continue

    # Compare results
    if results:
        compare_conversations(results)

    # Export detailed results
    export_data = []
    for result in results:
        export_data.append({
            'title': result['title'],
            'context': result['context'],
            'turn_count': result['turn_count'],
            'summary': result['summary'],
            'regime_distribution': result['regime_distribution'],
            'trends': result['trends']
        })

    output_file = 'diverse_transcripts_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print(f"[+] Detailed results exported to {output_file}")
    print()

    # Calibration recommendations
    print("="*70)
    print("CALIBRATION RECOMMENDATIONS")
    print("="*70 + "\n")

    if results:
        # Aggregate metrics
        all_q = []
        all_ted = []
        all_cont = []

        for result in results:
            for sig in result['signals']:
                all_q.append(sig.q)
                all_ted.append(sig.TED)
                all_cont.append(sig.continuity)

        import numpy as np

        print("Observed metric distributions:")
        print(f"  q:          mean={np.mean(all_q):.3f}, std={np.std(all_q):.3f}, "
              f"median={np.median(all_q):.3f}")
        print(f"  TED:        mean={np.mean(all_ted):.3f}, std={np.std(all_ted):.3f}, "
              f"median={np.median(all_ted):.3f}")
        print(f"  continuity: mean={np.mean(all_cont):.3f}, std={np.std(all_cont):.3f}, "
              f"median={np.median(all_cont):.3f}")
        print()

        print("Suggested regime threshold adjustments:")
        print("  Current 'stuck' signature: q > 0.80, TED < 0.15, cont > 0.65")

        # Check if any conversations are actually stuck
        stuck_counts = sum(r['regime_distribution'].get('stuck', 0) for r in results)

        if stuck_counts == 0:
            print("  [!] No stuck states detected - thresholds may be too strict")
            print(f"      Consider: q > 0.75, TED < 0.20, cont > 0.55")

        print()
        print("  Current 'exploring' signature: 0.55 < q < 0.85, 0.20 < TED < 0.40")
        exploring_pct = np.mean([r['regime_distribution'].get('exploring', 0) /
                                 max(r['processed_count'], 1)
                                 for r in results])
        print(f"      {exploring_pct*100:.1f}% of turns classified as exploring")

        print()


if __name__ == "__main__":
    main()
