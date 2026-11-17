"""Espace client Prêt à Poster : génère site/<slug>/ (index.html + media/) à partir d'un spec JSON.
Usage : python3 build_espace.py spec.json
"""
import json, os, shutil, sys, html, hashlib, datetime as dt
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(sys.argv[1]))
ROOT = os.path.join(HERE, 'site', spec['client']['slug'])
MED = os.path.join(ROOT, 'media')
if os.path.exists(MED): shutil.rmtree(MED)
os.makedirs(MED)


def add(src, thumb_w=None):
    ext = os.path.splitext(src)[1].lower()
    h = hashlib.md5(open(src, 'rb').read()).hexdigest()[:10]
    if ext in ('.jpg', '.jpeg', '.png'):
        name = f'{h}.jpg'
        if not os.path.exists(os.path.join(MED, name)):
            im = ImageOps.exif_transpose(Image.open(src))
            if im.mode in ('RGBA', 'LA', 'P'):
                im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (250, 246, 240)); bg.paste(im, mask=im.split()[-1]); im = bg
            im = im.convert('RGB')
            if max(im.size) > 1440: im.thumbnail((1440, 1920))
            im.save(os.path.join(MED, name), quality=88, optimize=True)
        return f'media/{name}'
    name = f'{h}{ext}'; shutil.copy(src, os.path.join(MED, name)); return f'media/{name}'


items = []
for it in spec['items']:
    it = dict(it)
    it['media'] = [{'file': add(m), 'video': m.lower().endswith('.mp4')} for m in it['media']]
    if it.get('cover'): it['poster'] = add(it['cover'])
    items.append(it)
items.sort(key=lambda i: i['date'])

# semaines (lundi)
weeks = {}
for it in items:
    d = dt.date.fromisoformat(it['date']); mon = d - dt.timedelta(days=d.weekday())
    weeks.setdefault(mon.isoformat(), []).append(it['id'])
MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']
wl = []
for k in sorted(weeks):
    d = dt.date.fromisoformat(k)
    wl.append({'id': k, 'label': f'Sem. du {d.day}{"er" if d.day == 1 else ""} {MOIS[d.month - 1]}', 'items': weeks[k]})

prof = dict(spec.get('profile', {}))
if prof.get('photo'): prof['photo'] = add(prof['photo'])
prof['covers'] = [{'label': c['label'], 'file': add(c['file'])} for c in prof.get('covers', [])]

data = {k: spec[k] for k in ('client', 'pack', 'contact', 'texts', 'extras') if k in spec}
data.update({'items': items, 'weeks': wl, 'profile': prof})
tpl = open(os.path.join(HERE, 'template.html')).read()
out = tpl.replace('/*DATA*/', 'const DATA = ' + json.dumps(data, ensure_ascii=False) + ';').replace('{{TITLE}}', html.escape(spec['client']['name']))
open(os.path.join(ROOT, 'index.html'), 'w').write(out)
for f in ('logo.svg', 'logo.png'):
    if os.path.exists(os.path.join(HERE, 'assets', f)): shutil.copy(os.path.join(HERE, 'assets', f), os.path.join(ROOT, f))
tot = sum(os.path.getsize(os.path.join(MED, f)) for f in os.listdir(MED))
print(ROOT, len(items), 'publications,', tot // 1024 // 1024, 'Mo')
