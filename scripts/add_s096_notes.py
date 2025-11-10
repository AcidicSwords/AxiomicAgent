from pathlib import Path
import json
from PyPDF2 import PdfReader
import sys

pdf_path = Path('RAWDATA/mit18_s096iap23_lec_full.pdf')
if not pdf_path.exists():
    raise SystemExit('PDF not found')
reader = PdfReader(str(pdf_path))
segments = []
chunk_idx = 0
for page in reader.pages:
    text = (page.extract_text() or '').strip()
    if not text:
        continue
    segments.append({'start': chunk_idx * 30.0, 'end': (chunk_idx + 1) * 30.0, 'text': text})
    chunk_idx += 1
if not segments:
    raise SystemExit('No text extracted')
transcript = {'video_id': '18.s096-lecture-notes', 'segments': segments}
transcript_dir = Path('RAWDATA/raw_mit_curriculum/transcripts')
transcript_dir.mkdir(parents=True, exist_ok=True)
transcript_path = transcript_dir / '18.s096-iap-2023_notes_transcript.json'
transcript_path.write_text(json.dumps(transcript, indent=2), encoding='utf-8')

json_path = Path('RAWDATA/raw_mit_curriculum/18.s096-iap-2023.json')
data = json.loads(json_path.read_text(encoding='utf-8'))
items = data.get('items', [])
existing = [it for it in items if it.get('item_id') == 'lecture_notes_pdf']
if existing:
    print('item already exists, updating transcript path')
    existing[0]['transcript_path'] = str(Path('transcripts') / transcript_path.name)
else:
    section_indices = [it.get('section_index') for it in items if isinstance(it.get('section_index'), int)]
    next_section_index = max(section_indices or [-1]) + 1
    new_item = {
        'item_id': 'lecture_notes_pdf',
        'title': 'Lecture Notes',
        'kind': 'lecture',
        'section_index': next_section_index,
        'section_slug': 'notes',
        'section_title': 'Lecture Notes',
        'section_chunk_index': 0,
        'week': next_section_index,
        'order': len(items),
        'source_path': 'resources/18.s096-lecture-notes',
        'transcript_path': str(Path('transcripts') / transcript_path.name),
    }
    items.append(new_item)
    data['items'] = items
    json_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
print('transcript saved, json updated')
