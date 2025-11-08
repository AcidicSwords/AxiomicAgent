import json
from pathlib import Path

root = Path('reports/mit_curriculum_insights_identity')
summary = []
for path in sorted(root.glob('*_insight.json')):
    data = json.loads(path.read_text())
    aggr = data.get('aggregates', {})
    entry = {
        'course': path.stem.replace('_insight', ''),
        'avg_q': aggr.get('avg_q'),
        'avg_ted': aggr.get('avg_ted'),
        'avg_stability': aggr.get('avg_stability'),
        'avg_spread': aggr.get('avg_spread'),
        'steps': aggr.get('steps'),
        'recommendations': data.get('recommendations', []),
        'counts': data['steps'][0].get('counts', {}) if data.get('steps') else {},
        'top_nodes': data['steps'][0].get('top_nodes', []) if data.get('steps') else [],
    }
    entry['top_nodes'] = entry['top_nodes'][:3]
    summary.append(entry)

print('=== MIT Curriculum Insight Summary (Identity Policy) ===')
print(f'Total courses: {len(summary)}')
print('\nPer-course aggregates:')
for row in summary:
    print(f"- {row['course']}: q={row['avg_q']}, ted={row['avg_ted']}, stability={row['avg_stability']}, spread={row['avg_spread']}")
    counts = ', '.join(f"{k}:{v}" for k, v in row['counts'].items())
    print(f'   counts: {counts}')
    if row['top_nodes']:
        nodes = ', '.join(node['label'] for node in row['top_nodes'])
        print(f'   top nodes: {nodes}')
    recs = '; '.join(row['recommendations'])
    if recs:
        print(f'   recommendations: {recs}')
print('\nComparison saved to reports/mit_curriculum_insights_identity/comparison.json')
