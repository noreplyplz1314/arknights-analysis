"""
从角色库档案文本中挖掘说话者名 → 干员的映射证据
对每个高频说话者名，搜索所有干员的文本字段（module_lore/archives/item_description等）
如果某个干员文本中出现了这个说话者名，则记录为候选映射
"""
import json, os, re
from collections import Counter, defaultdict

base = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'

with open(os.path.join(base, 'characters.json'), encoding='utf-8') as f:
    characters = json.load(f)
with open(os.path.join(base, 'stories.json'), encoding='utf-8') as f:
    stories = json.load(f)

# ====== 说话者统计（>10次）======
speakers = Counter()
for s in stories:
    for d in s.get('dialogues', []):
        sp = d.get('speaker', '').strip()
        if sp and sp not in ('???', '？？？', '', '—', '...', '……'):
            speakers[sp] += 1

# 关注：不在角色库key中、且不是明显群演的高频说话者
skip_patterns = [
    '成员', '士兵', '干员', '市民', '居民', '村民', '骑士', '商人', '贵族',
    '工人', '员工', '难民', '感染者', '流民', '村民', '长老', '族长', '神',
    '生物', '声音', '店主', '老板', '狱警', '卫兵', '守卫', '教徒', '修士',
    '教士', '游客', '记者', '演员', '观众', '粉丝', '船长', '船员', '水手',
    '军官', '士兵', '战士', '佣兵', '忍者', '警察', '律师', '助手', '随从',
    '手下', '队长', '领队', '成员A', '成员B', '小孩', '孩子', '少女', '少年',
    '男人', '女人', '母亲', '父亲', '老人', '长者', '阿达克利斯', '萨卡兹',
    '维多利亚', '罗德岛', '龙门', '整合运动', '乌萨斯', '莱茵', '拉特兰',
    '深池', '巴别塔', '谢拉格', '卡西米尔', '莱塔尼亚', '哥伦比亚', '叙拉古',
    '萨尔贡', '伊比利亚', '阿戈尔', '萨米', '杜林', '玻利瓦尔', '海洋',
]

def is_crowd(name):
    for p in skip_patterns:
        if p in name:
            return True
    return False

# 候选说话者：非群演、不在角色库、>10次
candidates = [(n, c) for n, c in speakers.items() 
              if n not in characters and not is_crowd(n) and c >= 10 
              and n not in ('???', '？？？')]
print(f"候选说话者（非群演、不在角色库、>=10次）: {len(candidates)}")

# ====== 在角色库文本中搜索 ======
# 收集每个干员的全文本
op_texts = {}
for op_name, op_data in characters.items():
    texts = []
    for field in ('module_lore', 'archives', 'item_description', 'trust_description', 'archive_data'):
        val = op_data.get(field)
        if isinstance(val, str):
            texts.append(val)
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict):
                    texts.extend(str(v) for v in item.values() if isinstance(v, str))
        elif isinstance(val, dict):
            texts.extend(str(v) for v in val.values() if isinstance(v, str))
    op_texts[op_name] = ' '.join(texts)

# 对每个候选说话者，找包含它的干员
mapping_evidence = {}
for name, count in candidates:
    hits = []
    for op_name, op_text in op_texts.items():
        if name in op_text:
            hits.append(op_name)
    mapping_evidence[name] = {'count': count, 'hits': hits}

# 输出
print("\n=== 有映射证据的说话者（在干员文本中出现） ===")
for name, info in sorted(mapping_evidence.items(), key=lambda x: -x[1]['count']):
    hits = info['hits']
    if hits:
        # 优先显示包含次数最多的
        print(f"  {name} ({info['count']}次) → {hits[:3]}{'...' if len(hits)>3 else ''}")

print("\n=== 无映射证据的说话者（需要PRTS或用户判断） ===")
no_evidence = [(n, i) for n, i in mapping_evidence.items() if not i['hits']]
print(f"  共 {len(no_evidence)} 个:")
for name, info in sorted(no_evidence, key=lambda x: -x[1]['count']):
    print(f"  {name} ({info['count']}次)")

# 保存
with open(r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\mapping_evidence.json', 'w', encoding='utf-8') as f:
    json.dump({'evidence': mapping_evidence}, f, ensure_ascii=False, indent=2)
print(f"\n已保存 mapping_evidence.json")
