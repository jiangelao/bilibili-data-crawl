---
name: bilibili-creator-data
description: 爬取B站创作中心视频数据，包括播放量、点赞量、收藏量、封标点击率、3秒跳出率、互动率等，并保存到飞书表格。支持Cookie持久化存储（存储于skill目录内部），仅在Cookie失效或不存在时才要求用户手动更新。触发方式：当用户需求涉及"爬取"、"抓取"、"b站"、"B站"、"哔哩哔哩"、"视频数据"、"创作中心"、"播放量"、"数据分析"等关键词或其近义词时，即可调用此skill。
---

# Bilibili Creator Data (v0.5.0)

## Overview

使用Cookie认证自动爬取B站创作中心视频数据，数据输出到飞书云文档的电子表格中，存放在名为"几何节点视频数据"的文件夹内。

**核心特性：**
- Cookie持久化存储到skill目录内部（`scripts/.bilibili_cookie.json`），无需每次手动输入
- Cookie文件不与用户主目录耦合，兼容云端Agent部署
- 所有百分比字段存储为**数值类型**，可直接在飞书中用于计算
- `fetch_video_data.py` 启动时自动检测并安装 `requests` 依赖，无需手动配置
- `update_feishu.py` 改用 stdin（标准输入）传递 JSON 数据，彻底避免 shell 转义导致的 JSON 损坏
- `update_feishu.py` v0.5.0 适配 Windows 平台（自动检测并使用 lark-cli.cmd）
- `update_feishu.py` v0.5.0 修复 lark-cli 嵌套 JSON 返回结构解析（`data.results`、`data.spreadsheet.spreadsheet.token` 等）
- `update_feishu.py` v0.5.0 适配 Windows 平台（自动检测并使用 lark-cli.cmd）
- `update_feishu.py` v0.5.0 修复 lark-cli 嵌套 JSON 返回结构解析（`data.results`、`data.spreadsheet.spreadsheet.token` 等）

## Trigger Conditions

当用户的请求包含以下任一类关键词（或其近义词/变体）时，触发此skill：

- **平台词**：b站、B站、哔哩哔哩、bilibili
- **动作词**：爬取、抓取、获取、拉取、采集、提取、导出、下载、查询
- **数据词**：视频数据、创作中心、播放量、数据分析、数据统计、视频表现、创作者数据、视频分析

如果用户仅提到"B站"但未涉及数据获取（如"B站怎么发视频"），则不触发此skill。

## Prerequisites

执行前确认以下信息：
1. 目标视频的BV号（如 `BV1cNRWBzEkj`）
2. 云环境已安装 `lark-cli` 并完成飞书认证
3. 数据将输出到飞书云表格，存放在"几何节点视频数据"文件夹中

> ⚠️ **Windows 注意事项**：
> 1. **Python**: Windows 自带的 `python3` 命令可能指向 Windows Apps Store 占位程序（exit code 49）。遇到此问题时必须使用完整 Python 路径（如 `D:/Dev_env/Python/Python3/python.exe`），或确认 `python` 命令可用。下文的 `"Python路径"` 均指代此处选定的命令。
> 2. **lark-cli**: Windows 上 lark-cli 安装为 `lark-cli.cmd`，`subprocess.run(["lark-cli"])` 无法直接调用。v0.5.0 已内置自动兼容处理（检测 `sys.platform` 自动切换）。如果手动测试命令，请使用 `lark-cli.cmd`。

## Execution

### Step 1: 加载Cookie

先尝试从本地持久化文件加载Cookie。

```
"Python路径" scripts/cookie_manager.py load
```

判断返回结果：

- **`success` 为 `true`**：使用加载到的Cookie值（`sessdata`、`dedeuserid_ckmd5`），跳到 Step 2。
- **`success` 为 `false` 且 `message` 包含"不存在"**：提示用户提供Cookie，然后执行保存操作：
  ```
  "Python路径" scripts/cookie_manager.py save --sessdata "SESSDATA值" --dedeuserid_ckmd5 "DedeUserID__ckMd5值"
  ```
  保存成功后继续 Step 2。
- **`success` 为 `false` 且 `message` 包含"格式错误"或"不完整"**：先执行删除：
  ```
  "Python路径" scripts/cookie_manager.py delete
  ```
  然后提示用户提供新的Cookie并保存，保存成功后继续 Step 2。

**Stop condition**: Cookie 加载成功或者用户提供了新的有效 Cookie 并保存成功。否则继续等待用户输入。

### Step 2: 验证Cookie有效性

使用已加载的Cookie验证登录状态。

```
"Python路径" scripts/verify_cookie.py "SESSDATA" "DedeUserID__ckMd5"
```

判断返回结果：

- **`is_login` 为 `true`**：记录用户名，继续 Step 3。
- **`is_login` 为 `false`**（Cookie失效）：
  1. 删除本地失效的Cookie文件：`"Python路径" scripts/cookie_manager.py delete`
  2. 提示用户："Cookie已失效，请重新登录B站并提供 SESSDATA 和 DedeUserID__ckMd5"
  3. 等待用户提供新Cookie后，执行保存：`"Python路径" scripts/cookie_manager.py save --sessdata "新值" --dedeuserid_ckmd5 "新值"`
  4. 保存成功后重新执行验证命令。验证通过则继续 Step 3；仍然失败则停止执行。

**Stop condition**: Cookie 验证通过（`is_login=true`），或用户提供了新 Cookie 且验证通过。

### Step 3: 获取视频数据

使用Cookie爬取指定视频的数据。

```
"Python路径" scripts/fetch_video_data.py "SESSDATA" "DedeUserID__ckMd5" "BV号"
```

> 脚本启动时会自动检测 `requests` 库是否已安装，如缺失则自动执行 `pip install requests`。

脚本返回JSON格式的视频数据，包含以下字段（所有比率字段均为数值类型）：

| 字段 | 含义 | 示例 |
|------|------|------|
| title | 视频标题 | "我的视频标题" |
| views | 播放量 | 12345 |
| likes | 点赞量 | 678 |
| favorites | 收藏量 | 234 |
| cover_click_rate | 封标点击率（星） | 3.0 |
| bounce_rate_3s | 3秒跳出率（%） | 32.02 |
| interaction_rate | 互动率（%） | 5.67 |
| fan_conversion_rate | 播转粉率（%） | 1.23 |
| tourist_ratio | 游客占比（%） | 45.67 |
| fan_view_rate | 粉丝观看率（%） | 54.33 |
| avg_play_completion_rate | 平均播放占总时长率（%） | 28.50 |
| stat_date | 统计日期 | 2026-05-20 |

判断返回结果：

- **`success` 为 `true`**：记录返回的JSON数据，继续 Step 4。
- **`success` 为 `false`**：
  - 停止执行
  - 提示用户检查BV号是否正确，或确认该视频是否在当前账号的创作中心中

**Stop condition**: 数据获取成功（`success=true`），或确认视频不可访问后停止。

### Step 4: 计算衍生指标

根据 Step 3 返回的数据计算（在后续步骤中作为计算列使用，无需单独调用脚本）：

- 收播率 = `favorites / views x 100%`
- 点赞率 = `likes / views x 100%`

> 这两个指标由 `update_feishu.py` 自动计算写入，Step 5 中无需手动计算。

**Stop condition**: 确认 Step 3 返回的数据中 `views > 0`（满足计算条件）。直接进入 Step 5。

### Step 5: 更新飞书表格

数据将输出到飞书云文档"几何节点视频数据"文件夹中。每个视频标题对应一个独立的飞书电子表格，多次爬取同一视频时自动追加新行。

**注意：** JSON 数据通过**标准输入（stdin）管道**传递，避免 shell 转义导致 JSON 损坏。切勿使用命令行参数传递 JSON。

运行飞书更新脚本：
```
echo 'JSON数据' | "Python路径" scripts/update_feishu.py "视频标题"
```

等效的PowerShell写法：
```
'JSON数据' | "Python路径" scripts/update_feishu.py "视频标题"
```

其中 `'JSON数据'` 是 Step 3 返回的完整JSON字符串（不带额外转义）。

**飞书表格列顺序（严格按照此顺序）：**

| 列号 | 字段名 | 类型 |
|------|--------|------|
| 1 | 统计日期 | 文本 |
| 2 | 播放量 | 整数 |
| 3 | 点赞量 | 整数 |
| 4 | 收藏量 | 整数 |
| 5 | 收播率(%) | 数值 |
| 6 | 点赞率(%) | 数值 |
| 7 | 封标点击率(星) | 数值 |
| 8 | 3秒跳出率(%) | 数值 |
| 9 | 互动率(%) | 数值 |
| 10 | 播转粉率(%) | 数值 |
| 11 | 游客占比(%) | 数值 |
| 12 | 粉丝观看率(%) | 数值 |
| 13 | 平均播放占总时长率(%) | 数值 |

脚本自动完成以下操作：
1. 检查飞书云空间中是否存在"几何节点视频数据"文件夹，不存在则自动创建
2. 在该文件夹下搜索与视频标题同名的电子表格
3. 表格不存在：创建新表格，写入表头和数据
4. 表格已存在：读取现有表格，将新数据追加为新的行

判断返回结果：
- **`success` 为 `true`**：记录飞书表格 URL，继续 Step 6。
- **`success` 为 `false`**：读取 `message` 中的错误信息，按以下规则处理：
  - 如果 `message` 包含"认证"或"token"或"auth"：提示用户运行 `lark-cli auth login` 重新认证。
  - 如果 `message` 包含"超时"或"Timeout"：提示稍后重试。
  - 其他情况：直接显示 `message` 内容给用户。

**Stop condition**: 飞书表格更新成功（`success=true`），或已向用户报告了明确的失败原因。

### Step 6: 输出结果

向用户报告最终结果：

- 视频标题
- 统计日期
- 飞书表格链接（可直接点击查看）
- 数据存储位置："几何节点视频数据"文件夹
- 如果是首次爬取：告知**已创建新表格**
- 如果是追加数据：告知**已追加新行**
- 确认所有数据均为数值类型，可直接在飞书中用于计算

**Stop condition**: 结果已完整输出给用户。

---

## Error Handling

Read `references/error-reference.md` when any execution step returns an error. Purpose: identify root cause and apply recovery action.

简要错误分类：

| 错误来源 | 常见原因 | 快速处理 |
|----------|----------|----------|
| Cookie | 不存在 / 失效 / 损坏 | 引导用户重新提供 |
| 视频数据 | BV号错误 / 无权访问 | 检查BV号 |
| 网络 | 请求失败 / 超时 | 重试，检查网络 |
| 飞书API | 认证失效 / 权限不足 | 检查 lark-cli 认证 |
| lark-cli | 超时 / Windows 找不到命令 / 返回嵌套结构不匹配 | 重试 / 使用 lark-cli.cmd / 检查返回结构 |
| JSON 传参 | 通过 argv 传递 JSON 导致 shell 转义损坏 | 改用 stdin 管道传递 |
| 飞书搜索 | 搜索结果在 data.results 中导致永远找不到已有资源 | v0.5.0 已修复（_deep_get） |

详细错误恢复步骤请见 `references/error-reference.md`。

---

## Resources

### scripts/

| 脚本 | 用途 | 关键参数 |
|------|------|----------|
| `cookie_manager.py` | Cookie持久化管理（load/save/delete/check） | `--sessdata`, `--dedeuserid_ckmd5` |
| `verify_cookie.py` | 验证Cookie是否有效 | SESSDATA, DedeUserID__ckMd5 |
| `fetch_video_data.py` | 爬取视频数据，自动安装 requests | SESSDATA, DedeUserID__ckMd5, BV号 |
| `update_feishu.py` | 更新飞书表格（JSON 数据通过 stdin 传递） | 视频标题（argv）, JSON数据（stdin） |

### references/

| 参考文件 | 内容 | 何时阅读 |
|----------|------|----------|
| `api_reference.md` | B站创作中心API文档（接口地址、响应字段、错误码） | 需要调试API时；或使用 `Read references/api_reference.md` when debugging API errors. Purpose: lookup endpoint details and error codes. |
| `error-reference.md` | 各错误场景的详细恢复步骤 | 执行中出现错误时 |
