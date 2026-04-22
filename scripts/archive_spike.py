"""Snapshot the current spike + mapping + notes into _reports/_archive/ with a timestamp."""
import shutil
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / '_reports' / '_archive'
ARCHIVE.mkdir(parents=True, exist_ok=True)
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M')

to_archive = [
    (ROOT / '_reports' / 'spike_wheel_comparison.html',  f'spike_wheel_comparison_v8_{ts}.html'),
    (ROOT / '_reports' / 'spike_standard_map.html',       f'spike_standard_map_v8_{ts}.html'),
    (ROOT / 'l2_wedge_map.xlsx',                          f'l2_wedge_map_v8_{ts}.xlsx'),
    (ROOT / '_pipeline' / 'src' / 'pipeline' / 'motivators_section.py',  f'motivators_section_v8_{ts}.py'),
    (ROOT / '_pipeline' / 'data' / 'wedge_narratives.json',              f'wedge_narratives_v8_{ts}.json'),
    (ROOT / '_pipeline' / 'scripts' / 'build_spike_v4.py',               f'build_spike_v4_{ts}.py'),
]

saved = []
for src, name in to_archive:
    if not src.exists():
        print(f'  SKIP (not found): {src}')
        continue
    dst = ARCHIVE / name
    shutil.copyfile(src, dst)
    saved.append(dst)
    print(f'  {src.name} -> {dst.name}  ({dst.stat().st_size} bytes)')

print(f'\nArchived {len(saved)} files to {ARCHIVE}')
