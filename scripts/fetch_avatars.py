# -*- coding: utf-8 -*-
"""批量获取 PRTS 头像 URL，生成 avatars.json
头像文件规则：文件:头像_<角色名>.png（PRTS wiki）
对干员/剧情角色逐个查询 imageinfo 拿真实 URL；不存在的记为 missing（前端用占位）。
"""
import json, os, time, urllib.request, urllib.parse

ROOT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30'
GRAPH_PATH = os.path.join(ROOT, 'graph.json')
CHAR_PATH = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json\characters.json'
OUT_PATH = os.path.join(ROOT, 'arknights-graph', 'avatars.json')

with open(GRAPH_PATH, encoding='utf-8') as f:
    graph = json.load(f)
with open(CHAR_PATH, encoding='utf-8') as f:
    characters = json.load(f)

# 收集角色名：graph 节点 + characters 干员
names, seen = [], set()
for n in graph['nodes']:
    if n['name'] not in seen:
        seen.add(n['name']); names.append(n['name'])
for name in characters:
    if name not in seen:
        seen.add(name); names.append(name)

print(f'需查询角色: {len(names)}')

BATCH = 40
avatars, missing = {}, []

def api_get(titles):
    url = ('https://prts.wiki/api.php?action=query&titles=' +
           urllib.parse.quote(titles) + '&prop=imageinfo&iiprop=url&format=json')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://prts.wiki/'
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

for i in range(0, len(names), BATCH):
    batch = names[i:i + BATCH]
    titles = '|'.join('文件:头像_' + n for n in batch)
    try:
        data = api_get(titles)
        for pid, p in data.get('query', {}).get('pages', {}).items():
            fname = p['title'].replace('文件:头像_', '')
            ii = p.get('imageinfo')
            if ii:
                avatars[fname] = ii[0]['url']
            else:
                missing.append(fname)
    except Exception as e:
        print(f'  batch {i} error: {e}')
        missing.extend(batch)
    time.sleep(0.25)
    if (i // BATCH) % 10 == 0:
        print(f'  进度 {min(i+BATCH, len(names))}/{len(names)}，已找到 {len(avatars)}')

result = {'count': len(avatars), 'total': len(names), 'avatar': avatars, 'missing': missing}
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print(f'完成：找到头像 {len(avatars)}/{len(names)}，缺失 {len(missing)}')
print('缺失示例:', missing[:15])
