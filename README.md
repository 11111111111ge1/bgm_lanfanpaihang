# Bangumi烂番排行榜

从 Bangumi.tv 获取最差动漫排行数据的工具，帮助你快速了解评分最低的动漫作品。

## 功能特性

- 📊 获取 Bangumi 平台最差动漫排行榜
- 💾 支持 JSON 格式导出数据
- 🔒 自动分离普通内容和受限内容（R18）
- 📤 支持数据上传到平台
- 📈 历史数据对比功能
- 🔄 自动错误处理和重试机制

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Access Token

创建 `.env` 文件并添加你的 Bangumi Access Token：

```
BANGUMI_ACCESS_TOKEN=your_access_token_here
```

> 💡 如何获取 Access Token：访问 [Bangumi 开发者设置](https://bgm.tv/dev/app) 创建应用并获取 token

### 3. 运行程序

```bash
python main.py
```

## 使用说明

本项目包含多个独立脚本，每个脚本需要单独运行。建议按以下顺序执行：

### 1. 获取排行数据 (main.py)

从 Bangumi API 获取最差动漫排行数据并保存为 JSON 文件。

```bash
python main.py --year 2026 --limit 100
```

**输出：** `output/json/bangumi_worst_anime_2026.json`

---

### 2. 获取去年目录数据 (get_index.py)

下载去年的 Bangumi 目录数据，用于对比排名变化。

```bash
python get_index.py
```

**输出：** `output/indices/index_{OLD_INDEX_ID}_{timestamp}.json`

---

### 3. 提取去年 NSFW 排名 (get_current_ranks.py)

从去年的目录描述中提取 NSFW 条目的排名信息。

```bash
python get_current_ranks.py
```

**输出：** `output/ranks/ranks_{timestamp}.json`

---

### 4. 上传到目录 (upload_to_index.py)

将今年的数据上传到 Bangumi 目录，自动对比去年排名显示变化。

```bash
python upload_to_index.py
```

**功能：**
- 上传所有条目到目录
- 自动对比去年排名，显示变化（↑↓NEW）
- 分离 NSFW 内容到描述中

**⚠️ 注意：** 由于 API bug（[Issue #270](https://github.com/bangumi/api/issues/270)），需要手动复制控制台输出的标题和描述到目录页面

## 数据说明

### JSON 文件结构

```json
{
  "metadata": {
    "fetch_date": "2026-01-01T12:00:00Z",
    "total_results": 100
  },
  "normal": [...],
  "nsfw": [...]
}
```

### 数据字段

| 字段 | 说明 |
|------|------|
| rank_position | 在排行榜中的位置（1-100） |
| id | Bangumi 条目 ID |
| name | 作品名称（原名） |
| score | 评分（1-10） |
| bangumi_rank | Bangumi 平台总排名 |
| rank_change | 与去年排名变化 |
| is_new | 是否新上榜 |
| nsfw | 是否为受限内容 |

## 常见问题

### Q: 为什么需要 Access Token？

A: Bangumi API 需要认证才能访问。你需要在 Bangumi 网站创建应用获取 token。

### Q: 数据多久更新一次？

A: 数据来自 Bangumi 实时 API，每次运行都会获取最新数据。

### Q: 受限内容（R18）如何处理？

A: 程序会自动将 R18 内容分离到单独的数组中，方便你选择性使用。

### Q: 遇到速率限制怎么办？

A: 程序内置了自动重试机制，会在遇到速率限制时自动等待并重试。

## 注意事项

⚠️ **重要提示：**

1. 请勿频繁请求 API，程序已设置合理的请求间隔
2. 不要将 `.env` 文件分享给他人或提交到公开仓库
3. R18 内容会单独输出，请根据当地法律法规妥善处理
4. 排名数据基于获取时的实时数据，可能随时变化

## 相关链接

- [Bangumi API 文档](https://github.com/bangumi/api)
- [讨论贴](https://bgm.tv/group/topic/447246)
- [2026年排行榜](https://bgm.tv/index/87084)
- [2025年排行榜](https://bgm.tv/index/74044)
- [2024年排行榜](https://bgm.tv/index/52786)

## 技术支持

如遇到问题，请查看：
- API 文档位于 `api-master` 文件夹
- 配置文件：`config/config.py`

## License

MIT License - 自由使用和修改
