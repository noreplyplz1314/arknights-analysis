"""
生成 scene_dialogues.json：
- 每幕的完整对话序列（归一化说话者）
- 出场人物（非群演）
- 剧情梗概（自动摘要生成，核心幕人工精修）

供前端：悬停显示梗概+人物、点击侧边栏展示全幕对话、卡片内折叠角色台词
"""
import json, os, re
from collections import Counter

BASE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph'

with open(os.path.join(BASE, 'stories.json'), encoding='utf-8') as f:
    stories = json.load(f)
with open(os.path.join(OUT, 'graph.json'), encoding='utf-8') as f:
    graph = json.load(f)
with open(os.path.join(OUT, '..', 'name_mapping.json'), encoding='utf-8') as f:
    mapping = json.load(f)
with open(os.path.join(OUT, 'timeline.json'), encoding='utf-8') as f:
    timeline = json.load(f)

# ====== 归一化映射 ======
normalize = {}
for speaker, info in mapping['confirmed'].items():
    normalize[speaker] = info['operator']
for speaker, info in mapping['high_confidence'].items():
    normalize[speaker] = info['operator']

def canon(raw):
    if not raw: return None
    if raw in ('？？？','???','……','...','—','___'): return None
    return normalize.get(raw, raw)

CROWD = ['成员','士兵','干员','市民','居民','村民','骑士','商人','贵族','工人','员工',
         '难民','感染者','流民','长老','族长','生物','声音','店主','老板','狱警','卫兵',
         '守卫','教徒','修士','教士','游客','记者','演员','观众','粉丝','船长','船员',
         '军官','战士','佣兵','忍者','警察','律师','助手','随从','手下','队长','小孩',
         '孩子','少女','少年','男人','女人','母亲','父亲','老人','长者','阿达克利斯',
         '萨卡兹','维多利亚','罗德岛','龙门','整合运动','乌萨斯','莱茵','拉特兰','深池',
         '巴别塔','谢拉格','卡西米尔','莱塔尼亚','哥伦比亚','叙拉古','萨尔贡','伊比利亚',
         '阿戈尔','萨米','杜林','玻利瓦尔','旁白','系统','广播','喇叭','收音机','电视',
         '提示音','电子音','机械音','通讯','人质','犯人','囚犯','医生','护士','病人','学生',
         '教师','教授','助理','保安','保镖','打手','混混','黑帮','店员','服务员','厨师',
         '伙计','管家','侍女','司机','驮兽','怪物','机械','装置','无人机','恐鱼','海嗣',
         '经理','镇民','猎人','首领','线人','议员','患者','代表','摊贩','刺客','密探','幼童',
         '山雪鬼','拓荒队','歌迷','孩子']
def is_crowd(name):
    if len(name) <= 1: return True
    for p in CROWD:
        if p in name: return True
    if re.match(r'^(冷静|沉稳|紧张|愤怒|恐惧|疑惑|惊讶|焦急|疲惫|慌乱|温柔|严肃|兴奋|好奇|坚定|低沉|陌生|熟悉|年轻|年老|受伤|强壮|虚弱|冷漠|热情|平静|颤抖|遥远|神秘|高大|魁梧|警觉|暴躁|恭敬|慌张|吃惊|绝望|犹豫|果断|开心|悲伤|哭泣|微笑|沉默|惊愕|欣慰|激动|忐忑|迟疑|麻木|沙哑|浑厚|刺耳|轻柔|得意|谦逊|傲慢|羞涩|腼腆|豪爽|谨慎|警惕|困惑|迷茫|疯狂|歇斯底里)[^，。]{2,6}$', name):
        return True
    return False

# ====== 活动标题映射（与 build_timeline_v2 保持一致） ======
PREFIX_TITLES = {
    'GT': '骑兵与猎人', 'OF': '火蓝之心', 'CB': '喧闹法则', 'DM': '生于黑夜',
    'TW': '沃伦姆德的薄暮', 'RI': '密林悍将归来', 'MN': '玛莉娅·临光',
    'MB': '孤岛风云', 'WR': '画中人', 'OD': '源石尘行动', 'WD': '遗尘漫步',
    'SV': '覆潮之下', 'DH': '多索雷斯假日', 'NL': '长夜临光', 'BI': '风雪过境',
    'IW': '将进酒', 'TB': '阴云火花', 'SN': '愚人号', 'LE': '尘影余音',
    'DV': '绿野幻梦', 'IC': '理想城·长夏狂欢季', 'IS': '叙拉古人',
    'FC': '照我以火', 'WB': '登临意', 'CF': '落叶逐火', 'CW': '孤星',
    'HE': '空想花庭', 'SL': '火山旅梦', 'CV': '不义之财', 'ZT': '崔林特尔梅之金',
    'RS': '银心湖列车', 'HS': '怀黍离', 'CR': '水晶箭行动', 'BB': '巴别塔',
    'FA': '生路', 'BP': '出苍白海', 'EA': '出苍白海', 'EP': '出苍白海',
    'SW': '太阳甩在身后', 'DT': '泰拉饭', 'RE': '泰拉饭', 'PV': '揭幕者们',
    'BW': '挽歌燃烧殆尽', 'EG': '挽歌燃烧殆尽', 'JH': '相见欢', 'AT': '相见欢',
    'GO': '追迹日落以西', 'SA': '追迹日落以西', 'FD': '我们明日见', 'CG': '辞岁行',
    'SE': '辞岁行', 'AD': '雅赛努斯复仇记', 'AS': '众生行记', 'BD': '直到大地变成一颗酸橙',
    'FM': '空想花庭', 'GA': '画中人', 'DC': '登临意', 'PS': '生路',
    'TA': '我们明日见', 'TG': '大家一起来', 'OS': '未尽篇章', 'KR': '骑兵与猎人(复刻)',
    'TR': '教学关卡', 'VI': '维多利亚篇', 'ME': '多索雷斯', 'OR': '叙拉古人',
    'MT': '玛莉娅·临光', 'PA': '密林悍将归来', 'UR': '孤岛风云', 'IM': '将进酒',
    'SS': '愚人号', 'BF': '感谢庆典', 'AF': '洪炉示岁', 'AW': '沃伦姆德的薄暮',
    'TD': '泰拉饭', 'TC': '风雪过境', 'CR': '联锁竞赛', 'APF': '愚人节活动',
}
CHAPTER_NAMES = {
    0: '觉醒', 1: '黑暗时代·上', 2: '黑暗时代·下', 3: '二次呼吸', 4: '急性衰竭',
    5: '靶向药物', 6: '局部坏死', 7: '苦难摇篮', 8: '怒号光明', 9: '风暴瞭望',
    10: '破碎日冕', 11: '淬火尘霾', 12: '惊霆无声', 13: '恶兆湍流', 14: '慈悲灯塔',
    15: '离解复合', 16: '反常光谱', 17: '相变临界'
}

def segment_name(sc):
    if sc['type'] == 'main_story':
        ch = sc['chapter']
        if ch is not None:
            return f"主线 · {CHAPTER_NAMES.get(ch, f'第{ch}章')}"
        return '主线'
    if sc['event_name']:
        return sc['event_name']
    if sc['event_prefix'] and sc['event_prefix'] in PREFIX_TITLES:
        return PREFIX_TITLES[sc['event_prefix']]
    if sc['event_prefix']:
        return sc['event_prefix']
    stage = sc['stage'] or sc['title'] or ''
    m = re.match(r'^([A-Z]+)', stage)
    if m:
        pfx = m.group(1)
        if pfx.startswith('END'):
            mm = re.match(r'^END(\d+)', stage)
            if mm:
                return f"主线 · {CHAPTER_NAMES.get(int(mm.group(1)), '')} · 尾声"
        if pfx.startswith('M'):
            mm = re.match(r'^M(\d+)', stage)
            if mm:
                return f"主线 · {CHAPTER_NAMES.get(int(mm.group(1)), '')} · 磨难"
        if pfx == 'RO':
            return '集成战略 · 灰蕈迷境/傀影与猩红孤钻'
        if pfx == 'RA':
            return '集成战略 · 沙中之火'
        if pfx == 'UO':
            return '集成战略 · 探索者的银凇止境'
        if pfx == 'APF':
            return '愚人节活动'
        if pfx in PREFIX_TITLES:
            return PREFIX_TITLES[pfx]
    if sc.get('type') == 'story_collection':
        return '故事集'
    return '活动'

# ====== 构建幕级数据（stage 合并 BEG/END） ======
scenes = {}
for s in stories:
    md = s.get('metadata', {})
    to = md.get('timeline_order')
    if to is None: continue
    stage = s.get('stage')
    if stage:
        key = stage
    else:
        title = s.get('title','')
        key = re.sub(r'/(BEG|END|NBT)$','',title) or title
    if key not in scenes:
        scenes[key] = {
            'order': to,
            'stage': stage or '',
            'title': s.get('stage_name','') or key,
            'chapter': s.get('chapter'),
            'event_prefix': s.get('event_prefix'),
            'event_name': s.get('event_name'),
            'type': s.get('type'),
            'locations': [],
            'dialogues': [],       # 有序完整对话 [{s, t}]
            'char_counter': Counter(),
        }
    else:
        scenes[key]['order'] = min(scenes[key]['order'], to)
    for loc in md.get('locations', []):
        if loc and loc not in scenes[key]['locations'] and loc != '未知':
            scenes[key]['locations'].append(loc)
    for d in s.get('dialogues', []):
        sp = canon(d.get('speaker',''))
        txt = (d.get('text') or '').strip()
        if txt:
            scenes[key]['dialogues'].append({'s': sp, 't': txt})
            if sp and not is_crowd(sp):
                scenes[key]['char_counter'][sp] += 1
    for t in s.get('narrative_text', []):
        if t:
            scenes[key]['dialogues'].append({'s': None, 't': t.strip()})

ordered_scenes = sorted(scenes.values(), key=lambda x: x['order'])

# ====== 剧情梗概生成 ======
# 基于对话内容自动摘要：提取关键对话 + 出场人物 + 地点
# 规则：按对话轮次，找信息量最大的句子（含角色名/特殊词/较长句）
IMPORTANT_KEYWORDS = ['叛','杀','死','塔露拉','阿米娅','博士','凯尔希','罗德岛','整合运动',
                      '源石','感染','王','魔王','卡兹戴尔','龙门','乌萨斯','维多利亚','萨卡兹',
                      '战争','和约','阴谋','计划','实验','天灾','矿石病','海嗣','深渊','黑蛇']

def summarize(scene):
    chars = [c for c, cnt in scene['char_counter'].most_common(8) if not is_crowd(c)]
    loc = ' / '.join(scene['locations'][:2]) if scene['locations'] else ''
    # 抽取关键对话
    texts = [d['t'] for d in scene['dialogues'] if d['t'] and len(d['t']) >= 10]
    key_lines = []
    for t in texts:
        score = 0
        for kw in IMPORTANT_KEYWORDS:
            if kw in t:
                score += 1
        if len(t) >= 25:
            score += 0.5
        if score >= 1:
            key_lines.append((score, t))
    key_lines.sort(key=lambda x: -x[0])
    # 生成梗概
    parts = []
    if loc:
        parts.append(f"发生于{loc}")
    if chars:
        parts.append(f"登场：{'、'.join(chars[:5])}")
    if key_lines:
        parts.append(f"关键：{key_lines[0][1][:60]}")
    return '；'.join(parts) if parts else '（本幕以叙述为主）'

# ====== 核心幕人工精修梗概 ======
# 这些是剧情关键节点，人工编写更准确的梗概
MANUAL_SUMMARIES = {
    '0-1': '切尔诺伯格遭遇整合运动袭击，罗德岛紧急救援，阿米娅与博士初登场。',
    '0-10': '罗德岛在切尔诺伯格困境中突围，遭遇梅菲斯特与浮士德，临光、Ace参与战斗。',
    '1-1': '博士从石棺中苏醒，失去记忆，被罗德岛救出。',
    '4-4': '阿米娅与霜星初次正面交锋，雪怪小队展现战力。',
    '6-16': '梅菲斯特与浮士德悲剧落幕，整合运动内部矛盾激化。',
    '7-1': '爱国者与罗德岛对峙，揭示爱国者的过去与立场。',
    '7-18': '爱国者阵亡，博卓卡斯替的故事终结，罗德岛获其遗志。',
    '8-1': '龙门与整合运动的决战，塔露拉的真面目开始显露。',
    '8-8': '阿米娅与塔露拉的决战，黑蛇科西切的阴谋揭开。',
    '8-20': '塔露拉被击败，整合运动瓦解，第八章主线下半部收束。',
    '9-1': '罗德岛抵达维多利亚，开启风暴瞭望篇章。',
    '10-1': '伦蒂尼姆陷落，萨卡兹王庭掌控维多利亚首都。',
    '11-1': '维多利亚王座之争浮出水面，阿勒黛与维娜的往事揭开。',
    '12-1': '萨卡兹王庭全面进攻，罗德岛与自救军并肩作战。',
    '13-1': '伦蒂尼姆战役白热化，特雷西斯与特蕾西娅的过去被揭示。',
    '14-1': '慈悲灯塔篇开启，罗德岛与萨卡兹的最终对决。',
    '14-21': '特蕾西娅之死真相揭晓，阿米娅继承魔王权柄。',
    '15-1': '内化宇宙篇，普瑞赛斯与博士的过去全面展开。',
    '15-17': '凯尔希与普瑞赛斯的对峙，源石计划的真相。',
    '16-1': '乌萨斯远北矿区，新篇章展开。',
    '17-1': '乌萨斯源石工业革命暴乱，费奥多尔线推进。',
    'BB-1': '巴别塔时代，博士与特蕾西娅的相遇。',
    'BB-10': '巴别塔覆灭之夜，博士的背叛与特蕾西娅之死。',
    'SN-1': '愚人号启航，深海线的重要节点。',
    'CW-1': '孤星篇开启，莱茵生命总辖克丽斯腾的太空计划。',
    'NL-1': '长夜临光开幕，卡西米尔骑士竞技的暗流。',
    'BI-1': '风雪过境开幕，谢拉格雪山政治博弈。',
    'CW-9': '克丽斯腾升空冲向星门，孤星结局。',
    'CW-8': '塞雷娅与赫默的伦理对峙，莱茵生命的真面目。',
    'NL-8': '耀骑士临光复出之战，卡西米尔骑士制度的崩塌。',
    'BI-6': '雪山大典暗杀事件，休露丝被诬陷。',
    'IS-10': '叙拉古家族混战，西西里夫人的秩序。',
    'IW-8': '将进酒结局，宁辞秋与梁洵告别。',
    'ZT-10': '崔林特尔梅之金结局，女皇与塑心的对决。',
    'RS-8': '银心湖列车结局，谢拉格改革完成。',
    'HS-9': '怀黍离结局，炎国岁兽线推进。',
    'SL-8': '火山旅梦结局，汐斯塔重建。',
    'CV-8': '不义之财结局，哥伦比亚金钱与正义。',
    'FC-8': '照我以火结局，叙拉古家族余烬。',
    'WB-9': '登临意结局，大炎天师线的展开。',
    'LE-7': '尘影余音结局，白垩的牺牲与黑键的救赎。',
    'SV-9': '覆潮之下结局，深海教会与海嗣的真相。',
    'OD-8': '源石尘行动结局，彩虹小队与萨尔贡的救援。',
    'GT-6': '骑兵与猎人结局，大鲍勃与赏金猎人线的起点。',
    'SN-5': '愚人号遭遇深海主教，斯卡蒂与海嗣的宿命。',
    'TR-1': '罗德岛基地教学关，博士熟悉基础作战指令。',
    'BB-ST-2': '博士在巴别塔中苏醒的回忆，与特蕾西娅的初识。',
    'BB-7': '巴别塔与萨卡兹叛军交战，博士展现出战术碾压能力。',
    'DM-3': '巴别塔时期博士的意识碎片，身份悬置的叙事。',
    '6-2': '整合运动袭击龙门，霜星与罗德岛初次接触。',
    '6-17': '浮士德之死，梅菲斯特精神崩溃，雪怪小队覆灭。',
    '5-10': '梅菲斯特与浮士德少年回忆，塔露拉悲剧的根源。',
    '4-10': '霜星战死，阿米娅的第一次重大失去。',
    '7-3': '爱国者与凯尔希的对话，揭示感染者战争的残酷。',
    '9-21': '罗德岛抵达维多利亚，伦蒂尼姆陷入混乱。',
    '10-3': '萨卡兹占领伦蒂尼姆，号角与推进之王重逢。',
    '11-2': '阿勒黛与维娜的往事，坎伯兰家族的衰落。',
    '12-2': '变形者集群现身，茉莉被替换的真相。',
    '13-5': '特雷西斯的过去，萨卡兹内战的历史。',
    '14-6': '阿米娅直面特蕾西娅的投影，魔王传承开始。',
    '15-9': '凯尔希牺牲自己对抗普瑞赛斯，内化宇宙的决战。',
    '16-4': '乌萨斯远北矿区，矿工与源石工业的真相。',
    '17-9': '费奥多尔与阿洛伊泽的对话，乌萨斯内乱升级。',
}

# ====== 组装输出 ======
scene_details = {}
for sc in ordered_scenes:
    key = sc['stage'] or sc['title']
    chars = [c for c, cnt in sc['char_counter'].most_common(12) if not is_crowd(c)]
    summary = MANUAL_SUMMARIES.get(key) or summarize(sc)
    scene_details[key] = {
        'order': sc['order'],
        'title': sc['title'],
        'segment': segment_name(sc),
        'location': ' / '.join(sc['locations'][:2]) if sc['locations'] else '',
        'summary': summary,
        'characters': chars,
        'dialogues': sc['dialogues'][:300],  # 完整对话（截断极端长幕）
    }

with open(os.path.join(OUT, 'scene_dialogues.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'scene_count': len(scene_details),
        'scenes': scene_details,
    }, f, ensure_ascii=False, indent=2)

print(f"幕总数: {len(scene_details)}")
# 检查核心幕梗概
print("\n=== 核心幕梗概示例 ===")
for k in ['0-1','7-18','8-8','14-21','15-17','BB-10','CW-1']:
    if k in scene_details:
        sc = scene_details[k]
        print(f"  [{sc['order']}] {sc['title']} | {sc['segment']}")
        print(f"     梗概: {sc['summary']}")
        print(f"     人物: {sc['characters'][:6]}")
