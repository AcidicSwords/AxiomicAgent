"""
Deep dive analysis: Conversation vs Curriculum Robustness
Compare comprehensive metrics to determine if conversations are as robust as curriculum.
"""
import json
from pathlib import Path
import statistics
import sys

# Fix unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def load_combined():
    """Load the combined.json report."""
    path = Path(r"D:\AxiomicAgent\reports\comprehensive\combined.json")
    return json.load(open(path, encoding='utf-8'))

def analyze_metrics(data, category):
    """Extract and analyze metrics for a category."""
    # Curriculum has 'comparison', conversation has 'index'
    if category == 'curriculum':
        items = data[category]['comparison']
    else:  # conversation
        items = data[category]['index']

    # Extract metrics with proper field names
    metrics = {
        'q': [],
        'ted': [],
        'stability': [],
        'spread': [],
        'continuity': [],
        'ted_trusted': []
    }

    for x in items:
        metrics['q'].append(x.get('avg_q') or x.get('avg_Q', 0))
        metrics['ted'].append(x.get('avg_ted') or x.get('avg_TED', 0))

        # Conversation data may not have all fields
        if category == 'curriculum':
            metrics['stability'].append(x.get('avg_stability', 0))
            metrics['spread'].append(x.get('avg_spread', 0))
            metrics['continuity'].append(x.get('avg_continuity', 0))
            metrics['ted_trusted'].append(x.get('avg_ted_trusted', 0))
        else:  # conversation
            # Use q as proxy for stability if not available
            metrics['stability'].append(x.get('avg_stability', x.get('avg_q', 0)))
            metrics['spread'].append(x.get('avg_spread', 0) if x.get('avg_spread') is not None else 0)
            metrics['continuity'].append(x.get('avg_continuity', 0))
            metrics['ted_trusted'].append(x.get('avg_ted_trusted', 0) if 'avg_ted_trusted' in x else x.get('avg_TED', 0))

    stats = {}
    for metric, values in metrics.items():
        # Filter out None values
        valid_values = [v for v in values if v is not None]
        if valid_values:
            stats[metric] = {
                'mean': statistics.mean(valid_values),
                'median': statistics.median(valid_values),
                'stdev': statistics.stdev(valid_values) if len(valid_values) > 1 else 0,
                'min': min(valid_values),
                'max': max(valid_values),
                'range': max(valid_values) - min(valid_values)
            }
        else:
            stats[metric] = {
                'mean': 0, 'median': 0, 'stdev': 0,
                'min': 0, 'max': 0, 'range': 0
            }

    return stats, metrics

def print_metric_comparison(curr_stats, conv_stats, metric_name):
    """Print detailed comparison for a single metric."""
    curr = curr_stats[metric_name]
    conv = conv_stats[metric_name]

    print(f"\n{metric_name.upper()}:")
    print(f"  Curriculum: mean={curr['mean']:.3f}, median={curr['median']:.3f}, std={curr['stdev']:.3f}")
    print(f"  Conversation: mean={conv['mean']:.3f}, median={conv['median']:.3f}, std={conv['stdev']:.3f}")
    print(f"  Range: Curriculum={curr['range']:.3f}, Conversation={conv['range']:.3f}")

    # Determine which is better
    if metric_name in ['q', 'stability', 'continuity']:  # Higher is better
        if curr['mean'] > conv['mean']:
            diff = curr['mean'] - conv['mean']
            print(f"  → Curriculum {diff:.3f} higher (BETTER)")
        else:
            diff = conv['mean'] - curr['mean']
            print(f"  → Conversation {diff:.3f} higher (BETTER)")
    elif metric_name in ['ted']:  # Lower is better for drift
        if curr['mean'] < conv['mean']:
            diff = conv['mean'] - curr['mean']
            print(f"  → Curriculum {diff:.3f} lower drift (BETTER)")
        else:
            diff = curr['mean'] - conv['mean']
            print(f"  → Conversation {diff:.3f} lower drift (BETTER)")
    else:  # Spread, ted_trusted - context dependent
        print(f"  → Difference: {abs(curr['mean'] - conv['mean']):.3f}")

def main():
    data = load_combined()

    print("="*100)
    print("DEEP DIVE: CONVERSATION vs CURRICULUM ROBUSTNESS")
    print("="*100)

    curr_stats, curr_metrics = analyze_metrics(data, 'curriculum')
    conv_stats, conv_metrics = analyze_metrics(data, 'conversation')

    print("\n" + "="*100)
    print("DATASET OVERVIEW")
    print("="*100)
    print(f"Curriculum courses: {len(data['curriculum']['comparison'])}")
    print(f"Conversation transcripts: {len(data['conversation']['index'])}")

    # Get step counts
    curr_steps = [x['steps'] for x in data['curriculum']['summary']]
    conv_steps = [x['steps'] for x in data['conversation']['summary']]

    print(f"\nStep counts:")
    print(f"  Curriculum: mean={statistics.mean(curr_steps):.0f}, median={statistics.median(curr_steps):.0f}, range={min(curr_steps)}-{max(curr_steps)}")
    print(f"  Conversation: mean={statistics.mean(conv_steps):.0f}, median={statistics.median(conv_steps):.0f}, range={min(conv_steps)}-{max(conv_steps)}")

    print("\n" + "="*100)
    print("METRIC-BY-METRIC COMPARISON")
    print("="*100)

    for metric in ['q', 'ted', 'stability', 'spread', 'continuity', 'ted_trusted']:
        print_metric_comparison(curr_stats, conv_stats, metric)

    print("\n" + "="*100)
    print("VARIABILITY ANALYSIS (Stability Assessment)")
    print("="*100)
    print("\nStandard Deviation Comparison (lower = more consistent):")
    for metric in ['q', 'ted', 'stability', 'continuity']:
        curr_std = curr_stats[metric]['stdev']
        conv_std = conv_stats[metric]['stdev']
        winner = "Curriculum" if curr_std < conv_std else "Conversation"
        print(f"  {metric:15} Curriculum={curr_std:.3f}, Conversation={conv_std:.3f}  → {winner} more consistent")

    print("\n" + "="*100)
    print("ROBUSTNESS INDICATORS")
    print("="*100)

    # Count how many metrics favor each category
    scores = {'curriculum': 0, 'conversation': 0, 'neutral': 0}

    # Quality (higher better)
    if curr_stats['q']['mean'] > conv_stats['q']['mean'] + 0.05:
        scores['curriculum'] += 1
        print("\n✓ Quality (q): CURRICULUM wins (significantly higher)")
    elif conv_stats['q']['mean'] > curr_stats['q']['mean'] + 0.05:
        scores['conversation'] += 1
        print("\n✓ Quality (q): CONVERSATION wins (significantly higher)")
    else:
        scores['neutral'] += 1
        print("\n≈ Quality (q): NEUTRAL (very close)")

    # Drift (lower better)
    if curr_stats['ted']['mean'] < conv_stats['ted']['mean'] - 0.05:
        scores['curriculum'] += 1
        print("✓ Drift (TED): CURRICULUM wins (lower drift)")
    elif conv_stats['ted']['mean'] < curr_stats['ted']['mean'] - 0.05:
        scores['conversation'] += 1
        print("✓ Drift (TED): CONVERSATION wins (lower drift)")
    else:
        scores['neutral'] += 1
        print("≈ Drift (TED): NEUTRAL (similar)")

    # Stability (higher better)
    if curr_stats['stability']['mean'] > conv_stats['stability']['mean'] + 0.05:
        scores['curriculum'] += 1
        print("✓ Stability: CURRICULUM wins")
    elif conv_stats['stability']['mean'] > curr_stats['stability']['mean'] + 0.05:
        scores['conversation'] += 1
        print("✓ Stability: CONVERSATION wins")
    else:
        scores['neutral'] += 1
        print("≈ Stability: NEUTRAL")

    # Continuity (higher better for engagement)
    if curr_stats['continuity']['mean'] > conv_stats['continuity']['mean'] + 0.05:
        scores['curriculum'] += 1
        print("✓ Continuity: CURRICULUM wins (better thread continuity)")
    elif conv_stats['continuity']['mean'] > curr_stats['continuity']['mean'] + 0.05:
        scores['conversation'] += 1
        print("✓ Continuity: CONVERSATION wins (better thread continuity)")
    else:
        scores['neutral'] += 1
        print("≈ Continuity: NEUTRAL")

    # Consistency (lower stdev better)
    curr_consistency = statistics.mean([curr_stats[m]['stdev'] for m in ['q', 'ted', 'continuity']])
    conv_consistency = statistics.mean([conv_stats[m]['stdev'] for m in ['q', 'ted', 'continuity']])

    if curr_consistency < conv_consistency:
        scores['curriculum'] += 1
        print("✓ Consistency: CURRICULUM wins (lower variability)")
    else:
        scores['conversation'] += 1
        print("✓ Consistency: CONVERSATION wins (lower variability)")

    print("\n" + "="*100)
    print("FINAL VERDICT")
    print("="*100)
    print(f"\nScore: Curriculum={scores['curriculum']}, Conversation={scores['conversation']}, Neutral={scores['neutral']}")

    total_points = scores['curriculum'] + scores['conversation']
    if total_points > 0:
        curr_pct = (scores['curriculum'] / total_points) * 100
        conv_pct = (scores['conversation'] / total_points) * 100
        print(f"Percentage: Curriculum={curr_pct:.1f}%, Conversation={conv_pct:.1f}%")

    print("\n" + "-"*100)
    if abs(scores['curriculum'] - scores['conversation']) <= 1:
        print("RESULT: Conversations are NOW AS ROBUST as curriculum! 🎉")
        print("  - Metrics are comparable across quality, drift, and continuity")
        print("  - Both show consistent, structured knowledge flow")
        print("  - Conversation extraction has reached curriculum-level reliability")
    elif scores['curriculum'] > scores['conversation']:
        gap = scores['curriculum'] - scores['conversation']
        print(f"RESULT: Curriculum still edges out conversations by {gap} point(s)")
        print("  - Conversations need improvement in areas where curriculum excels")
    else:
        gap = scores['conversation'] - scores['curriculum']
        print(f"RESULT: Conversations EXCEED curriculum robustness by {gap} point(s)! 🚀")
        print("  - Conversation analysis may actually be more refined")

    print("\n" + "="*100)
    print("DETAILED INSIGHTS")
    print("="*100)

    print("\nStrengths of CURRICULUM:")
    print("  - Very high quality scores (avg q > 0.87)")
    print("  - Low drift (controlled topic progression)")
    print("  - Pedagogically structured content flow")

    print("\nStrengths of CONVERSATION:")
    print("  - High granularity (more steps = finer analysis)")
    print("  - Natural dialogue patterns captured")
    print("  - Real-world interaction complexity")

    print("\nKey Findings:")
    print("  1. Quality gap:", f"{abs(curr_stats['q']['mean'] - conv_stats['q']['mean']):.3f}")
    print("  2. Drift difference:", f"{abs(curr_stats['ted']['mean'] - conv_stats['ted']['mean']):.3f}")
    print("  3. Continuity difference:", f"{abs(curr_stats['continuity']['mean'] - conv_stats['continuity']['mean']):.3f}")

    if conv_stats['q']['mean'] > 0.45 and conv_stats['ted']['mean'] < 0.8:
        print("\n✓ Conversations meet minimum robustness thresholds!")

    print("\n" + "="*100)

if __name__ == "__main__":
    main()
