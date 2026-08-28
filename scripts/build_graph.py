"""
生成最终 graph.json：
- 节点：角色（干员/NPC），含阵营、对话量、出场幕数、关系密度、角色标签、异格关系
- 边：交互强度（对话交互 + 同幕共现）
- 节点重要性评分，支持核心/全量视图
"""
import json, os
from collections import Counter, defaultdict

BASE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30'

with open(os.path.join(BASE, 'characters.json'), encoding='utf-8') as f:
    characters = json.load(f)
with open(os.path.join(OUT, 'graph_interim.json'), encoding='utf-8') as f:
    interim = json.load(f)
with open(os.path.join(OUT, 'name_mapping.json'), encoding='utf-8') as f:
    mapping = json.load(f)

dialogue_count = interim['dialogue_count']
scene_count = interim['scene_count']
interaction = {tuple(k.split('|')): v for k, v in interim['interaction'].items()}
cooccur = {tuple(k.split('|')): v for k, v in interim['cooccur'].items()}

# ====== 节点筛选阈值 ======
# 全量视图：对话 >= 20
# 核心视图：评分 top 90
MIN_DIALOGUE_ALL = 20

# ====== 角色属性 ======
# 阵营
def get_faction(name):
    if name in characters:
        c = characters[name]
        bi = c.get('basic_info', {})
        fac = bi.get('faction', '')
        if fac:
            return fac
        aff = c.get('affiliation', {})
        if isinstance(aff, dict) and aff.get('main_faction'):
            return aff['main_faction']
        return '未知'
    # NPC 阵营推断（基于 name_mapping resolved + 领域知识）
    npc_factions = {
        '塔露拉': '整合运动', '特蕾西娅': '卡兹戴尔', '魏彦吾': '龙门',
        '霜星': '整合运动', '爱国者': '整合运动', '普瑞赛斯': '前文明',
        '曼弗雷德': '萨卡兹王庭', '血魔大君': '萨卡兹王庭', '变形者集群': '萨卡兹王庭',
        '特雷西斯': '萨卡兹王庭', '科西切': '乌萨斯', '黑蛇': '乌萨斯',
        '梅菲斯特': '整合运动', '浮士德': '整合运动', '碎骨': '整合运动',
        '米莎': '整合运动', '阿丽娜': '乌萨斯', '休露丝': '谢拉格',
        '伊雷妮': '叙拉古', '戈尔丁': '维多利亚', '薇尔丽芙': '拉特兰',
        '爱布拉娜': '塔拉', '白垩': '莱塔尼亚', '安多恩': '拉特兰',
        '克丽斯腾': '哥伦比亚', '博士': '罗德岛', 'PRTS': '罗德岛',
    }
    return npc_factions.get(name, '未知')

# 角色类型：干员 / NPC
def is_operator(name):
    return name in characters

# 异格关系
# 本体 -> 异格列表
alter_map = {}
for op in characters:
    # 提取括号内的异格标记
    if '(' in op and ')' in op:
        base = op.split('(')[0]
        alter_map.setdefault(base, []).append(op)

# 从 name_mapping confirmed 提取异格说明
alter_note = {}
for speaker, info in mapping['confirmed'].items():
    if info['operator'] in characters:
        op_data = characters[info['operator']]
        # 无额外操作

# ====== 关系边 ======
# 综合强度：交互（直接对话）+ 共现
# 归一化
links = {}
all_links = {}

for (a, b), cnt in interaction.items():
    if a == b:
        continue
    key = tuple(sorted([a, b]))
    if key not in all_links:
        all_links[key] = {'interact': 0, 'cooccur': 0}
    all_links[key]['interact'] += cnt

for (a, b), cnt in cooccur.items():
    if a == b:
        continue
    key = tuple(sorted([a, b]))
    if key not in all_links:
        all_links[key] = {'interact': 0, 'cooccur': 0}
    all_links[key]['cooccur'] += cnt

# ====== 全量节点 ======
all_nodes = {}
for name, dcnt in dialogue_count.items():
    if dcnt < MIN_DIALOGUE_ALL:
        continue
    if name in ('博士',):  # 博士特殊：保留，但标记玩家视角
        pass
    all_nodes[name] = {
        'name': name,
        'dialogue': dcnt,
        'scenes': scene_count.get(name, 0),
        'faction': get_faction(name),
        'operator': is_operator(name),
        'alters': alter_map.get(name, []),
    }

# ====== 计算节点重要性评分 ======
# score = 0.35*主线 + 0.25*支线 + 0.20*对话 + 0.10*关系 + 0.10*标签
# 简化实现：基于对话量、出场幕数、关系数
# 对话量 log 归一化
import math
max_dialogue = max(dialogue_count.values()) if dialogue_count else 1
max_scenes = max(scene_count.values()) if scene_count else 1

for name, node in all_nodes.items():
    dc = node['dialogue']
    sc = node['scenes']
    # 关系度：该节点参与的边数
    rel_degree = sum(1 for (a, b) in all_links if a == name or b == name)
    node['rel_degree'] = rel_degree
    
    # 评分
    d_score = math.log1p(dc) / math.log1p(max_dialogue)
    s_score = math.log1p(sc) / math.log1p(max_scenes)
    r_score = math.log1p(rel_degree) / math.log1p(max(rel_degree, 1))
    
    # 干员 + 0.05 基础加成；NPC 若对话高也给权重
    tag_bonus = 0.1 if node['operator'] else 0.02
    score = 0.40 * d_score + 0.25 * s_score + 0.25 * r_score + 0.10 * tag_bonus
    node['score'] = round(score, 4)

# ====== 核心节点 ======
core_names = sorted(all_nodes, key=lambda n: all_nodes[n]['score'], reverse=True)[:90]
core_set = set(core_names)

# ====== 构建边（同时覆盖核心节点） ======
edges = []
seen_edges = set()
for (a, b), vals in all_links.items():
    if a not in all_nodes or b not in all_nodes:
        continue
    # 边强度
    strength = vals['interact'] * 2 + vals['cooccur']
    edges.append({
        'source': a,
        'target': b,
        'interact': vals['interact'],
        'cooccur': vals['cooccur'],
        'strength': strength,
    })
edges.sort(key=lambda e: e['strength'], reverse=True)

print(f"全量节点: {len(all_nodes)}")
print(f"全量边: {len(edges)}")
print(f"核心节点: {len(core_set)}")

# ====== 导出 ======
graph = {
    'meta': {
        'title': '明日方舟 · 人物关系图谱',
        'version': '2026-08-23',
        'source': 'PRTS Wiki 剧情数据 + 角色身份映射表',
        'node_count_all': len(all_nodes),
        'edge_count_all': len(edges),
        'core_count': len(core_set),
    },
    'nodes': list(all_nodes.values()),
    'links': edges,
    'core_nodes': list(core_set),
    'alter_map': alter_map,
}

with open(os.path.join(OUT, 'graph.json'), 'w', encoding='utf-8') as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)

print("已保存 graph.json")

# ====== 输出核心节点列表 ======
print("\n=== 核心节点 TOP 40 ===")
for i, name in enumerate(core_names[:40], 1):
    n = all_nodes[name]
    t = '干员' if n['operator'] else 'NPC'
    print(f"  {i:2d}. {name:8s} [{t}] {n['faction']} | 评分{n['score']:.3f} | 对话{n['dialogue']} | 关系{n['rel_degree']}")
