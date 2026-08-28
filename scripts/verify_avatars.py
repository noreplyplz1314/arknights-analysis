# -*- coding: utf-8 -*-
"""通过 MD5 哈希路径直接构造 PRTS 头像 URL 并并发验证存在性。
规则：文件名=头像_<角色名>.png，media 路径 = /<md5[0]>/<md5[0:2]>/<文件名>
CDN 直连不受 prts.wiki WAF 影响。
"""
import json, os, hashlib, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30'
GRAPH_PATH = os.path.join(ROOT, 'graph.json')
CHAR_PATH = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json\characters.json'
OUT_PATH = os.path.join(ROOT, 'arknights-graph', 'avatars.json')

with open(GRAPH_PATH, encoding='utf-8') as f:
    graph = json.load(f)
with open(CHAR_PATH, encoding='utf-8') as f:
    characters = json.load(f)

names, seen = [], set()
for n in graph['nodes']:
    if n['name'] not in seen:
        seen.add(n['name']); names.append(n['name'])
for name in characters:
    if name not in seen:
        seen.add(name); names.append(name)

print(f'候选角色: {len(names)}')

def avatar_url(name):
    fn = '头像_' + name + '.png'
    h = hashlib.md5(fn.encode('utf-8')).hexdigest()
    return 'https://media.prts.wiki/{}/{}/{}'.format(h[0], h[0:2], urllib.parse.quote(fn))

def check(name):
    url = avatar_url(name)
    try:
        req = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status == 200:
                return name, url
    except Exception:
        pass
    return name, None

results = {}
missing = []
with ThreadPoolExecutor(max_workers=16) as ex:
    for i, (name, url) in enumerate(ex.map(check, names), 1):
        if url:
            results[name] = url
        else:
            missing.append(name)
        if i % 200 == 0:
            print(f'  进度 {i}/{len(names)}，命中 {len(results)}')

result = {'count': len(results), 'total': len(names), 'avatar': results, 'missing': missing}
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print(f'完成：头像 {len(results)}/{len(names)}，缺失 {len(missing)}')
print('缺失示例:', missing[:15])
