# -*- coding: utf-8 -*-
"""图谱数据增强：
1. 补全节点阵营（核心节点当前有 8 个"未知"）
2. 为节点生成简介 profile（干员取"客观履历"，NPC 手写/由 resolved 生成）
3. 为边标注关系 relation（手工核心关系对 + 阵营规则兜底）
输出：arknights-graph/graph.json（前端使用）+ 根目录 graph.json
"""
import json, os, re
from collections import Counter

GRAPH_PATH = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\graph.json'
OUT_PATH = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\graph.json'
BASE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'

with open(os.path.join(BASE, 'characters.json'), encoding='utf-8') as f:
    characters = json.load(f)
with open(r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\name_mapping.json', encoding='utf-8') as f:
    mapping = json.load(f)
with open(GRAPH_PATH, encoding='utf-8') as f:
    graph = json.load(f)

# ============================================================
# 1. 阵营补全
# ============================================================
EXTRA_FACTIONS = {
    '“灰礼帽”': '罗德岛', '阿洛伊泽': '乌萨斯', '菈塔托丝': '谢拉格',
    '阿克托斯': '谢拉格', '斐尔迪南': '哥伦比亚', '卡彭': '叙拉古',
    '麟青砚': '炎', '大嘴莫布': '龙门',
    # 谢拉格
    '尤卡坦': '谢拉格', '锏': '谢拉格',
    # 乌萨斯
    '费奥多尔': '乌萨斯', '奥列格': '乌萨斯', '维特': '乌萨斯',
    '赫拉格': '乌萨斯', '罗莎琳': '乌萨斯',
    # 叙拉古
    '拉维妮娅': '叙拉古', '莱昂图索': '叙拉古', '德米特里': '叙拉古',
    '贝纳尔多': '叙拉古', '卢比奥': '叙拉古', '斯克里普': '叙拉古',
    # 罗德岛 / 巴别塔
    '明椒': '罗德岛', '阿斯卡纶': '罗德岛', 'Logos': '罗德岛',
    '逻各斯': '罗德岛', 'Misery': '罗德岛', 'Outcast': '罗德岛',
    'Scout': '罗德岛', 'Ace': '罗德岛', 'ACE': '罗德岛', '杜宾': '罗德岛',
    '煌': '罗德岛', '迷迭香': '罗德岛', '极境': '罗德岛', '灰喉': '罗德岛',
    '暴行': '罗德岛', '可露希尔': '罗德岛', '华法琳': '罗德岛', '陈': '龙门',
    # 维多利亚
    '赫德雷': '维多利亚', '伊内丝': '维多利亚', '号角': '维多利亚',
    '风笛': '维多利亚', '推进之王': '维多利亚', '维娜': '维多利亚',
    '达格达': '维多利亚', '琴柳': '维多利亚', '海蒂': '维多利亚',
    # 塔拉 / 深池
    '苇草': '塔拉', '拉芙希妮': '塔拉', '爱布拉娜': '塔拉',
    # 深海猎人 / 伊比利亚 / 阿戈尔
    '乌尔比安': '深海猎人', '歌蕾蒂娅': '深海猎人', '劳伦缇娜': '深海猎人',
    '安哲拉': '深海猎人', '斯卡蒂': '深海猎人', '格拉尼': '深海猎人',
    '艾丽妮': '伊比利亚', '布兰都斯': '阿戈尔',
    # 哥伦比亚 / 莱茵
    '克丽斯腾': '哥伦比亚', '塞雷娅': '哥伦比亚', '赫默': '哥伦比亚',
    '缪尔赛思': '哥伦比亚', '多萝西': '哥伦比亚', '星源': '哥伦比亚',
    '埃琳娜': '哥伦比亚',
    # 拉特兰
    '安多恩': '拉特兰', '阿尔图罗': '拉特兰', '费德里科': '拉特兰',
    '莫斯提马': '拉特兰', '菲亚梅塔': '拉特兰', '能天使': '拉特兰',
    '塞茜莉亚': '拉特兰', '奥莉维亚': '拉特兰',
    # 龙门 / 炎
    '魏彦吾': '龙门', '林雨霞': '龙门', '鼠王': '龙门',
    '德克萨斯': '龙门', '拉普兰德': '叙拉古', '罗德岛': '罗德岛',
    '陈晖洁': '龙门',
    # 整合运动
    '塔露拉': '整合运动', '霜星': '整合运动', '爱国者': '整合运动',
    '梅菲斯特': '整合运动', '浮士德': '整合运动', '碎骨': '整合运动',
    '米莎': '整合运动', '弑君者': '整合运动', '柳德米拉': '整合运动',
    '雪怪小队': '整合运动', '游击队': '整合运动',
    # 卡兹戴尔 / 萨卡兹
    '特蕾西娅': '卡兹戴尔', '特雷西斯': '卡兹戴尔', 'W': '罗德岛',
    '维什戴尔': '罗德岛', '爱布拉娜': '塔拉',
    # 前文明 / 乌萨斯
    '普瑞赛斯': '前文明', '科西切': '乌萨斯', '黑蛇': '乌萨斯',
    # 谢拉格
    '银灰': '谢拉格', '恩希欧迪斯': '谢拉格', '初雪': '谢拉格',
    '恩雅': '谢拉格', '灵知': '谢拉格', '诺希斯': '谢拉格',
    '崖心': '谢拉格', '角峰': '谢拉格', '讯使': '谢拉格',
    # 卡西米尔
    '玛嘉烈': '卡西米尔', '玛莉娅': '卡西米尔', '佐菲娅': '卡西米尔',
    '索娜': '卡西米尔', '格蕾纳蒂': '卡西米尔', '艾沃娜': '卡西米尔',
    '耀骑士': '卡西米尔', '瑕光': '卡西米尔', '鞭刃': '卡西米尔',
    # 莱塔尼亚
    '白垩': '莱塔尼亚', '黑键': '莱塔尼亚', '阿黛尔': '莱塔尼亚',
    '艾雅法拉': '莱塔尼亚',
    # 萨尔贡
    '卡涅利安': '萨尔贡', '埃塞亚斯': '萨尔贡',
    # 博士等
    '博士': '罗德岛', '凯尔希': '罗德岛', '阿米娅': '罗德岛', 'PRTS': '罗德岛',
    # 高频 NPC 补充
    '阿勒黛': '维多利亚', '克洛维希娅': '维多利亚',
    '梁洵': '炎', '萌萌香': '炎', '老鲤': '炎', '宁辞秋': '炎',
    '埃内斯托': '玻利瓦尔', '拉菲艾拉': '玻利瓦尔', '坎黛拉': '玻利瓦尔', '潘乔': '玻利瓦尔',
    '审判官艾丽妮': '伊比利亚', '大审判官': '伊比利亚', '胡安娜': '伊比利亚',
    '塞弗林': '莱塔尼亚', '甘比诺': '叙拉古', '瓦拉赫': '叙拉古', '卢奇诺': '叙拉古',
    '学者猫': '萨尔贡',
}

def resolve_faction(name):
    # 1. 角色库
    if name in characters:
        c = characters[name]
        bi = c.get('basic_info', {})
        fac = bi.get('faction', '') or (c.get('affiliation', {}) or {}).get('main_faction', '')
        if fac:
            return fac
    # 2. 手工字典
    if name in EXTRA_FACTIONS:
        return EXTRA_FACTIONS[name]
    # 3. resolved（用户判定 NPC）
    if name in mapping.get('resolved', {}):
        r = mapping['resolved'][name]
        if r.get('faction'):
            f = r['faction'].split('/')[0].strip()
            return f
        if r.get('identity'):
            for key in FACTION_HINTS:
                if key in r['identity']:
                    return FACTION_HINTS[key]
    # 4. confirmed 真名 -> 干员 -> 阵营
    for speaker, info in mapping.get('confirmed', {}).items():
        if speaker == name:
            op = info.get('operator', '')
            if op in characters:
                c = characters[op]
                fac = c.get('basic_info', {}).get('faction', '') or (c.get('affiliation', {}) or {}).get('main_faction', '')
                if fac:
                    return fac
    return None

FACTION_HINTS = {
    '萨卡兹': '卡兹戴尔', '卡兹戴尔': '卡兹戴尔', '罗德岛': '罗德岛',
    '乌萨斯': '乌萨斯', '谢拉格': '谢拉格', '叙拉古': '叙拉古',
    '维多利亚': '维多利亚', '拉特兰': '拉特兰', '哥伦比亚': '哥伦比亚',
    '龙门': '龙门', '炎': '炎', '莱塔尼亚': '莱塔尼亚',
    '卡西米尔': '卡西米尔', '萨尔贡': '萨尔贡', '伊比利亚': '伊比利亚',
    '阿戈尔': '阿戈尔', '前文明': '前文明', '塔拉': '塔拉',
}

faction_fixed = 0
for n in graph['nodes']:
    if n['faction'] == '未知':
        new = resolve_faction(n['name'])
        if new:
            n['faction'] = new
            faction_fixed += 1

# ============================================================
# 2. 节点简介 profile
# ============================================================
def build_operator_profile(name):
    c = characters.get(name, {})
    for a in c.get('archives', []):
        if a.get('title') == '客观履历':
            text = re.sub(r'\s+', ' ', a.get('text', '')).strip()
            if text:
                return text[:130] + ('…' if len(text) > 130 else '')
    bi = c.get('basic_info', {})
    aff = c.get('affiliation', {}) or {}
    fac = bi.get('faction', '') or aff.get('main_faction', '')
    cls = bi.get('class', '') or bi.get('branch', '')
    race = ''
    for a in c.get('archives', []):
        if a.get('title') == '基础档案':
            m = re.search(r'【种族】(.+)', a.get('text', ''))
            if m:
                race = m.group(1).strip().split('\n')[0]
    parts = [f'{name}是{fac}干员' if fac else f'{name}是罗德岛相关干员']
    if race:
        parts.append(f'{race}族')
    if cls:
        parts.append(f'职业{cls}')
    return '，'.join(parts) + '。'

NPC_PROFILES = {
    '博士': '罗德岛战术指挥官，失忆者。1096年12月自切尔诺伯格石棺苏醒。曾是巴别塔战术核心（"恶灵"），与特蕾西娅、凯尔希、普瑞赛斯有复杂过去。',
    '塔露拉': '旧整合运动领袖，德拉克族，科西切（黑蛇）曾经的容器。主导切尔诺伯格事变，EP8被罗德岛击败并羁押。与陈为姐妹。',
    '特蕾西娅': '卡兹戴尔魔王、巴别塔领袖。1094年遇刺身亡，临终将黑王冠传承给阿米娅；慈悲灯塔中人格彻底消散。',
    '普瑞赛斯': '前文明人类，源石项目相关。EP15苏醒后操控PRTS夺取罗德岛控制权，与博士为前文明旧识。',
    '曼弗雷德': '萨卡兹王庭军/军事委员会高级指挥官，特雷西斯麾下。伦蒂尼姆围城战重要将领，结局战败被俘。',
    '血魔大君': '萨卡兹鲜血王庭之主，真名杜卡雷。伦蒂尼姆核心BOSS，结局坠入时空乱流，留有回归伏笔。',
    '变形者集群': '萨卡兹变形者王庭成员，蜂巢式集群意识，无固定人格。结局分裂为两大意识分支。',
    '霜星': '整合运动雪怪小队队长。EP7在切尔诺伯格战斗中殒命，临终选择加入罗德岛。',
    '爱国者': '乌萨斯最后一位温迪戈，真名博卓卡斯替。EP7战死，与凯尔希有旧怨。',
    '魏彦吾': '龙门实际控制者，陈的舅舅。曾许诺教陈赤霄剑术，与科西切、龙门各方势力周旋。',
    '特雷西斯': '萨卡兹摄政王，特蕾西娅之兄。发动巴别塔覆灭与伦蒂尼姆事变，萨卡兹王庭的实际掌控者。',
    '科西切': '乌萨斯公爵，被称为"不死的黑蛇"。曾附身塔露拉，操控整合运动走向毁灭。',
    '梅菲斯特': '整合运动干部，真名伊诺。浮士德死后彻底崩溃，龙门篇逐渐疯狂。',
    '浮士德': '整合运动干部，真名萨沙，梅菲斯特的挚友。EP6为掩护同伴殒命。',
    '弑君者': '整合运动干部，真名柳德米拉。曾是叙拉古杀手组织成员，与罗德岛多次交手。',
    '碎骨': '整合运动干部，米莎之兄。龙门篇率队袭击罗德岛。',
    '米莎': '切尔诺伯格少女，碎骨之妹。龙门篇悲剧核心，身份被整合运动利用。',
    '阿丽娜': '乌萨斯感染者，塔露拉在整合运动的挚友与精神支柱，已故。',
    '休露丝': '谢拉格布朗陶家族二女，菈塔托丝之妹、尤卡坦之妻。风雪过境/银心湖列车登场。',
    '菈塔托丝': '谢拉格布朗陶家族长女与实权者，家族事务的实际掌控人。风雪过境/银心湖列车中与恩希欧迪斯（银灰）为首的希瓦艾什家族展开政治博弈。',
    '伊雷妮': '叙拉古新沃尔西尼卡车司机互助会会长，揭幕者们登场。',
    '戈尔丁': '维多利亚伦蒂尼姆圣马尔索学校教师，海蒂旧识。主线第11-12章登场，剧情中已自杀。',
    '薇尔丽芙': '拉特兰公证所官员，菲亚梅塔的上级。',
    '费奥多尔': '乌萨斯年轻政治家/改革派，第17章核心线索人物（费佳）。与兄长、阿洛伊泽等构成乌萨斯内乱线。',
    '阿洛伊泽': '乌萨斯角色，第16-17章登场，与费奥多尔（费佳）相关。',
    '“灰礼帽”': '萨卡兹雇佣兵的旧行动代号，活跃于切尔诺伯格与伦蒂尼姆剧情线，与 W 关联密切。',
    '麟青砚': '大炎司岁台相关角色，活跃于炎国岁相线（画中人/将进酒/登临意），与"岁"的碎片们关联。',
    '阿克托斯': '谢拉格希瓦艾什家族亲信，风雪过境登场，辅佐恩希欧迪斯（银灰）。',
    '斐尔迪南': '哥伦比亚莱茵生命相关人员，绿野幻梦/孤星登场，与克丽斯腾、塞雷娅、赫默等有交集。',
    '安多恩': '拉特兰"吾导先路"核心人物，与能天使、莫斯提马、菲亚梅塔有复杂过往，拉特兰万国峰会事件的中心。',
    '卡彭': '叙拉古裔龙门黑帮头目，喧闹法则登场，与莫斯提马、拜松、槐琥有交集。',
    '大嘴莫布': '龙门黑帮人物，喧闹法则登场，与鼠王势力相关。',
}

def build_npc_profile(name, faction):
    if name in NPC_PROFILES:
        return NPC_PROFILES[name]
    if name in mapping.get('resolved', {}):
        r = mapping['resolved'][name]
        parts = []
        if r.get('identity'):
            parts.append(r['identity'])
        if r.get('tags'):
            parts.append('、'.join(r['tags']))
        if parts:
            return '；'.join(parts)[:130]
    return build_data_profile(name, faction)

# 数据兜底简介：活跃段落 + 高频关联人物
_timeline_path = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\timeline.json'
_timelines = {}
if os.path.exists(_timeline_path):
    with open(_timeline_path, encoding='utf-8') as f:
        _timelines = json.load(f).get('char_timelines', {})

def build_data_profile(name, faction):
    parts = []
    if faction != '未知':
        parts.append(f'{faction}阵营剧情角色')
    tl = _timelines.get(name)
    if tl:
        seg_counter = Counter(s.get('segment', '') for s in tl if s.get('segment'))
        top = [s for s, _ in seg_counter.most_common(2) if s]
        if top:
            parts.append('活跃于' + '、'.join(top))
    rels = sorted(
        (l for l in graph['links'] if l['source'] == name or l['target'] == name),
        key=lambda l: -l['strength']
    )[:3]
    if rels:
        names = []
        for l in rels:
            other = l['target'] if l['source'] == name else l['source']
            if other not in names:
                names.append(other)
        if names:
            parts.append('主要关联：' + '、'.join(names))
    if parts:
        return '，'.join(parts) + '。'
    return '次要剧情角色。'

profile_count = 0
for n in graph['nodes']:
    if n['operator']:
        n['profile'] = build_operator_profile(n['name'])
    else:
        n['profile'] = build_npc_profile(n['name'], n['faction'])
    if n.get('profile'):
        profile_count += 1

# ============================================================
# 3. 边关系 relation
# ============================================================
RELATIONS = {
    frozenset(['特蕾西娅', '阿米娅']): '传承',
    frozenset(['特蕾西娅', '博士']): '被背叛',
    frozenset(['特蕾西娅', 'W']): '恩人',
    frozenset(['特蕾西娅', '特雷西斯']): '兄妹·宿敌',
    frozenset(['特蕾西娅', '凯尔希']): '战友',
    frozenset(['博士', '阿米娅']): '守护',
    frozenset(['博士', '凯尔希']): '同僚',
    frozenset(['博士', '普瑞赛斯']): '前文明旧识',
    frozenset(['博士', 'W']): '旧识·仇敌',
    frozenset(['凯尔希', '阿米娅']): '监护人',
    frozenset(['凯尔希', '普瑞赛斯']): '前文明对峙',
    frozenset(['凯尔希', '爱国者']): '对峙',
    frozenset(['塔露拉', '陈']): '姐妹·宿敌',
    frozenset(['塔露拉', '阿米娅']): '敌对',
    frozenset(['塔露拉', '霜星']): '旧主·部下',
    frozenset(['塔露拉', '科西切']): '被附身',
    frozenset(['陈', '魏彦吾']): '叔侄',
    frozenset(['银灰', '初雪']): '兄妹',
    frozenset(['恩希欧迪斯', '恩雅']): '兄妹',
    frozenset(['银灰', '灵知']): '挚友',
    frozenset(['恩希欧迪斯', '诺希斯']): '挚友',
    frozenset(['玛嘉烈', '玛莉娅']): '姐妹',
    frozenset(['玛嘉烈', '佐菲娅']): '姑侄·战友',
    frozenset(['耀骑士', '瑕光']): '姐妹',
    frozenset(['耀骑士', '鞭刃']): '姑侄·战友',
    frozenset(['W', '特蕾西娅']): '忠诚',
    frozenset(['拉芙希妮', '爱布拉娜']): '姐妹',
    frozenset(['苇草', '爱布拉娜']): '姐妹',
    frozenset(['阿米娅', '霜星']): '化敌为友',
    frozenset(['推进之王', '号角']): '战友',
    frozenset(['维娜', '号角']): '战友',
    frozenset(['能天使', '莫斯提马']): '挚友',
    frozenset(['普瑞赛斯', '阿米娅']): '对峙',
    frozenset(['曼弗雷德', '特雷西斯']): '部属',
    frozenset(['血魔大君', '特雷西斯']): '同盟',
    frozenset(['血魔大君', 'Logos']): '宿敌',
    frozenset(['杜卡雷', 'Logos']): '宿敌',
    frozenset(['变形者集群', '特雷西斯']): '同盟',
    frozenset(['休露丝', '菈塔托丝']): '姐妹',
    frozenset(['休露丝', '尤卡坦']): '夫妻',
    frozenset(['伊雷妮', '拉维妮娅']): '挚友',
    frozenset(['阿米娅', '陈']): '挚友',
    frozenset(['塞雷娅', '赫默']): '昔日同僚',
    frozenset(['塞雷娅', '克丽斯腾']): '旧识·宿敌',
    frozenset(['赫默', '克丽斯腾']): '对峙',
    frozenset(['玛莉娅', '佐菲娅']): '姑侄',
    frozenset(['瑕光', '鞭刃']): '姑侄',
    frozenset(['费奥多尔', '阿洛伊泽']): '关联',
    frozenset(['W', '赫德雷']): '旧识',
    frozenset(['W', '伊内丝']): '旧识',
    frozenset(['霜星', '爱国者']): '义父女',
    frozenset(['梅菲斯特', '浮士德']): '挚友',
    frozenset(['碎骨', '米莎']): '兄妹',
    frozenset(['阿米娅', '特蕾西娅']): '传承',
    frozenset(['博士', '特蕾西娅']): '被背叛',
    frozenset(['阿米娅', '魔王']): '王冠传承',
    frozenset(['特蕾西娅', '魔王']): '本体-投影',
    frozenset(['阿米娅', '凯尔希']): '监护人',
    frozenset(['陈', '塔露拉']): '姐妹·宿敌',
    frozenset(['德克萨斯', '拉普兰德']): '宿敌·故交',
    frozenset(['格拉尼', '斯卡蒂']): '战友',
    frozenset(['斯卡蒂', '乌尔比安']): '旧识',
    frozenset(['艾丽妮', '乌尔比安']): '引路人',
    frozenset(['白垩', '黑键']): '挚友',
    frozenset(['赫默', '塞雷娅']): '昔日同僚',
    frozenset(['临光', '瑕光']): '姐妹',
    frozenset(['临光', '鞭刃']): '姑侄·战友',
}

def relation_for(a, b, fa, fb):
    key = frozenset([a, b])
    if key in RELATIONS:
        return RELATIONS[key]
    if fa == fb and fa != '未知':
        return '同阵营'
    if fa != '未知' and fb != '未知':
        return '跨阵营'
    return '剧情交集'

rel_set_count = 0
for l in graph['links']:
    a, b = l['source'], l['target']
    fa = next((n['faction'] for n in graph['nodes'] if n['name'] == a), '未知')
    fb = next((n['faction'] for n in graph['nodes'] if n['name'] == b), '未知')
    l['relation'] = relation_for(a, b, fa, fb)
    if frozenset([a, b]) in RELATIONS:
        rel_set_count += 1

# ============================================================
# 强制将主角级节点纳入核心视图（评分可能被挤出 TOP90）
# ============================================================
MUST_CORE = ['博士', '阿米娅', '凯尔希', '普瑞赛斯']
name_set = {n['name'] for n in graph['nodes']}
core_set = set(graph['core_nodes'])
for must in MUST_CORE:
    if must in name_set and must not in core_set:
        graph['core_nodes'].append(must)
        core_set.add(must)
        print(f'强制加入核心视图: {must}')

# ============================================================
# 重要角色标记 important
# 判定：核心视图节点 ∪ 幕主角(每幕对话Top1/Top2累计≥6) ∪ BOSS名单
# 用途：重要角色之间的边不受强度阈值过滤，始终显示
# ============================================================
# 幕主角统计：每幕对话量 Top1/Top2
_actor_score = {}
_scene_path = os.path.join(os.path.dirname(GRAPH_PATH), 'scene_dialogues.json')
if os.path.exists(_scene_path):
    with open(_scene_path, encoding='utf-8') as f:
        _scenes = json.load(f).get('scenes', {})
    _top1, _top2 = Counter(), Counter()
    for _key, _v in _scenes.items():
        _cnt = Counter()
        for _d in _v.get('dialogues', []):
            _s, _t = _d.get('s'), _d.get('t')
            if _s and _t and _s not in ('？？？', '旁白', '叙述'):
                _cnt[_s] += 1
        if not _cnt:
            continue
        _rk = _cnt.most_common(2)
        if _rk:
            _top1[_rk[0][0]] += 1
        if len(_rk) >= 2:
            _top2[_rk[1][0]] += 1
    for _k in set(_top1) | set(_top2):
        _actor_score[_k] = _top1.get(_k, 0) + 0.5 * _top2.get(_k, 0)

# BOSS / 主要剧情人物名单（补充强化）
BOSS_NAMES = {
    '血魔大君', '曼弗雷德', '变形者集群', '爱国者', '塔露拉', '特蕾西娅', '特雷西斯',
    '霜星', '碎骨', '梅菲斯特', '浮士德', '弑君者', '科西切', '黑蛇', '普瑞赛斯',
    '博卓卡斯替', '大鲍勃', 'W', '泥岩', '塔拉', '巫王',
}

_important_count = 0
for _n in graph['nodes']:
    _imp = (_n['name'] in core_set
            or _actor_score.get(_n['name'], 0) >= 6
            or _n['name'] in BOSS_NAMES)
    _n['important'] = _imp
    if _imp:
        _important_count += 1
print(f'重要角色标记: {_important_count} / {len(graph["nodes"])}')

# ============================================================
# 保存
# ============================================================
with open(GRAPH_PATH, 'w', encoding='utf-8') as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(graph, f, ensure_ascii=False, indent=2)

print(f'阵营补全: {faction_fixed} 个节点从"未知"归入具体阵营')
unknown = sum(1 for n in graph['nodes'] if n['faction'] == '未知')
print(f'仍有"未知"阵营: {unknown}（全量次要角色）')
print(f'简介生成: {profile_count}/{len(graph["nodes"])}')
print(f'手工关系对命中边数: {rel_set_count}')
from collections import Counter
rc = Counter(l['relation'] for l in graph['links'])
print('关系标签分布:', dict(rc.most_common()))
print()
print('=== 核心节点阵营现状 ===')
core = set(graph['core_nodes'])
for n in graph['nodes']:
    if n['name'] in core and n['faction'] == '未知':
        print(f'  仍未知: {n["name"]}')
print('核心未知阵营数:', sum(1 for n in graph['nodes'] if n['name'] in core and n['faction']=='未知'))
