# 明日方舟剧情图谱与时间线工具（arknights-analysis）

> ⚠️ 非官方项目，仅供学习与交流使用。所有剧情/角色数据均来自公开资料整理，与鹰角网络（Hypergryph / Yostar）无隶属关系。

## 功能

- 角色关系图谱（基于 ECharts 的交互式可视化）
- 剧情时间线浏览
- 场景对话检索
- 阵营 / 关系详情查阅

## 目录结构

```
index.html                单页应用入口（通过 fetch 加载本地 JSON）
graph.json                关系图谱数据
timeline.json             时间线数据
scene_dialogues.json      场景对话数据
relation_details.json     关系详情
avatars.json / faction_logos.json  头像与阵营图标索引
avatars.zip               头像资源压缩包（解压为 avatars/）
scripts/                  数据处理脚本（Python）
```

## 本地运行

> 由于浏览器在 `file://` 下会拦截 `fetch()` 本地文件，请使用本地 HTTP 服务打开。

```bash
# 0. 头像资源 avatars/ 已随仓库提供，无需解压
# 1. 启动本地服务
python -m http.server 8823 --bind 127.0.0.1

# 3. 浏览器访问
#    http://127.0.0.1:8823
```

## 开源说明

- 代码以 MIT 许可证开源（见 `LICENSE`）。
- 头像资源 `avatars/` 已随仓库提供（由 `avatars.zip` 解压得到），克隆即可直接使用。
- 数据文件（JSON）已随仓库提供，克隆即可运行。

## 免责声明

本项目为粉丝向衍生作品，不构成任何官方授权。如权利方提出异议，将配合下线相关内容。
