#!/usr/bin/env python3
"""Pre-generates the /armenian read-out clips with Microsoft's Edge voice hy-AM-AnahitNeural (edge-tts, no API key).
One mp3 per distinct text of the deck allow-list (letter id, word hy, first example sentence), named by the sha1 of the
UTF-8 text: web/server/data/tts/<sha1>.mp3, plus index.json (sha1 -> text). The app only reads these files; it never generates.
Resumable: existing files are skipped. Needs `pip install edge-tts` (CT 104: /opt/edge-tts/venv).
Run: /opt/edge-tts/venv/bin/python3 -I addons/armenian/scripts/build-tts.py
"""
import asyncio, hashlib, json, os

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'web', 'server', 'data')
OUT = os.path.join(DATA, 'tts')
VOICE = 'hy-AM-AnahitNeural'


def texts():
    deck = json.load(open(os.path.join(DATA, 'armenian.json'), encoding='utf-8'))
    cards = deck['cards'] if isinstance(deck, dict) else deck
    out = set()
    for c in cards:
        out.add(c['id'][2:] if c['id'].startswith('w:') else c['id'])
        if c.get('t') == 'w' and c.get('hy'):
            out.add(c['hy'])
        if c.get('ex'):
            out.add(c['ex'][0])
    return sorted(t for t in out if t)


async def main():
    os.makedirs(OUT, exist_ok=True)
    todo = texts()
    index, made, fails = {}, 0, []
    for t in todo:
        sha = hashlib.sha1(t.encode('utf-8')).hexdigest()
        index[sha] = t
        f = os.path.join(OUT, sha + '.mp3')
        if os.path.exists(f):
            continue
        for attempt in range(3):
            try:
                await edge_tts.Communicate(t, VOICE).save(f + '.tmp')
                if os.path.getsize(f + '.tmp') < 500:
                    raise RuntimeError('clip too small')
                os.replace(f + '.tmp', f)
                made += 1
                break
            except Exception as e:
                if os.path.exists(f + '.tmp'):
                    os.remove(f + '.tmp')
                if attempt == 2:
                    fails.append((t, str(e)))
                else:
                    await asyncio.sleep(2 * (attempt + 1))
        await asyncio.sleep(0.3)
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    total = sum(os.path.getsize(os.path.join(OUT, s + '.mp3')) for s in index if os.path.exists(os.path.join(OUT, s + '.mp3')))
    print(f'texts {len(todo)}, generated {made}, total {total} bytes, failures {len(fails)}')
    for t, e in fails:
        print('FAIL', t, e)


asyncio.run(main())
