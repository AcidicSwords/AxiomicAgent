"""
Test conversation adapter on positive vs negative conversation examples.

Positive: Professional, productive, healthy conversations
Negative: Chaotic, evasive, or dysfunctional conversations

Goal: Calibrate metrics to distinguish conversation quality.
"""

import sys
sys.path.insert(0, 'D:\\AxiomicAgent')

from adapters.conversation.adapter import ConversationAdapter
from adapters.conversation.regime import RegimeClassifier
import json
from pathlib import Path
from collections import defaultdict


def load_and_process(filepath, label, max_turns=None):
    """Process a transcript and return analysis."""

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    title = data.get('title', Path(filepath).stem)
    turns = data.get('transcript', data.get('turns', []))

    # Filter NARRATION
    turns = [t for t in turns if t.get('speaker') != 'NARRATION']

    if max_turns:
        turns = turns[:max_turns]

    # Process
    adapter = ConversationAdapter()
    classifier = RegimeClassifier()

    all_signals = []
    all_regimes = []

    print(f"\nProcessing [{label}]: {title}")
    print(f"  Turns: {len(turns)}")

    for i, turn in enumerate(turns):
        speaker = turn.get('speaker', 'Unknown')
        text = turn.get('text', '')

        if not text or len(text.strip()) < 10:
            continue

        role = "user" if i % 2 == 0 else "assistant"

        try:
            signals = adapter.process_turn(role, text)
            all_signals.append(signals)

            regime = classifier.classify(signals)
            all_regimes.append(regime)
        except Exception as e:
            continue

    summary = adapter.get_conversation_summary()

    # Regime distribution
    regime_counts = defaultdict(int)
    for r in all_regimes:
        regime_counts[r.regime] += 1

    trends = classifier.detect_trends(all_signals)

    return {
        'label': label,
        'title': title,
        'summary': summary,
        'signals': all_signals,
        'regime_distribution': dict(regime_counts),
        'trends': trends
    }


def compare_positive_vs_negative(positive_results, negative_results):
    """
    Compare metrics between positive and negative conversations.
    """

    print("\n" + "="*80)
    print("POSITIVE vs NEGATIVE CONVERSATION COMPARISON")
    print("="*80 + "\n")

    # Aggregate stats
    def aggregate_stats(results):
        all_q = []
        all_ted = []
        all_cont = []
        all_spread = []

        for result in results:
            for sig in result['signals']:
                all_q.append(sig.q)
                all_ted.append(sig.TED)
                all_cont.append(sig.continuity)
                if sig.spread is not None:
                    all_spread.append(sig.spread)

        import numpy as np
        return {
            'q_mean': np.mean(all_q) if all_q else 0,
            'q_std': np.std(all_q) if all_q else 0,
            'ted_mean': np.mean(all_ted) if all_ted else 0,
            'ted_std': np.std(all_ted) if all_ted else 0,
            'cont_mean': np.mean(all_cont) if all_cont else 0,
            'cont_std': np.std(all_cont) if all_cont else 0,
            'spread_mean': np.mean(all_spread) if all_spread else 0,
        }

    pos_stats = aggregate_stats(positive_results)
    neg_stats = aggregate_stats(negative_results)

    print("METRIC COMPARISON:")
    print(f"{'Metric':<15} {'Positive':<20} {'Negative':<20} {'Difference':<15}")
    print("-" * 70)

    print(f"{'q (quality)':<15} "
          f"{pos_stats['q_mean']:.3f} ± {pos_stats['q_std']:.3f}     "
          f"{neg_stats['q_mean']:.3f} ± {neg_stats['q_std']:.3f}     "
          f"{(neg_stats['q_mean'] - pos_stats['q_mean']):.3f}")

    print(f"{'TED (drift)':<15} "
          f"{pos_stats['ted_mean']:.3f} ± {pos_stats['ted_std']:.3f}     "
          f"{neg_stats['ted_mean']:.3f} ± {neg_stats['ted_std']:.3f}     "
          f"{(neg_stats['ted_mean'] - pos_stats['ted_mean']):.3f}")

    print(f"{'continuity':<15} "
          f"{pos_stats['cont_mean']:.3f} ± {pos_stats['cont_std']:.3f}     "
          f"{neg_stats['cont_mean']:.3f} ± {neg_stats['cont_std']:.3f}     "
          f"{(neg_stats['cont_mean'] - pos_stats['cont_mean']):.3f}")

    print("\n")

    # Hypothesis testing
    print("HYPOTHESES:")
    print()

    print("H1: Negative conversations have LOWER quality (q)")
    if neg_stats['q_mean'] < pos_stats['q_mean']:
        diff = pos_stats['q_mean'] - neg_stats['q_mean']
        print(f"    [+] CONFIRMED: Negative q is {diff:.3f} lower")
        print(f"        Interpretation: Chaotic/evasive conversations less coherent")
    else:
        print(f"    [!] REJECTED: Negative q is higher or equal")

    print()
    print("H2: Negative conversations have HIGHER drift (TED)")
    if neg_stats['ted_mean'] > pos_stats['ted_mean']:
        diff = neg_stats['ted_mean'] - pos_stats['ted_mean']
        print(f"    [+] CONFIRMED: Negative TED is {diff:.3f} higher")
        print(f"        Interpretation: Topic avoidance, fragmentation")
    else:
        print(f"    [!] REJECTED: Negative TED is lower or equal")

    print()
    print("H3: Negative conversations have LOWER continuity")
    if neg_stats['cont_mean'] < pos_stats['cont_mean']:
        diff = pos_stats['cont_mean'] - neg_stats['cont_mean']
        print(f"    [+] CONFIRMED: Negative continuity is {diff:.3f} lower")
        print(f"        Interpretation: Evasion, interruption, lack of engagement")
    else:
        print(f"    [!] REJECTED: Negative continuity is higher or equal")

    print()
    print("H4: Negative conversations have HIGHER variability (std)")
    if neg_stats['q_std'] > pos_stats['q_std']:
        print(f"    [+] CONFIRMED: Negative q std is {neg_stats['q_std']:.3f} vs {pos_stats['q_std']:.3f}")
        print(f"        Interpretation: Unstable, erratic patterns")
    else:
        print(f"    [!] REJECTED: Negative variability is lower or equal")

    print("\n")

    # Individual conversation breakdown
    print("="*80)
    print("INDIVIDUAL CONVERSATION METRICS")
    print("="*80 + "\n")

    all_results = positive_results + negative_results

    print(f"{'Conversation':<50} {'Label':<10} {'q':<8} {'TED':<8} {'Cont':<8}")
    print("-" * 84)

    for result in all_results:
        title = result['title'][:48]
        label = result['label']
        s = result['summary']

        print(f"{title:<50} {label:<10} {s['avg_q']:<8.3f} {s['avg_TED']:<8.3f} {s['avg_continuity']:<8.3f}")

    print("\n")

    # Regime distribution comparison
    print("="*80)
    print("REGIME DISTRIBUTION COMPARISON")
    print("="*80 + "\n")

    # Aggregate regime counts
    pos_regimes = defaultdict(int)
    neg_regimes = defaultdict(int)

    for result in positive_results:
        for regime, count in result['regime_distribution'].items():
            pos_regimes[regime] += count

    for result in negative_results:
        for regime, count in result['regime_distribution'].items():
            neg_regimes[regime] += count

    pos_total = sum(pos_regimes.values())
    neg_total = sum(neg_regimes.values())

    all_regimes = set(list(pos_regimes.keys()) + list(neg_regimes.keys()))

    print(f"{'Regime':<15} {'Positive':<20} {'Negative':<20}")
    print("-" * 55)

    for regime in sorted(all_regimes):
        pos_count = pos_regimes.get(regime, 0)
        neg_count = neg_regimes.get(regime, 0)

        pos_pct = (pos_count / pos_total * 100) if pos_total > 0 else 0
        neg_pct = (neg_count / neg_total * 100) if neg_total > 0 else 0

        print(f"{regime:<15} {pos_count:>5} ({pos_pct:>5.1f}%)        {neg_count:>5} ({neg_pct:>5.1f}%)")

    print("\n")


def main():
    """Run positive vs negative comparison."""

    reports_dir = Path("D:\\AxiomicAgent\\reports")

    # Positive examples
    positive = [
        "rogers_gloria_parsed.json",
        "CPD_ September 26, 1960 Debate Transcript.json",
    ]

    # Negative examples
    negative = [
        "Bad/CPD_ September 29, 2020 Debate Transcript.json",
        # "Bad/Full Transcript_ Lance Armstrong on Oprah – Armchair Spectator.json",  # Skip if too long
    ]

    positive_results = []
    negative_results = []

    print("="*80)
    print("PROCESSING CONVERSATIONS")
    print("="*80)

    # Process positive
    for fname in positive:
        fpath = reports_dir / fname
        if fpath.exists():
            try:
                result = load_and_process(fpath, "POSITIVE")
                positive_results.append(result)
            except Exception as e:
                print(f"[!] Error processing {fname}: {e}")

    # Process negative
    for fname in negative:
        fpath = reports_dir / fname
        if fpath.exists():
            try:
                result = load_and_process(fpath, "NEGATIVE", max_turns=100)  # Limit for performance
                negative_results.append(result)
            except Exception as e:
                print(f"[!] Error processing {fname}: {e}")

    # Compare
    if positive_results and negative_results:
        compare_positive_vs_negative(positive_results, negative_results)
    else:
        print("[!] Insufficient data for comparison")

    print("="*80)
    print("CALIBRATION INSIGHTS")
    print("="*80 + "\n")

    print("Based on positive vs negative comparison:")
    print()
    print("1. If negative conversations show LOWER q:")
    print("   -> Quality metric successfully detects dysfunction")
    print("   -> Can use q < threshold as warning signal")
    print()
    print("2. If negative conversations show HIGHER TED:")
    print("   -> Drift metric detects topic avoidance/fragmentation")
    print("   -> Excessive drift = red flag")
    print()
    print("3. If negative conversations show LOWER continuity:")
    print("   -> Continuity metric detects evasion/interruption")
    print("   -> Can distinguish engagement vs avoidance")
    print()
    print("4. If negative conversations show HIGHER variability:")
    print("   -> Stable metrics = healthy conversation")
    print("   -> Erratic metrics = dysfunctional conversation")
    print()

    print("Next steps:")
    print("  - If hypotheses confirmed -> thresholds should separate positive/negative")
    print("  - If hypotheses rejected -> need better extraction or different metrics")
    print("  - Collect more examples to establish statistical significance")
    print()


if __name__ == "__main__":
    main()
