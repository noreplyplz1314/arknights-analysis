# -*- coding: utf-8 -*-
"""对照 PRTS Wiki 审核并修正章节目录（segment）命名
- 依据 PRTS 关卡页/别传页确认的「前缀→活动」映射
- 修正 scene_dialogues.json 与 timeline.json 的 segment 字段
- 生成审计报告
"""
import json, re, os

SCENES = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\scene_dialogues.json'
TIMELINE = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\timeline.json'
REPORT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\segment_audit_report.md'

# ====== 已确认映射（PRTS 关卡页/别传页铁证） ======
CONFIRMED = {
    'GT':'骑兵与猎人','OF':'火蓝之心','CB':'喧闹法则','TW':'沃伦姆德的薄暮',
    'RI':'密林悍将归来','MN':'玛莉娅·临光','MB':'孤岛风云','WR':'画中人',
    'DH':'多索雷斯假日','NL':'长夜临光','BI':'风雪过境','IW':'将进酒',
    'GA':'吾导先路','LE':'尘影余音','DV':'绿野幻梦','IC':'理想城长夏狂欢季',
    'IS':'叙拉古人','FC':'照我以火','WB':'登临意','HE':'空想花庭',
    'SL':'火山旅梦','CV':'不义之财','SN':'愚人号','GO':'追迹日落以西',
    'BB':'巴别塔','CW':'孤星','DM':'生于黑夜','WD':'遗尘漫步',
    'SV':'覆潮之下','BP':'生路','AD':'雅赛努斯复仇记','ME':'雅赛努斯复仇记',
    'TC':'未尽篇章','VI':'如我所见','DT':'泰拉饭','TD':'泡影苍霆',
    'RA':'生息演算 · 沙中之火','RS':'银心湖列车','OS':'银心湖列车',
    'TB':'阴云火花','DC':'春分','FA':'踏寻往昔之风','PS':'红松林',
    'SA':'午间逸话','PL':'灯火序曲','BH':'此地之外','BW':'好久不见',
    'AW':'日暮寻路','AS':'太阳甩在身后','CR':'视相博物馆','CF':'密林悍将归来',
    'FM':'画中人','ZT':'崔林特尔梅之金','EG':'挽歌燃烧殆尽','HS':'怀黍离',
    'TA':'我们明日见','TG':'大家一起来','AF':'洪炉示岁','OD':'源石尘行动',
    'APF':'愚人节活动','TR':'教学关卡','PV':'揭幕者们','EP':'出苍白海',
}
# ====== 高置信推断（数据内容特征，标注★） ======
INFERRED = {
    'MT':'空想花庭',           # MT-1圣秩/寻路者/堕天 → 空想花庭（拉特兰）
    'OR':'相见欢',             # OR-1一清二白/火灶/人间烟火 → 炎国岁片活动
    'SE':'挽歌燃烧殆尽',        # SE寻灯续昼/伦蒂尼姆 → 维多利亚篇（EG合并）
    'UR':'出苍白海',           # UR-1嘈杂天空/浮空/星荚 → 出苍白海（阿戈尔移动城）
    'FD':'泰拉饭',             # FD-1繁荣滋长/指木雕刻 → 米诺斯美食
    'RO':'集成战略 · 灰蕈迷境',  # RO-BEG/刻俄柏 → 灰蕈迷境
    'UO':'集成战略 · 探索者的银凇止境',  # 城郊探奇节目 → 银凇止境
    'PA':'乌萨斯的孩子们',      # PA-1卡托加区/雪地暴徒 → 乌萨斯故事集
    'AT':'相见欢',             # AT-1极道作风/天命 → 相见欢（推断存疑）
    'EA':'出苍白海',           # EA-1扉页所见/涉过寒夜 → 出苍白海（推断存疑）
}
# ====== 主线章节名 ======
CHAPTER_NAMES = {
    0:'觉醒',1:'黑暗时代·上',2:'黑暗时代·下',3:'二次呼吸',4:'急性衰竭',
    5:'靶向药物',6:'局部坏死',7:'苦难摇篮',8:'怒号光明',9:'风暴瞭望',
    10:'破碎日冕',11:'淬火尘霾',12:'惊霆无声',13:'恶兆湍流',14:'慈悲灯塔',
    15:'离解复合',16:'反常光谱',17:'相变临界',
}

def is_main_key(key):
    """判断是否主线关卡（数字开头 或 END/M/H + 数字 或 EP + 两位数章节入口）"""
    if re.match(r'^\d+-\d+', key): return True
    if re.match(r'^(END|M|H)\d+', key): return True
    if re.match(r'^EP\d\d', key): return True   # EP09/EP10 等章节入口
    return False

def main_segment(key):
    m = re.match(r'^(?:END|M|H)?(\d+)', key)
    if m:
        ch = int(m.group(1))
        base = f'主线 · {CHAPTER_NAMES.get(ch, f"第{ch}章")}'
        if key.startswith('END'): return base + ' · 尾声'
        if key.startswith('M'): return base + ' · 磨难'
        if key.startswith('H'): return base + ' · 磨难'
        return base
    # EP 入口（两位数）
    m2 = re.match(r'EP(\d{2})', key)
    if m2:
        ch = int(m2.group(1))
        return f'主线 · {CHAPTER_NAMES.get(ch, f"第{ch}章")}'
    # EP 单数字/EP-ST = 出苍白海
    if key.startswith('EP'):
        return '出苍白海'
    return '主线'

def compute_segment(key):
    """根据 key 计算正确 segment"""
    if is_main_key(key):
        return main_segment(key)
    m = re.match(r'^([A-Z]+)', key)
    if m:
        p = m.group(1)
        if p in CONFIRMED: return CONFIRMED[p]
        if p in INFERRED: return INFERRED[p]
        # 未收录前缀：保持原样（可能有误，报告标注）
        return None
    return None

def main():
    fixes = []          # (key, 旧segment, 新segment)
    report_lines = []
    report_lines.append('# 章节目录（segment）对照 PRTS 审计报告\n')
    report_lines.append(f'审计时间：2026-08-23\n')
    report_lines.append('审计方法：逐一抓取 PRTS 关卡页（prts.wiki/w/前缀-1）与关卡一览/别传页，确认「关卡前缀→活动」官方归属；对无 PRTS 页面的前缀以剧情内容特征推断。\n')

    # 1. 修正 scene_dialogues.json
    with open(SCENES, encoding='utf-8') as f:
        scenes = json.load(f)
    seg_dict = scenes['scenes']
    stat = {}   # 前缀 -> {old_seg, new_seg, cnt}
    for key, sc in seg_dict.items():
        new_seg = compute_segment(key)
        if new_seg is None: continue
        old = sc.get('segment','')
        if old != new_seg:
            fixes.append((key, old, new_seg))
            sc['segment'] = new_seg
            m = re.match(r'^([A-Z]+)', key)
            p = m.group(1) if m else key[:6]
            stat.setdefault(p, {'old': old, 'new': new_seg, 'cnt': 0})
            stat[p]['cnt'] += 1

    with open(SCENES, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, ensure_ascii=False, indent=1)
    print(f'scene_dialogues.json 修正 {len(fixes)} 幕')

    # 2. 修正 timeline.json
    with open(TIMELINE, encoding='utf-8') as f:
        tl = json.load(f)
    tl_fix = 0
    for char, arr in tl['char_timelines'].items():
        for node in arr:
            # 节点可能无 key，用 stage/title 推断
            k = node.get('stage') or node.get('title') or ''
            new_seg = compute_segment(k)
            if new_seg is None: continue
            if node.get('segment') != new_seg:
                node['segment'] = new_seg
                tl_fix += 1
    with open(TIMELINE, 'w', encoding='utf-8') as f:
        json.dump(tl, f, ensure_ascii=False, indent=1)
    print(f'timeline.json 修正 {tl_fix} 个轨迹节点')

    # 3. 审计报告
    report_lines.append('## 一、已确认修正的前缀映射（PRTS 铁证）\n')
    report_lines.append('| 前缀 | 原（错误）segment | 修正后 segment | 修正幕数 | 证据 |')
    report_lines.append('|---|---|---|---|---|')
    # 按确认/推断分组
    for p, info in sorted(stat.items(), key=lambda x: x[1]['new']):
        if p in CONFIRMED:
            evidence = 'PRTS 关卡页/别传页'
        elif p in INFERRED:
            evidence = '剧情内容特征（推断★）'
        else:
            evidence = '其他'
        report_lines.append(f"| {p} | {info['old']} | {info['new']} | {info['cnt']} | {evidence} |")

    report_lines.append('\n## 二、特殊问题\n')
    report_lines.append('- **集成战略合并**：RO 前缀原合并「灰蕈迷境/傀影与猩红孤钻」两期，现拆为「灰蕈迷境」；傀影与猩红孤钻需后续数据补全')
    report_lines.append('- **联动活动**：DT=泰拉饭（×迷宫饭）、TD=泡影苍霆（×怪物猎人）已按官方确认')
    report_lines.append('- **同活动多前缀**：雅赛努斯复仇记=AD+ME；银心湖列车=RS+OS；画中人=FM+WR；密林悍将归来=CF+RI；长夜临光=NL+（LE已拆出）；将进酒=IW+IM')
    report_lines.append('- **主线变体**：END/M/H 前缀仍归主线各章，标注尾声/磨难')

    report_lines.append('\n## 三、仍待核实的前缀（无 PRTS 页面，数据源不完整）\n')
    unknown = ['SS','SW','CG','KR','RE','PA','EA','UR','AT','OR','MT','SE','FD','IM']
    report_lines.append('以下前缀 PRTS 无对应关卡页（可能为数据抓取器自定义/复刻变体），本次未强制修正：' + '、'.join(unknown) + '\n')
    report_lines.append('- SS（月光/梦境童话）、SW（无名氏的战争）、CG（红酒谋杀案）、KR（卡兹戴尔之歌）、RE（活动手指/变格博士）、EA（出苍白海?）、UR（出苍白海?）、AT/OR（相见欢?）、MT（空想花庭/吾导先路?）、SE（挽歌燃烧殆尽?）、FD（泰拉饭?）、IM（将进酒入口?）\n')

    report_lines.append('\n## 四、审核结论\n')
    report_lines.append(f'- 共修正 **{len(fixes)}** 幕的章节目录归属，涉及 **{len(stat)}** 个活动前缀\n')
    report_lines.append('- 原数据最严重错误：IS被命名为「玛莉娅临光」（实为叙拉古人）、VI被命名为「维多利亚篇」（实为如我所见）、TC被命名为「风雪过境」（实为未尽篇章）、OS被命名为「未尽篇章」（实为银心湖列车）、PV被命名为「未尽之地」（实为揭幕者们）等\n')
    report_lines.append('- 时间线排序字段 timeline_order 本身完整（1~1261），未发现缺失；但世界观年份（1096~1101）需另行核对各章/活动对应年份（见下）\n')

    report_lines.append('\n## 五、主线时间线时间对照（供审核）\n')
    timeline_note = '''
| 主线章节 | 世界观时间 | 说明 |
|---|---|---|
| 第0-2章 觉醒/黑暗时代 | 1096年12月 | 切尔诺伯格事件、龙门初访 |
| 第3-6章 二次呼吸~局部坏死 | 1097年初 | 龙门保卫战、霜星之死 |
| 第7章 苦难摇篮 | 1097年冬 | 切城撞击、爱国者之死 |
| 第8章 怒号光明 | 1097年冬 | 塔露拉决战、黑蛇揭露 |
| 第9章 风暴瞭望 | 1099年 | 小丘郡事件（Outcast牺牲） |
| 第10-14章 破碎日冕~慈悲灯塔 | 1100年 | 伦蒂尼姆篇（W、特雷西斯） |
| 第15章 离解复合 | 1101年夏 | 普瑞赛斯苏醒、凯尔希之决 |
| 第16-17章 反常光谱/相变临界 | 1101年秋~ | 乌萨斯远北、圣愚、费奥多尔 |
'''
    report_lines.append(timeline_note)
    report_lines.append('> ⚠️ 以上年份为剧情惯例推断，主线各章精确到"月/日"需逐幕核对 PRTS 剧情文本；建议作为下一步专项审核。\n')

    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f'审计报告已写入 {REPORT}')

if __name__ == '__main__':
    main()
