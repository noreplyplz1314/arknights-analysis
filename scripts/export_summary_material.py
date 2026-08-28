# -*- coding: utf-8 -*-
"""导出每幕的浓缩素材块，供 AI 分批生成叙事梗概"""
import json, os, re

SRC = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\scene_dialogues.json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\summary_input'

def is_crowd(name):
    if not name: return True
    CROWD = ['士兵','成员','干员','市民','居民','村民','骑士','商人','贵族','工人','员工',
        '难民','感染者','流民','长老','族长','生物','声音','店主','老板','狱警','卫兵','守卫',
        '教徒','修士','教士','游客','记者','演员','观众','粉丝','船长','船员','水手','军官',
        '战士','佣兵','忍者','警察','律师','助手','随从','手下','队长','领队','小孩','孩子',
        '少女','少年','男人','女人','母亲','父亲','老人','长者','？？？','???','旁白','系统',
        '广播','喇叭','收音机','电视','提示音','电子音','机械音','通讯','无线电','耳机','人质',
        '犯人','囚犯','医生','护士','病人','学生','教师','教授','组长','助理','保安','安保',
        '保镖','打手','混混','黑帮','店员','服务员','厨师','伙计','管家','侍女','司机','驮兽',
        '动物','怪物','机械','装置','无人机','磐蟹','源石虫','恐鱼','海嗣','感染生物','幻影',
        '回音','低语','线人','赏金猎人','群演','路人','人群','众人','全体','诸位','感染者们',
        '萨卡兹','维多利亚','罗德岛','龙门','整合运动','乌萨斯','莱茵','拉特兰','深池','巴别塔',
        '女性','男性','孩童','老头','老太','青年','中年','少年兵','妇女','幼童','婴儿',
        '乌萨斯人','维多利亚人','萨卡兹佣兵','感染者','普通民众','群众','百姓','民兵',
        '列兵','军官甲','士兵甲','士官','传令兵','报务员','担架员','工兵','突击手']
    for c in CROWD:
        if c in name: return True
    return False

def main():
    with open(SRC, encoding='utf-8') as f:
        data = json.load(f)
    scenes = data['scenes']

    materials = {}
    for key, sc in scenes.items():
        # 分离旁白与对话
        narrs = []
        dlg = []
        for d in sc.get('dialogues', []):
            t = (d.get('t') or '').strip()
            if not t: continue
            if d.get('s') is None:
                narrs.append(t)
            else:
                dlg.append((d.get('s',''), t))
        # 统计角色
        char_cnt = {}
        for s, t in dlg:
            if not is_crowd(s):
                char_cnt[s] = char_cnt.get(s, 0) + 1
        chars = [c for c, _ in sorted(char_cnt.items(), key=lambda x: -x[1])][:6]
        # 旁白：合并，超过900字截首尾
        narr_full = ' '.join(narrs)
        if len(narr_full) > 900:
            narr = narr_full[:600] + ' …… ' + narr_full[-280:]
        else:
            narr = narr_full
        # 对话快照：前8条 + 末5条
        snap = []
        take = dlg[:8] + dlg[-5:]
        for s, t in take:
            snap.append(f"{s}：{t[:90]}")
        materials[key] = {
            'key': key,
            'title': sc.get('title',''),
            'order': sc.get('order', 0),
            'segment': sc.get('segment',''),
            'locations': sc.get('locations', [])[:2],
            'chars': chars,
            'narr': narr,
            'dlg_snapshot': snap,
            'n_dlg': len(dlg),
            'n_narr': len(narrs),
        }

    # 分组：主线 vs 活动
    main_keys, event_keys = [], []
    for key, m in materials.items():
        if m['segment'].startswith('主线'):
            main_keys.append(key)
        else:
            event_keys.append(key)
    # 按 order 排序
    main_keys.sort(key=lambda k: materials[k]['order'])
    event_keys.sort(key=lambda k: materials[k]['order'])

    os.makedirs(os.path.join(OUT, 'main'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'event'), exist_ok=True)

    # 每 part 20 幕
    def dump(keys, dname, prefix):
        parts = []
        for i in range(0, len(keys), 20):
            parts.append(keys[i:i+20])
        n = len(parts)
        for idx, pkeys in enumerate(parts):
            out = {'part': idx+1, 'total_parts': n, 'scene_count': len(pkeys), 'scenes': [materials[k] for k in pkeys]}
            with open(os.path.join(OUT, dname, f'{prefix}_{idx+1:02d}.json'), 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=1)
        return n

    nm = dump(main_keys, 'main', 'main')
    ne = dump(event_keys, 'event', 'event')
    print(f'主线幕: {len(main_keys)}, 分 {nm} part')
    print(f'活动幕: {len(event_keys)}, 分 {ne} part')
    print(f'总计: {len(materials)} 幕')

    # 输出一个 manifest
    with open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump({'main_parts': nm, 'event_parts': ne, 'main_scenes': len(main_keys), 'event_scenes': len(event_keys)}, f, ensure_ascii=False, indent=1)
    print('manifest 已生成')

if __name__ == '__main__':
    main()
