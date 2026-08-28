# -*- coding: utf-8 -*-
"""对缺失头像的角色尝试第二候选：头像_敌人_<名>.png"""
import json, os, hashlib, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30'
AV_PATH = os.path.join(ROOT, 'arknights-graph', 'avatars.json')

with open(AV_PATH, encoding='utf-8') as f:
    av = json.load(f)
missing = [n for n in av['missing'] if n not in av['avatar']]

def candidate_url(name):
    fn = '头像_敌人_' + name + '.png'
    h = hashlib.md5(fn.encode('utf-8')).hexdigest()
    return 'https://media.prts.wiki/{}/{}/{}'.format(h[0], h[0:2], urllib.parse.quote(fn))

def check(name):
    url = candidate_url(name)
    try:
        req = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status == 200:
                return name, url
    except Exception:
        pass
    return name, None

found = {}
still_missing = []
with ThreadPoolExecutor(max_workers=16) as ex:
    for name, url in ex.map(check, missing):
        if url:
            found[name] = url
        else:
            still_missing.append(name)

for name, url in found.items():
    av['avatar'][name] = url
av['missing'] = still_missing
av['count'] = len(av['avatar'])

with open(AV_PATH, 'w', encoding='utf-8') as f:
    json.dump(av, f, ensure_ascii=False, indent=1)

print(f'敌人头像补命中: {len(found)}')
print('补命中示例:', list(found.items())[:10])
print(f'现在总数: {av["count"]}/{av["total"]}，仍缺失 {len(still_missing)}')
print('仍缺失(核心):', [n for n in still_missing if n in set(json.load(open(os.path.join(ROOT,"graph.json"),encoding="utf-8"))["core_nodes"])])
