# 明日方舟剧情分析项目 · 接手文档

> 项目版本：**v1.0**（2026-08-23）
> 工作区：`C:\Users\Administrator\WorkBuddy\2026-08-01-13-46-30`
> 原始数据：`C:\Users\Administrator\WorkBuddy\2026-08-01-12-42-09\arknights-lore\data\json\`（PRTS Wiki 抓取：stories.json 1681 幕剧情 / characters.json 452 干员 / relationships.json / events.json 74 活动）
> 预览：`http://127.0.0.1:8823`（在 arknights-graph/ 下 `python -m http.server 8823`）

---

## 一、产品定位

把明日方舟全量剧情数据转化为**可交互探索的双视图工具**：
- **图谱视图**：人物关系网（阵营聚团、点选聚焦、关系标注、人物简介）
- **时间线视图**：1113 幕剧情时间线（角色轨迹、全幕对话、章节目录回溯、叙事梗概）

---

## 二、交付物（`arknights-graph/` 目录，v1.0 离线可用）

| 文件 | 说明 |
|---|---|
| `index.html` | 单页应用（图谱 + 时间线双视图），ECharts 力导向/静态簇布局 |
| `graph.json` | 图谱数据：**956 节点 / 10724 边 / 92 核心**；节点含 `faction/profile/important`；边含 `relation/strength` |
| `timeline.json` | 时间线数据：**1113 幕**、951 角色轨迹（order/段落/地点/关键台词/同场角色） |
| `scene_dialogues.json` | 场景数据：每幕完整对话 + 出场人物 + **叙事梗概**（1113 幕全覆盖）+ `year` 世界观年份（725 幕） |
| `echarts.min.js` | ECharts 5.5.0 本地副本（离线可用） |
| `avatars.json` | **角色头像映射**（1159 角色全覆盖）：`{avatar:{角色名: media.prts.wiki URL}}`；PRTS 图片为 MD5 哈希路径，URL 由 `头像_<名>.png` / `头像_敌人_<名>.png` 的 MD5 本地构造（无需 API，CDN 直连验证） |

### 根目录其他关键交付
- `arknights_timeline.txt` — 复核修正版世界观时间线（九节结构，修正 4 处时间错误）
- `name_mapping.json` / `name_mapping.md` — 角色身份映射表（42 确认 + 10 用户判定）
- `character_selection_rules.md` — 重点人物筛选规则（主线分层 + 10 条支线 + 异格 if 线）
- `arknights_lore_analysis_summary.md` — 综合分析报告（关键人物/匿名推断/博士分析/时间线）

---

## 三、数据管线（按序执行可复现）

```
原始 stories.json
   │  mine_relations.py       提取对话交互+同幕共现，name_mapping 归一化真名→干员，过滤群演
   │  → graph_interim.json
   │  build_graph.py          节点评分/核心90/边强度 → graph.json
   │  enrich_graph.py         ★ 补阵营/简介profile/边relation/important标记/MUST_CORE
   │  → graph.json（含 profile、relation、important）→ 复制到 arknights-graph/
   │
   │  build_timeline_v2.py    幕级时间线（合并BEG/END），PRTS前缀→活动名映射 → timeline.json
   │  build_scene_dialogues.py 每幕完整对话+梗概（40+核心幕人工精修，其余自动摘要）
   │  export_summary_material.py → summary_input/（素材块）
   │  （主线我逐批写梗概 / 活动21个子代理并行）→ summary_results/
   │  merge_summaries.py      合并 → scene_dialogues.json 全量叙事梗概
   │  inject_years.py         注入世界观年份（year 字段，725幕）
   │  fix_segments.py         修正活动前缀→官方活动名（394幕+2833节点）
   └──→ arknights-graph/{graph.json, timeline.json, scene_dialogues.json}
```

---

## 四、核心数据决策（重要，勿改动）

### 1. 角色身份映射（name_mapping）
- 剧情说话者用**真名**，干员库用**代号**（恩希欧迪斯=银灰、费德里科=送葬人、拉维妮娅=斥罪等 42 条已确认）
- `resolved` 10 项为用户判定（关键）：
  - **特蕾西娅本体**=独立NPC(已死亡)；干员「魔王 Civilight Eterna」=黑王冠内投影镜像，**非本人**，不映射
  - **塔露拉**=卫星NPC（`future_playable:true`，未实装干员，网传 2025 落地是谣言）
  - **普瑞赛斯**=世界观基底NPC（前文明）
  - 曼弗雷德/血魔大君(杜卡雷)/变形者集群=纯剧情NPC/BOSS（无实装线索）

### 2. 时间线年份（用户复核修正版）
- 特蕾西娅遇刺=1094（非1093）、EP9=1097秋、吾导先路=1099.3、伦蒂尼姆围城战 EP10-13=1098.7-10
- 完整九节年表见 `arknights_timeline.txt`

### 3. 重要角色（important，111/956）
- 判定 = 核心视图92 ∪ 幕主角(每幕对话Top1/Top2评分≥6) ∪ BOSS名单
- 重要角色之间的边**不受强度阈值过滤**，始终显示

### 4. 关键教训
- **"塔露拉2025实装"是错误信息源**（训练知识/社区传言），凡涉及实装判定一律以 PRTS 图鉴+官方公告为准
- 核心视图按评分截断会漏掉"对话分散型"主角（博士 score 0.669 在 TOP90 外），用 MUST_CORE 兜底
- filterNodes 返回 GRAPH.links 引用（无 `_l`），取边字段直接用 `l.relation`

---

## 五、前端功能清单（v1.0）

### 图谱视图
- 阵营簇**静态布局**（layout:none，同阵营圆周聚团，簇内黄金角螺旋）
- 节点：同阵营同色填充 + 外框描边；**核心92**默认视图；**核心视图节点用角色头像**（`symbol:image://`，全量视图保留色块防卡）
- **点选模式**：相关边金色虚线 + 关系标签；邻居之间淡虚线；无关节点淡出
- **左上悬浮小卡**：人物简介(profile) + 关键关系 chips + 头像；ESC/点空白退出
- 右侧详情卡：头像/对话量/出场幕/关联数/异格/核心关联/查看剧情轨迹
- 强度阈值滑杆（默认5%）、阵营筛选、干员/NPC筛选、搜索、核心/全量切换
- **重要角色边恒显示**：`isConcreteRel`(手工关系) + `importantLink`(两端重要)
- **角色列表带头像**：`avatarHtml()` 有图用图（no-referrer），无图用阵营色首字占位

### 时间线视图
- 角色轨迹列表（按重要度排序，可搜索）
- **单列 / 树状双列**切换：树状=主线一列+其他剧情一列，纵向统一坐标轴
- 卡片：年份徽章、关键台词、同场角色跳转、折叠本角色对话
- 点击卡片 → 全幕对话侧栏 + **章节目录回溯**（当前段落全部幕、高亮位置）
- 悬停 → 剧情梗概 tooltip（全 1113 幕叙事体）
- 段落/地点筛选

---

## 六、已知问题 / 待办

1. **第 8 章「怒号光明」数据缺失**：原始抓取无 stage=8-x 条目（timeline_order 143→145 断层），时间线/图谱中第8章描述基于常识
2. 全量视图仍有 642 个"未知"阵营（次要角色，灰色）
3. PRTS 无页面前缀待核实：KR/CG/BD/SS/SW/PA/RE/FD/IM
4. EP14「慈悲灯塔」年份：复核版未单列，标注"1098末~1099初（待官方确认）"
5. 多索雷斯/相见欢/空想花庭等 35 个 segment 无世界观年份锚点

---

## 七、快速上手

1. 启动预览：`cd arknights-graph && python -m http.server 8823` → 浏览器开 `http://127.0.0.1:8823`
2. 改数据：修改对应生成脚本重跑（enrich_graph.py / build_timeline_v2.py 等），把 graph.json 同步到 arknights-graph/
3. 改前端：直接编辑 `arknights-graph/index.html`，刷新即生效（注意浏览器缓存用 Ctrl+F5）
