"""
v2: 优化角色轨迹时间线数据
- 幕标题规范化（去掉 BEG/END，统一为「章节 关卡名」）
- 活动段名补全（使用 events.json 官方活动名）
- 每幕提取关键台词（角色在该幕最有信息量的一句）
"""
import json, os, re
from collections import defaultdict

BASE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph'

with open(os.path.join(BASE, 'stories.json'), encoding='utf-8') as f:
    stories = json.load(f)
with open(os.path.join(OUT, 'graph.json'), encoding='utf-8') as f:
    graph = json.load(f)
with open(os.path.join(OUT, '..', 'name_mapping.json'), encoding='utf-8') as f:
    mapping = json.load(f)
with open(os.path.join(BASE, 'events.json'), encoding='utf-8') as f:
    events = json.load(f)

# ====== 活动标题映射：event_prefix -> 官方活动名 ======
event_titles = {}
for k, ev in events.items():
    event_titles[k] = ev.get('title', k)

# PRTS 官方活动前缀映射（SideStory / 故事集）
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
# 综合映射：优先 events.json 的 title（更准确），否则用前缀表
def resolve_event_name(prefix):
    if not prefix: return None
    if prefix in event_titles:
        return event_titles[prefix]
    return PREFIX_TITLES.get(prefix)

# ====== 归一化 ======
normalize = {}
for speaker, info in mapping['confirmed'].items():
    normalize[speaker] = info['operator']
for speaker, info in mapping['high_confidence'].items():
    normalize[speaker] = info['operator']
all_ops = set(json.load(open(os.path.join(BASE, 'characters.json'), encoding='utf-8')).keys())

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

# ====== 构建幕（按 stage 合并 BEG/END） ======
scenes = {}
for s in stories:
    md = s.get('metadata', {})
    to = md.get('timeline_order')
    if to is None: continue
    stage = s.get('stage')
    # key：优先 stage；无 stage 用 title 去 BEG/END
    if stage:
        key = stage
    else:
        title = s.get('title','')
        key = re.sub(r'/(BEG|END|NBT)$','',title) or title
    if key not in scenes:
        scenes[key] = {
            'order': to,
            'stage': stage or '',
            'stage_name': s.get('stage_name','') or key,
            'chapter': s.get('chapter'),
            'event_prefix': s.get('event_prefix'),
            'event_name': s.get('event_name'),
            'type': s.get('type'),
            'locations': list(md.get('locations', [])),
            'dialogues': [],
            'chars': defaultdict(int),
        }
    else:
        scenes[key]['order'] = min(scenes[key]['order'], to)
    # 合并位置
    for loc in md.get('locations', []):
        if loc and loc not in scenes[key]['locations'] and loc != '未知':
            scenes[key]['locations'].append(loc)
    for d in s.get('dialogues', []):
        sp = canon(d.get('speaker',''))
        txt = (d.get('text') or '').strip()
        if sp and txt:
            scenes[key]['dialogues'].append({'s': sp, 't': txt})
            scenes[key]['chars'][sp] += 1
    for t in s.get('narrative_text', []):
        if t:
            scenes[key]['dialogues'].append({'s': None, 't': t.strip()})

ordered_scenes = sorted(scenes.values(), key=lambda x: x['order'])

# 章节名
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
            name = CHAPTER_NAMES.get(ch, f'第{ch}章')
            return f'主线 · {name}'
        return '主线'
    # 活动
    if sc['event_name']:
        return sc['event_name']
    resolved = resolve_event_name(sc['event_prefix'])
    if resolved:
        return resolved
    if sc['event_prefix']:
        return sc['event_prefix']
    # 无 event_prefix：尝试从 stage/title 前缀推断
    stage = sc.get('stage') or sc['stage_name'] or ''
    st_match = re.match(r'^([A-Z]+)', stage)
    if st_match:
        pfx = st_match.group(1)
        # 主线衍生（END/M/H = 主线关卡的变体）
        if pfx.startswith('END'):
            m = re.match(r'^END(\d+)', stage)
            if m:
                ch = int(m.group(1))
                return f'主线 · {CHAPTER_NAMES.get(ch, f"第{ch}章")} · 尾声'
        if pfx.startswith('H'):
            m = re.match(r'^H(\d+)', stage)
            if m:
                ch = int(m.group(1))
                return f'主线 · {CHAPTER_NAMES.get(ch, f"第{ch}章")} · 磨难'
        if pfx.startswith('M'):
            m = re.match(r'^M(\d+)', stage)
            if m:
                ch = int(m.group(1))
                return f'主线 · {CHAPTER_NAMES.get(ch, f"第{ch}章")} · 磨难'
        # 集成战略模式
        if pfx == 'RO':
            return '集成战略 · 灰蕈迷境/傀影与猩红孤钻'
        if pfx == 'RA':
            return '集成战略 · 沙中之火'
        if pfx == 'UO':
            return '集成战略 · 探索者的银凇止境'
        if pfx == 'APF':
            return '愚人节活动'
        # 活动前缀推断
        resolved2 = resolve_event_name(pfx)
        if resolved2:
            return resolved2
    if sc.get('type') == 'story_collection':
        return '故事集'
    return '活动'

# ====== 生成角色轨迹 ======
char_timelines = {}
for node in graph['nodes']:
    name = node['name']
    appear = []
    for sc in ordered_scenes:
        if name not in sc['chars']: continue
        # 该角色台词
        own_lines = [d['t'] for d in sc['dialogues'] if d['s'] == name and len(d['t']) >= 6]
        key_line = ''
        if own_lines:
            candidates = [l for l in own_lines if 20 <= len(l) <= 110]
            key_line = candidates[0] if candidates else own_lines[0]
        # 同场角色（按对话量排）
        co = sorted([c for c in sc['chars'] if c != name and not is_crowd(c)],
                    key=lambda c: sc['chars'][c], reverse=True)[:6]
        location = ' / '.join(sc['locations'][:2]) if sc['locations'] else ''
        appear.append({
            'order': sc['order'],
            'stage': sc['stage'] or sc['stage_name'],
            'title': sc['stage_name'],
            'segment': segment_name(sc),
            'location': location,
            'line': key_line[:130],
            'coactors': co,
        })
    if appear:
        appear.sort(key=lambda x: x['order'])
        char_timelines[name] = appear

print(f"总幕数: {len(ordered_scenes)}, 有轨迹角色: {len(char_timelines)}")

# ====== 保存 ======
with open(os.path.join(OUT, 'timeline.json'), 'w', encoding='utf-8') as f:
    json.dump({
        'scene_count': len(ordered_scenes),
        'chapter_names': {str(k): v for k, v in CHAPTER_NAMES.items()},
        'ordered_scenes': [
            {
                'order': sc['order'],
                'title': sc['stage_name'],
                'segment': segment_name(sc),
                'location': ' / '.join(sc['locations'][:2]) if sc['locations'] else '',
            }
            for sc in ordered_scenes
        ],
        'char_timelines': char_timelines,
    }, f, ensure_ascii=False, indent=2)

print("已保存 timeline.json")
# 阿米娅轨迹展示
am = char_timelines.get('阿米娅', [])
print(f"\n=== 阿米娅轨迹（前 10 幕） ===")
for a in am[:10]:
    print(f"  [{a['order']}] {a['segment']} · {a['title']} | {a['location']}")
    if a['line']:
        print(f"     台词: {a['line'][:60]}...")
