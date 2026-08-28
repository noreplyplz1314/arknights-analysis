import json, re

MD = "C:/Users/Administrator/Doubao/chats/2026-08-26/new-chat/明日方舟全登场角色人物档案.md"
G = "graph.json"

def norm(s):
    s = (s or '').strip()
    s = re.sub(r'[（(][^）)]*[）)]', '', s)   # 去除括号注解
    s = s.replace(' ', '').replace('　', '').replace('/', '')
    return s

text = open(MD, encoding='utf-8').read()
parts = re.split(r'(?m)^## ', text)   # 第一个元素为前言
chars = {}          # char_key -> {aliases:set, doctor:str, rels:{normname:desc}}
alias2char = {}     # norm(alias) -> char_key

for p in parts[1:]:
    lines = p.split('\n')
    header = lines[0].strip()
    # 角色显示名：去掉行首 "N. "
    m = re.match(r'^\d+\.\s*(.+)$', header)
    disp = m.group(1) if m else header
    key = disp
    c = {'aliases': set(), 'doctor': '', 'rels': {}}
    c['aliases'].add(disp)
    body = '\n'.join(lines[1:])
    # 姓名
    mm = re.search(r'- \*\*姓名\*\*：\s*(.+)', body)
    if mm:
        nm = mm.group(1).strip()
        if nm and nm != '未知':
            c['aliases'].add(nm)
    # 代号（可能 A / B）
    mm = re.search(r'- \*\*代号\*\*：\s*(.+)', body)
    if mm:
        for tok in re.split(r'[/／]', mm.group(1)):
            tok = tok.strip()
            if tok:
                c['aliases'].add(tok)
    # 与博士关系
    mm = re.search(r'- \*\*与博士关系\*\*：\s*(.*)', body)
    if mm:
        c['doctor'] = mm.group(1).strip()
    # 与重要剧情人物关系：收集其后缩进 bullet，直到下一个字段或分隔
    mm = re.search(r'- \*\*与重要剧情人物关系\*\*：(.*?)(?=\n- \*\*|\n---|\Z)', body, re.S)
    if mm:
        block = mm.group(1)
        for bl in block.split('\n'):
            bl = bl.strip()
            if not bl.startswith('-'):
                continue
            bl = bl[1:].strip()
            if '：' in bl:
                name, desc = bl.split('：', 1)
            elif ':' in bl:
                name, desc = bl.split(':', 1)
            else:
                continue
            name = name.strip(); desc = desc.strip()
            if name and desc:
                c['rels'][norm(name)] = desc
    chars[key] = c
    for a in c['aliases']:
        na = norm(a)
        if na:
            alias2char.setdefault(na, key)

# 载入 graph
g = json.load(open(G, encoding='utf-8'))
gnames = set(n['name'] for n in g['nodes'])

def char_of(graphname):
    return alias2char.get(norm(graphname))

def desc_for(A, B):
    ca = char_of(A); cb = char_of(B)
    if ca is not None:
        d = chars[ca]['rels'].get(norm(B))
        if d: return d
    if cb is not None:
        d = chars[cb]['rels'].get(norm(A))
        if d: return d
    # 涉及博士：取另一方「与博士关系」
    if norm(A) == '博士' and cb is not None and chars[cb]['doctor']:
        return chars[cb]['doctor']
    if norm(B) == '博士' and ca is not None and chars[ca]['doctor']:
        return chars[ca]['doctor']
    return None

enriched = 0
for l in g['links']:
    rel = l.get('relation') or '关联'
    # 所有关系类型都尝试用 md 抽取具体描述；有则写 rel_desc（标签优先显示），无则留空
    # （同阵营/跨阵营 若无 md 具体描述则由前端默认屏蔽；有则显示真实关系）
    d = desc_for(l['source'], l['target'])
    if d:
        l['rel_desc'] = d
        enriched += 1
    else:
        l.pop('rel_desc', None)

json.dump(g, open(G, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('md chars parsed:', len(chars))
print('alias->char entries:', len(alias2char))
print('concrete/剧情关联 links enriched with rel_desc:', enriched)
# 抽样
sample = [l for l in g['links'] if l.get('rel_desc')][:4]
for l in sample:
    print(f"  {l['source']} --[{l['relation']}]--> {l['target']}: {l['rel_desc'][:40]}")
