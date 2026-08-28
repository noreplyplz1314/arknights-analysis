# -*- coding: utf-8 -*-
"""生成「点击关系连线 → 两人关系详情」数据 relation_details.json

- archive: 干员档案/模组中互提的文本（优先展示）
- scenes:  共同经历的剧情幕（其次展示）
"""
import json, os, re
from collections import defaultdict

BASE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\relation_details.json'

with open(os.path.join(BASE, 'characters.json'), encoding='utf-8') as f:
    chars = json.load(f)
with open(r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\graph.json', encoding='utf-8') as f:
    graph = json.load(f)
with open(r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\name_mapping.json', encoding='utf-8') as f:
    mapping = json.load(f)
with open(r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\scene_dialogues.json', encoding='utf-8') as f:
    sc_data = json.load(f)['scenes']

node_names = {n['name'] for n in graph['nodes']}

# ====== 1. 别名表：节点名 -> 别名集合（档案文本可能用真名/代号互称） ======
alias_map = defaultdict(set)   # 节点名 -> {别名}
for nm in node_names:
    alias_map[nm].add(nm)

confirmed = mapping.get('confirmed', {}) or {}
for key, val in confirmed.items():
    if isinstance(val, dict):
        op = val.get('operator') or key
        rn = val.get('real_name') or key
    else:
        op = rn = key
    for nm in (op, rn, key):
        if nm in node_names:
            alias_map[nm].update([key, op, rn])
    # 反向：把别名归到存在的节点
    tgt = op if op in node_names else (rn if rn in node_names else (key if key in node_names else None))
    if tgt:
        alias_map[tgt].update([key, op, rn])

# ====== 2. 档案文本提取：节点名 -> [(source, text)] ======
def collect_char_texts(name):
    if name not in chars:
        return []
    c = chars[name]
    parts = []
    for a in c.get('archives', []) or []:
        if isinstance(a, dict) and a.get('text'):
            parts.append((a.get('title') or '档案', a['text']))
    for m in c.get('module_lore', []) or []:
        if isinstance(m, dict) and m.get('text'):
            parts.append((m.get('name') or '模组', m['text']))
    ad = c.get('archive_data') or {}
    if ad:
        parts.append(('档案数据', json.dumps(ad, ensure_ascii=False)))
    bi = c.get('basic_info') or {}
    if bi:
        parts.append(('基础信息', json.dumps(bi, ensure_ascii=False)))
    for f in ('item_description', 'trust_description'):
        if c.get(f):
            parts.append((f, c[f]))
    return parts

char_texts = {nm: collect_char_texts(nm) for nm in node_names}

# ====== 3. 句子提取：在文本中找提到某别名（长名优先）的句子 ======
_SENT_SPLIT = re.compile(r'[。！？!?；;\n]')
def find_mention_sentences(text, aliases, max_per_alias=2, max_total=4):
    """返回 [(alias, sentence)]"""
    out = []
    for alias in sorted(aliases, key=len, reverse=True):
        if not alias or len(alias) < 2:
            continue
        sents = [s.strip() for s in _SENT_SPLIT.split(text) if alias in s]
        # 去重
        seen = set()
        uniq = []
        for s in sents:
            if s not in seen and len(s) > 6:
                seen.add(s)
                uniq.append(s)
        for s in uniq[:max_per_alias]:
            out.append((alias, s))
        if len(out) >= max_total:
            break
    return out[:max_total]

# ====== 4. 对 graph 中每条边生成 archive 数据 ======
pairs = {}
docs_used = set()
link_count = len(graph['links'])
for li, l in enumerate(graph['links']):
    a, b = l['source'], l['target']
    if a not in node_names or b not in node_names:
        continue
    key = a + '|' + b if a < b else b + '|' + a
    if key in pairs:
        continue
    archive = []
    # A 的档案提到 B
    for src, txt in char_texts.get(a, []):
        for alias, sent in find_mention_sentences(txt, alias_map.get(b, {b})):
            archive.append({'from': a, 'to': b, 'source': src, 'text': sent[:110]})
            docs_used.add((a, src))
        if len(archive) >= 2:
            break
    # B 的档案提到 A
    for src, txt in char_texts.get(b, []):
        for alias, sent in find_mention_sentences(txt, alias_map.get(a, {a})):
            archive.append({'from': b, 'to': a, 'source': src, 'text': sent[:110]})
            docs_used.add((b, src))
        if len(archive) >= 4:
            break
    pairs[key] = {'archive': archive[:6], 'scenes': []}
    if li % 2000 == 0:
        print(f'  archive 进度 {li}/{link_count}')

print(f'archive 完成: {len(pairs)} 对')

# ====== 5. 共同经历：遍历所有幕，统计同场角色对 ======
pair_scenes = defaultdict(list)
for key, sc in sc_data.items():
    chs = [c for c in sc.get('characters', []) or [] if c in node_names]
    if len(chs) < 2:
        continue
    rec = {
        'key': key,
        'order': sc.get('order') or 0,
        'title': sc.get('title') or key,
        'segment': sc.get('segment') or '',
        'year': sc.get('year') or '',
        'location': sc.get('location') or '',
    }
    for i in range(len(chs)):
        for j in range(i + 1, len(chs)):
            a, b = chs[i], chs[j]
            k = a + '|' + b if a < b else b + '|' + a
            pair_scenes[k].append(rec)

# ====== 6. 合并到 pairs（仅保留 graph 边对，按 order 排序，截断） ======
for key in pairs:
    scenes = pair_scenes.get(key, [])
    scenes.sort(key=lambda s: s['order'])
    pairs[key]['scenes'] = scenes[:10]

# 统计
with_arc = sum(1 for v in pairs.values() if v['archive'])
with_scene = sum(1 for v in pairs.values() if v['scenes'])
print(f'总关系对: {len(pairs)} | 有档案关联: {with_arc} | 有共同经历: {with_scene}')

# ====== 7. 档案全文索引（供详情面板跳转） ======
docs = {}
for name, src in docs_used:
    docs.setdefault(name, [])
# 按 docs_used 收集完整档案文本
for name, src in docs_used:
    for s, txt in char_texts.get(name, []):
        if s == src:
            docs[name].append({'source': src, 'text': txt})
print(f'档案全文索引: {len(docs)} 个角色')

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump({'docs': docs, 'pairs': pairs}, f, ensure_ascii=False, indent=1)
print(f'已保存 {OUT}')
print(f'文件大小: {os.path.getsize(OUT)/1024:.0f} KB')
