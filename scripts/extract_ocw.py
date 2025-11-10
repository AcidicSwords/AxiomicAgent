from pathlib import Path
import json
from builders.curriculum.mit_ocw import extract_items_from_zip
root = Path('RAWDATA/RawOCW')
out = Path('RAWDATA/raw_mit_curriculum')
out.mkdir(parents=True, exist_ok=True)
for zip_path in sorted(root.glob('*.zip')):
    course = extract_items_from_zip(zip_path, profile='stem')
    target = out / f"{zip_path.stem}.json"
    target.write_text(json.dumps(course, indent=2), encoding='utf-8')
    print('wrote', target)
