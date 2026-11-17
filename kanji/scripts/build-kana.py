#!/usr/bin/env python3
"""Adds hiragana + katakana to addons/kanji/web/server/data/kanji.json (in front of the kanji, levels n=6 hiragana, n=7 katakana):
romaji as the meaning, stroke count from KanjiVG, up to three common example words written only in that script.
Run after build-kanji.py (idempotent: drops the old kana first). Source: jmdict-eng-common-*.json in the given dir (see build-kanji.py).
Run: python3 -I addons/kanji/scripts/build-kana.py /tmp/kanji-dl
"""
import glob, json, os, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

src = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web', 'server', 'data', 'kanji.json')
J = json.load(open(glob.glob(os.path.join(src, 'jmdict-eng-common-*.json'))[0]))['words']

BASE = [('a','i','u','e','o'), ('ka','ki','ku','ke','ko'), ('sa','shi','su','se','so'), ('ta','chi','tsu','te','to'),
        ('na','ni','nu','ne','no'), ('ha','hi','fu','he','ho'), ('ma','mi','mu','me','mo'), ('ya',None,'yu',None,'yo'),
        ('ra','ri','ru','re','ro'), ('wa',None,None,None,'wo'), ('n',)]
HIRA = 'あいうえお かきくけこ さしすせそ たちつてと なにぬねの はひふへほ まみむめも や_ゆ_よ らりるれろ わ___を ん'.split()
KATA = 'アイウエオ カキクケコ サシスセソ タチツテト ナニヌネノ ハヒフヘホ マミムメモ ヤ_ユ_ヨ ラリルレロ ワ___ヲ ン'.split()
DAKU = [('が','ぎ','ぐ','げ','ご','ga gi gu ge go'), ('ざ','じ','ず','ぜ','ぞ','za ji zu ze zo'), ('だ','ぢ','づ','で','ど','da ji zu de do'),
        ('ば','び','ぶ','べ','ぼ','ba bi bu be bo'), ('ぱ','ぴ','ぷ','ぺ','ぽ','pa pi pu pe po')]
SMALL = [('ゃ','small ya'), ('ゅ','small yu'), ('ょ','small yo'), ('っ','small tsu (double consonant)')]

def table(kana, to_kata):
    conv = (lambda s: ''.join(chr(ord(c) + 0x60) for c in s)) if to_kata else (lambda s: s)
    out = []
    for row, rom in zip(kana, BASE):
        chars = [c for c in row if c != '_']
        romas = [r for r in rom if r]
        for c, r in zip(chars, romas):
            out.append((c, 'wo (o)' if r == 'wo' else r))
    for *cs, rom in DAKU:
        out += [(conv(c), r) for c, r in zip(cs, rom.split())]
    out += [(conv(c), r) for c, r in SMALL]
    return out

hira = table(HIRA, False)
kata = table([''.join(c) for c in KATA], True)
# the katakana table was typed as katakana already; the dakuten/small ones are converted from hiragana
hira_set = {c for c, _ in hira}
kata_set = {c for c, _ in kata}
pure = lambda w, allowed: len(w) >= 2 and all(c in allowed for c in w)

def words(allowed):
    seen, out = set(), []
    for w in J:
        forms = [x['text'] for x in w['kana'] if x['common']]
        if not forms or not w['sense']:
            continue
        form = forms[0]
        if form in seen or not pure(form, allowed):
            continue
        # a hiragana-only entry that is usually written in kanji is not a word to learn to write in kana
        if any(x['common'] for x in w['kanji']) and 'uk' not in {m for s in w['sense'] for m in s.get('misc', [])}:
            continue
        sn = w['sense'][0]
        pos, misc = set(sn.get('partOfSpeech', [])), set(sn.get('misc', []))
        if not (pos & {'n', 'adj-i', 'adj-na', 'adv'} or any(p.startswith('v') for p in pos)) or misc & {'sl', 'col', 'vulg', 'abbr', 'arch', 'derog', 'fam', 'id', 'chn', 'obsc', 'on-mim'}:
            continue
        if form[0] in 'ゃゅょっャュョッ' or 'っちゅ' in form:
            continue
        gloss = '; '.join(g['text'] for g in w['sense'][0]['gloss'][:2])
        if len(gloss) > 32 or '(' in gloss:
            continue
        seen.add(form); out.append((form, form, gloss))
    return out

def pick(c, ws):
    own = [w for w in ws if c in w[0] and len(w[0]) <= 4]
    # start with the kana, short first, other kana "easier" = earlier in the table
    own.sort(key=lambda w: (not w[0].startswith(c), abs(len(w[0]) - 3), w[0]))
    return [list(w) for w in own[:3]]

def strokes(c):
    url = f'https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{ord(c):05x}.svg'
    svg = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20).read().decode()
    return len(re.findall(r'<path[^>]*\sd="', svg))

deck = json.load(open(OUT))
deck = [x for x in deck if x['n'] <= 5]
hw, kw = words(hira_set), words(kata_set)
entries = [(c, r, 6, hw) for c, r in hira] + [(c, r, 7, kw) for c, r in kata]
with ThreadPoolExecutor(6) as ex:
    counts = list(ex.map(lambda e: strokes(e[0]), entries))
kana = [{'k': c, 'n': n, 's': s, 'm': [r], 'on': [], 'kun': [], 'w': pick(c, ws)} for (c, r, n, ws), s in zip(entries, counts)]
json.dump(kana + deck, open(OUT, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(kana), 'kana +', len(deck), 'kanji →', OUT, os.path.getsize(OUT) // 1024, 'KB; without words:', [x['k'] for x in kana if not x['w']])
