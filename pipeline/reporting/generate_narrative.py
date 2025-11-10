import csv
import json
from pathlib import Path
from collections import Counter, defaultdict


ROOT = Path(__file__).resolve().parents[2]


def load_combined(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def top_nodes_edges(fs_dir: Path, top_k: int = 5):
    nodes_path = fs_dir / 'nodes.csv'
    edges_path = fs_dir / 'edges_obs.csv'
    if not nodes_path.exists() or not edges_path.exists():
        return None

    id_to_label = {}
    try:
        with nodes_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # nodes.csv has columns: id,label,...
                try:
                    nid = int(row['id'])
                except Exception:
                    continue
                id_to_label[nid] = row.get('label') or row.get('item_id') or str(nid)
    except Exception:
        return None

    deg = Counter()
    edge_counts = Counter()
    try:
        with edges_path.open('r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    s = int(row['src']); d = int(row['dst'])
                except Exception:
                    continue
                deg[s] += 1
                deg[d] += 1
                edge_counts[(s, d)] += 1
    except Exception:
        return None

    top_nodes = []
    for nid, c in deg.most_common(top_k):
        top_nodes.append({
            'id': nid,
            'label': id_to_label.get(nid, str(nid)),
            'degree': c,
        })

    top_edges = []
    for (s, d), c in edge_counts.most_common(top_k):
        top_edges.append({
            'src_id': s,
            'src_label': id_to_label.get(s, str(s)),
            'dst_id': d,
            'dst_label': id_to_label.get(d, str(d)),
            'count': c,
        })

    return {'top_nodes': top_nodes, 'top_edges': top_edges}


def write_narrative_md(out_path: Path, curriculum_sections, conversation_sections):
    lines = []
    lines.append('# Comprehensive Narrative')
    lines.append('')

    if curriculum_sections:
        lines.append('## Curriculum')
        for sec in curriculum_sections:
            lines.append(f"### {sec['title']}")
            lines.append(f"- id: `{sec['id']}`")
            lines.append(f"- avg_q: {sec['avg_q']:.3f} | avg_TED: {sec['avg_ted']:.3f} | steps: {sec['steps']}")
            if sec.get('top_nodes'):
                tn = ', '.join([f"{n['label']} (d={n['degree']})" for n in sec['top_nodes']])
                lines.append(f"- top nodes: {tn}")
            if sec.get('top_edges'):
                te = ', '.join([f"{e['src_label']} â†’ {e['dst_label']} (n={e['count']})" for e in sec['top_edges']])
                lines.append(f"- top edges: {te}")
            if sec.get('summary'):
                lines.append(f"- summary: {sec['summary']}")
            lines.append('')

    if conversation_sections:
        lines.append('## Conversations')
        for sec in conversation_sections:
            lines.append(f"### {sec['title']}")
            lines.append(f"- id: `{sec['id']}`")
            lines.append(f"- avg_q: {sec['avg_q']:.3f} | avg_TED: {sec['avg_ted']:.3f} | steps: {sec['steps']}")
            if sec.get('top_nodes'):
                tn = ', '.join([f"{n['label']} (d={n['degree']})" for n in sec['top_nodes']])
                lines.append(f"- top nodes: {tn}")
            if sec.get('top_edges'):
                te = ', '.join([f"{e['src_label']} â†’ {e['dst_label']} (n={e['count']})" for e in sec['top_edges']])
                lines.append(f"- top edges: {te}")
            if sec.get('summary'):
                lines.append(f"- summary: {sec['summary']}")
            lines.append('')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text('\n'.join(lines), encoding='utf-8')


def main():
    combined_path = ROOT / 'reports' / 'comprehensive' / 'combined.json'
    if not combined_path.exists():
        print('combined.json not found; aborting narrative generation.')
        return

    data = load_combined(combined_path)

    curriculum_summary = []
    conv_summary = []

    # Parse curriculum
    cur = data.get('curriculum', {})
    cur_list = cur.get('summary', []) if isinstance(cur, dict) else []
    for entry in cur_list:
        course_key = entry.get('course') or entry.get('id') or ''
        # Normalize id (strip trailing insight tags)
        base_id = course_key.replace('_insight_TEST', '').replace('_insight', '')
        fs_dir = ROOT / 'datasets' / 'mit_curriculum_fs' / base_id
        tops = top_nodes_edges(fs_dir) or {}
        curriculum_summary.append({
            'id': base_id,
            'title': base_id,
            'avg_q': float(entry.get('avg_q', 0.0)),
            'avg_ted': float(entry.get('avg_ted', 0.0)),
            'steps': int(entry.get('steps', 0) or 0),
            **tops,
            'summary': '',
        })

    # Parse conversations
    conv = data.get('conversation', {})
    conv_list = conv.get('summary', []) if isinstance(conv, dict) else []
    for entry in conv_list:
        conv_key = entry.get('course') or entry.get('id') or ''
        # FS datasets for conversation appear under mit_curriculum_fs as conversation_* in this repo
        fs_dir = ROOT / 'datasets' / 'mit_curriculum_fs' / conv_key.replace('.metrics', '')
        tops = top_nodes_edges(fs_dir) or {}
        conv_summary.append({
            'id': conv_key,
            'title': conv_key,
            'avg_q': float(entry.get('avg_q', 0.0)),
            'avg_ted': float(entry.get('avg_ted', 0.0)),
            'steps': int(entry.get('steps', 0) or 0),
            **tops,
            'summary': '',
        })

    out_md = ROOT / 'reports' / 'comprehensive' / 'narrative.md'
    write_narrative_md(out_md, curriculum_summary, conv_summary)
    print(f'Wrote narrative to {out_md}')


if __name__ == '__main__':
    main()


