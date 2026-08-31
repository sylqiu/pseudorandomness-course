#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a fully static GitHub Pages site from the MathFlow course data.

Template-as-code: the single player template (templates/player.html) is copied
verbatim — no string replacement. The static build only adds data files plus
data/config.json; the player detects static mode at runtime by fetching
data/config.json (404 on the live server -> API mode, 200 -> file mode).
"""
import json
import shutil
import sys
from pathlib import Path

MATHFLOW = Path('/Users/zd/Documents/mathflow')
sys.path.insert(0, str(MATHFLOW))
import course_server as cs  # noqa: E402  (reuse index/public/solutions builders)

COURSE_ID = 'pseudorandomness-primer'
OUT = Path('/Users/zd/Documents/pseudorandomness-course-site')

# snapshot this script's own source BEFORE rmtree(OUT) may delete it
_SCRIPT_SRC = Path(__file__).read_text(encoding='utf-8')

# ---- 0. clean & scaffold (never touch .git: remove contents only) ----
if OUT.exists():
    for item in OUT.iterdir():
        if item.name == '.git':
            continue
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
else:
    OUT.mkdir(parents=True)
(OUT / 'data' / 'lessons').mkdir(parents=True)
(OUT / 'data' / 'solutions').mkdir(parents=True)

# ---- 1. course index ----
index = [c for c in cs._course_index() if c['id'] == COURSE_ID]
assert index, 'course not found'
(OUT / 'data' / 'courses.json').write_text(
    json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')

# ---- 2. lessons (public: solutions stripped) + solutions ----
for lid, lesson in cs._all_lessons(COURSE_ID):
    pub = cs._lesson_public(lesson)
    audio = cs._lesson_audio_file(COURSE_ID, lid)
    if audio:
        pub['audio'] = {'file': audio}
    (OUT / 'data' / 'lessons' / f'{lid}.json').write_text(
        json.dumps(pub, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'data' / 'solutions' / f'{lid}.json').write_text(
        json.dumps(cs._lesson_solutions(lesson), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  lesson {lid}: public={len(pub["body"])}B, solutions={len(lesson.get("exercises") or [])}')

# ---- 3. media ----
src_media = cs.COURSES_DIR / COURSE_ID / 'media'
if src_media.is_dir():
    shutil.copytree(src_media, OUT / 'media', dirs_exist_ok=True)
    total = sum(f.stat().st_size for f in (OUT / 'media').rglob('*') if f.is_file())
    print(f'  media copied: {total/1e6:.1f} MB')

# ---- 4. template verbatim + static-mode config ----
(OUT / 'index.html').write_text(cs.PLAYER_HTML, encoding='utf-8')
(OUT / 'data' / 'config.json').write_text(
    json.dumps({'mode': 'static'}, ensure_ascii=False), encoding='utf-8')
print(f'  index.html written ({len(cs.PLAYER_HTML)} chars), data/config.json written')

# ---- 5. copy build script + a README into the repo ----
(OUT / 'build_static_site.py').write_text(_SCRIPT_SRC, encoding='utf-8')
(OUT / 'README.md').write_text(
    "# Pseudorandomness Course (static site)\n\n"
    "MathFlow course mode, exported as a static site (GitHub Pages).\n\n"
    "Rebuild with: `python3 build_static_site.py`\n", encoding='utf-8')

print('DONE ->', OUT)
