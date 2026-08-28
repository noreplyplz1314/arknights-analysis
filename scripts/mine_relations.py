"""
数据挖掘：角色对话交互 + 同幕共现关系
应用 name_mapping 归一化，过滤群演，统计节点属性
"""
import json, os, re
from collections import Counter, defaultdict

BASE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30'

# ====== 加载数据 ======
with open(os.path.join(BASE, 'stories.json'), encoding='utf-8') as f:
    stories = json.load(f)
with open(os.path.join(BASE, 'characters.json'), encoding='utf-8') as f:
    characters = json.load(f)
with open(os.path.join(OUT, 'name_mapping.json'), encoding='utf-8') as f:
    mapping = json.load(f)

# ====== 构建归一化映射表 ======
# 说话者名 -> 归一化名（干员代号 或 保留原名）
normalize = {}

# 1. confirmed 映射：说话者名 -> 干员代号
for speaker, info in mapping['confirmed'].items():
    normalize[speaker] = info['operator']

# 2. high_confidence 中映射到干员且干员在角色库的
for speaker, info in mapping['high_confidence'].items():
    op = info['operator']
    if op in characters:
        normalize[speaker] = op

# 3. resolved 中特殊处理：
#    - 特蕾西娅 -> 特蕾西娅 (本体NPC，不映射到魔王)
#    - 塔露拉 -> 塔露拉 (独立NPC)
#    - 其余独立NPC保留原名
# 说话者名如果就是干员名，直接保留

# 角色库中所有干员名
all_ops = set(characters.keys())

# ====== 群演/功能性说话者过滤模式 ======
CROWD_PATTERNS = [
    '士兵', '成员', '干员', '市民', '居民', '村民', '骑士', '商人', '贵族',
    '工人', '员工', '难民', '感染者', '流民', '村民', '长老', '族长',
    '生物', '声音', '店主', '老板', '狱警', '卫兵', '守卫', '教徒', '修士',
    '教士', '游客', '记者', '演员', '观众', '粉丝', '船长', '船员', '水手',
    '军官', '战士', '佣兵', '忍者', '警察', '律师', '助手', '随从',
    '手下', '队长', '领队', '小孩', '孩子', '少女', '少年',
    '男人', '女人', '母亲', '父亲', '老人', '长者', '阿达克利斯', '萨卡兹',
    '维多利亚', '罗德岛', '龙门', '整合运动', '乌萨斯', '莱茵', '拉特兰',
    '深池', '巴别塔', '谢拉格', '卡西米尔', '莱塔尼亚', '哥伦比亚', '叙拉古',
    '萨尔贡', '伊比利亚', '阿戈尔', '萨米', '杜林', '玻利瓦尔',
    '？？？', '???', '旁白', '系统', '广播', '喇叭', '收音机', '电视',
    '提示音', '电子音', '机械音', '通讯', '无线电', '耳机',
    '人质', '犯人', '囚犯', '医生', '护士', '病人', '学生', '教师', '教授',
    '组长', '组长', '助理', '保安', '安保', '保镖', '打手', '混混', '黑帮',
    '赌场', '店员', '服务员', '厨师', '伙计', '管家', '侍女', '司机',
    '驮兽', '动物', '怪物', '机械', '装置', '无人机', '磐蟹', '源石虫',
    '恐鱼', '海嗣', '感染生物', '幻影', '回音', '低语',
    # 追加群演（经语境核实）
    '经理', '镇民', '猎人', '首领', '线人', '议员', '患者', '代表',
    '摊贩', '刺客', '密探', '幼童', '孩子', '歌迷', '山雪鬼', '拓荒队',
]

# 更激进的过滤：纯描述性说话者（无专名特征）
def is_crowd(name):
    """判断是否为群演/功能性说话者"""
    if name in ('博士', 'PRTS', 'Mon3tr', 'Miss.Christine', 'Castle-3', 'Lancet-2', 'THRM-EX', 'Friston-3'):
        return False
    if len(name) <= 1:
        return True
    # 描述性前缀（形容词+名词）
    if re.match(r'^(冷静|沉稳|紧张|愤怒|恐惧|疑惑|惊讶|焦急|疲惫|慌乱|温柔|严肃|兴奋|好奇|坚定|低沉|陌生|熟悉|年轻|年老|受伤|强壮|虚弱|冷漠|热情|平静|颤抖|遥远|神秘|高大|魁梧|文静|温柔|警觉|暴躁|恭敬|慌张|恐惧|吃惊|绝望|犹豫|果断|开心|悲伤|哭泣|微笑|沉默|惊愕|欣慰|激动|忐忑|彷徨|迟疑|焦急|麻木|冷淡|沙哑|浑厚|刺耳|轻柔|悠扬|得意|谦逊|傲慢|羞涩|腼腆|豪爽|谨慎|警惕|疲惫|困惑|迷茫|疯狂|歇斯底里)[^，。]{2,6}$', name):
        return True
    # 常见群演名词模式
    for p in CROWD_PATTERNS:
        if p in name:
            return True
    # 带数字编号的
    if re.search(r'[A-E]$', name) and len(name) <= 8:
        return True
    return False

# ====== 统计 ======
dialogue_count = Counter()       # 每个角色的对话量
scene_count = Counter()          # 每个角色出场的幕数
scene_chars = defaultdict(set)   # 每幕的角色集合
char_stories = defaultdict(set)  # 每个角色出现的剧目

# 对话交互：同一幕内相邻对话的 speaker->next_speaker
interaction = Counter()          # (speaker, target) -> 次数
cooccur = Counter()              # (a, b) 同幕共现次数

for story in stories:
    dialogues = story.get('dialogues', [])
    scene_key = story.get('title') or story.get('page_id')
    chars_in_scene = set()
    
    for i, d in enumerate(dialogues):
        raw = (d.get('speaker') or '').strip()
        if not raw or raw in ('？？？', '???', '……', '...', '—'):
            continue
        # 归一化
        name = normalize.get(raw, raw)
        if name in all_ops:
            canonical = name
        elif raw in all_ops:
            canonical = raw
        else:
            canonical = name
        # 过滤群演
        if is_crowd(canonical):
            continue
        dialogue_count[canonical] += 1
        chars_in_scene.add(canonical)
        
        # 对话交互：下一条有名字的对话者
        for j in range(i+1, min(i+5, len(dialogues))):
            nxt_raw = (dialogues[j].get('speaker') or '').strip()
            if not nxt_raw or nxt_raw in ('？？？', '???', '……', '...', '—'):
                continue
            nxt = normalize.get(nxt_raw, nxt_raw)
            if nxt in all_ops:
                nxt_c = nxt
            elif nxt_raw in all_ops:
                nxt_c = nxt_raw
            else:
                nxt_c = nxt
            if nxt_c != canonical and not is_crowd(nxt_c):
                interaction[(canonical, nxt_c)] += 1
            break  # 只取下一个说话者
    
    # 共现：同幕内两两组合
    chars_in_scene = [c for c in chars_in_scene if not is_crowd(c)]
    for c in chars_in_scene:
        scene_count[c] += 1
    chars_list = sorted(chars_in_scene)
    for i in range(len(chars_list)):
        for j in range(i+1, len(chars_list)):
            cooccur[(chars_list[i], chars_list[j])] += 1

# ====== 筛选节点：至少 15 次对话 或 有名字的重要角色 ======
# 保留所有 >=15 次对话的
min_dialogue = 15
core_speakers = {n for n, c in dialogue_count.items() if c >= min_dialogue}

# 补充：干员库中在剧情出现过的（即使对话少）
# 从 role库 + 对话过滤出

# 补充一些明确重要但对话较少的角色（如 W 的异格维什戴尔等已在库）
print(f"总角色(归一化后): {len(dialogue_count)}")
print(f"核心角色(对话>=15): {len(core_speakers)}")
print(f"总对话交互对数: {len(interaction)}")
print(f"总共现对数: {len(cooccur)}")

# ====== 保存中间数据 ======
result = {
    'dialogue_count': {k: v for k, v in dialogue_count.items()},
    'scene_count': {k: v for k, v in scene_count.items()},
    'interaction': {f'{k[0]}|{k[1]}': v for k, v in interaction.items()},
    'cooccur': {f'{k[0]}|{k[1]}': v for k, v in cooccur.items()},
}
with open(os.path.join(OUT, 'graph_interim.json'), 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("已保存 graph_interim.json")

# ====== 输出 top 角色 ======
print("\n=== TOP 30 角色（按对话量） ===")
for name, count in dialogue_count.most_common(30):
    scenes = scene_count.get(name, 0)
    print(f"  {name:10s} | 对话{count:4d} | 出场{scenes:3d}幕")
