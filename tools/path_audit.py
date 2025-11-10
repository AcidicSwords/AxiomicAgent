#!/usr/bin/env python
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[1]
RAW_YT = ROOT / 'RAWDATA' / 'RawYT'
TRANS_ROOT = ROOT / 'RAWDATA' / 'RawYTTranscripts'


def _fix_crlf(text: str) -> str:
    # Normalize any stray CRLF issues implicitly via Python I/O
    return text


def audit_youtube_normalized() -> int:
    changed = 0
    if not RAW_YT.exists():
        return 0
    for json_path in sorted(RAW_YT.glob('*.json')):
        try:
            # tolerate BOM
            text = json_path.read_text(encoding='utf-8-sig')
            data: Dict[str, Any] = json.loads(text)
        except Exception:
            continue
        course_id = data.get('course_id') or json_path.stem
        items = data.get('items') or []
        course_trans_dir = TRANS_ROOT / course_id
        for item in items:
            tr = item.get('transcript_path')
            vid = str(item.get('item_id') or '').strip()
            if not vid:
                continue
            # If transcript path points at axiom_corelite, rewrite to local transcripts
            needs_fix = isinstance(tr, str) and ('axiom_corelite' in tr or 'AxiomCoreLite' in tr)
            # If missing but a VTT exists locally, attach
            missing = (not tr) and (course_trans_dir / f'{vid}.vtt').exists()
            if needs_fix or missing:
                rel = os.path.relpath(course_trans_dir / f'{vid}.vtt', start=json_path.parent)
                item['transcript_path'] = rel.replace('\\', '/')
                changed += 1
        if changed:
            json_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return changed


def main() -> None:
    yt = audit_youtube_normalized()
    print(f'[path_audit] youtube normalized updated items: {yt}')


if __name__ == '__main__':
    main()
