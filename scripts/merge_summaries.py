# -*- coding: utf-8 -*-
"""合并所有 AI 生成的叙事梗概到 scene_dialogues.json"""
import json, os, glob

RESULTS_DIR = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\summary_results'
SCENES_PATH = r'C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30\arknights-graph\scene_dialogues.json'

def main():
    # 1. 收集所有结果
    merged = {}
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, '*.json')))
    print(f'结果文件: {len(files)} 个')
    for fp in files:
        with open(fp, encoding='utf-8') as f:
            d = json.load(f)
        for k, v in d.items():
            if k in merged:
                print(f'⚠️ 重复 key: {k} ({os.path.basename(fp)})')
            merged[k] = v
    print(f'合并梗概总数: {len(merged)}')

    # 2. 应用到 scene_dialogues.json
    with open(SCENES_PATH, encoding='utf-8') as f:
        data = json.load(f)
    scenes = data['scenes']

    updated = 0
    not_found = []
    for key, summary in merged.items():
        if key in scenes:
            old = scenes[key].get('summary', '')
            scenes[key]['summary'] = summary
            updated += 1
        else:
            not_found.append(key)
    print(f'已更新场景: {updated}')
    print(f'未匹配 key: {len(not_found)}')
    if not_found[:15]:
        print('示例:', not_found[:15])

    # 3. 统计更新后质量
    total = len(scenes)
    no_summary = [k for k, v in scenes.items() if not v.get('summary')]
    short_sum = [k for k, v in scenes.items() if v.get('summary') and len(v['summary']) < 30]
    print(f'\n总场景: {total}')
    print(f'无梗概: {len(no_summary)}')
    print(f'短梗概(<30字): {len(short_sum)}')
    # 检查还有没有"发生于/登场/关键"摘要格式残留
    digest_like = [k for k, v in scenes.items() if v.get('summary') and ('登场：' in v['summary'] or '关键：' in v['summary'])]
    print(f'摘要格式残留: {len(digest_like)}')
    if digest_like[:10]:
        print('示例:', digest_like[:10])

    with open(SCENES_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('\n已写回 scene_dialogues.json')

if __name__ == '__main__':
    main()
