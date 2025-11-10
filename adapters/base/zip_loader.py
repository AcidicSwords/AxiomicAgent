import csv
import hashlib
import io
import json
import os
import zipfile
from typing import Dict, Set, Tuple

from .types import RawStream, Edge, Frame


def _hash_zip(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()[:16]


def _read_csv(zf: zipfile.ZipFile, name: str):
    with zf.open(name) as f:
        data = io.TextIOWrapper(f, encoding='utf-8')
        reader = csv.DictReader(data)
        for row in reader:
            yield row


def load_zip_stream(path: str) -> RawStream:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    nodes: Dict[int, str] = {}
    obs_steps: Dict[int, Frame] = {}
    true_steps: Dict[int, Frame] = {}
    meta: Dict[str, object] = {}

    with zipfile.ZipFile(path, 'r') as zf:
        names = set(zf.namelist())
        if 'nodes.csv' in names:
            for row in _read_csv(zf, 'nodes.csv'):
                nid = int(row['id'])
                label = row.get('term') or row.get('concept') or row.get('label') or row.get('name') or row['id']
                nodes[nid] = label
        else:
            raise ValueError('nodes.csv missing in zip stream')

        if 'edges_obs.csv' not in names:
            raise ValueError('edges_obs.csv missing in zip stream')
        for row in _read_csv(zf, 'edges_obs.csv'):
            step = int(row['step'])
            edge = (int(row['src']), int(row['dst']))
            obs_steps.setdefault(step, set()).add(edge)

        if 'edges_true.csv' in names:
            for row in _read_csv(zf, 'edges_true.csv'):
                step = int(row['step'])
                edge = (int(row['src']), int(row['dst']))
                true_steps.setdefault(step, set()).add(edge)

        if 'meta.json' in names:
            with zf.open('meta.json') as f:
                meta.update(json.load(io.TextIOWrapper(f, encoding='utf-8')))

    meta.setdefault('dataset_path', path)
    meta.setdefault('hash', _hash_zip(path))
    meta.setdefault('steps', len(obs_steps))
    meta.setdefault('nodes', len(nodes))

    return RawStream(nodes=nodes, obs_steps=obs_steps, true_steps=true_steps, meta=meta)

