---
name: bilibili-creator-data
description: 爬取B站创作中心视频数据，包括播放量、点赞量、收藏量、封标点击率、3秒跳出率、互动率等，并保存到腾讯文档表格。数据存放在名为"几何节点视频数据"的文件夹中。支持Cookie持久化存储，仅在Cookie失效或不存在时才要求用户手动更新。触发方式：当用户需求涉及"爬取"、"抓取"、"b站"、"B站"、"哔哩哔哩"、"视频数据"、"创作中心"、"播放量"、"数据分析"等关键词或其近义词时，即可调用此skill。
---

# Bilibili Creator Data

## Overview

使用Cookie认证自动爬取B站创作中心视频数据，数据输出到腾讯文档的在线表格中，存放在名为"几何节点视频数据"的文件夹内，适用于定期追踪视频表现。Cookie会持久化存储到本地，无需每次手动输入。

**数据字段说明**：所有百分比字段（3秒跳出率、互动率、播转粉率等）在腾讯文档表格中存储为 **数值类型**，可直接用于后续计算。

## Trigger Conditions

当用户的请求包含以下任一类关键词（或其近义词/变体）时，触发此skill：

- **平台词**：b站、B站、哔哩哔哩、bilibili、Bilibili
- **动作词**：爬取、抓取、获取、拉取、采集、提取、导出、下载、查询
- **数据词**：视频数据、创作中心、播放量、数据分析、数据统计、视频表现、创作者数据、视频分析
- **组合示例**：
  - "帮我爬取B站视频数据"
  - "抓取一下b站的创作中心数据"
  - "获取哔哩哔哩的视频播放量"
  - "B站视频数据分析"
  - "导出B站视频统计"

如果用户仅提到"B站"但未涉及数据获取（如"B站怎么发视频"），则不触发此skill。

## Prerequisites

执行前确认以下信息：
1. 目标视频的BV号（如 BV1cNRWBzEkj）
2. 云环境已安装 `mcporter` 并完成腾讯文档认证（数据将输出到腾讯文档在线表格）

Cookie信息（SESSDATA 和 DedeUserID__ckMd5）优先从本地文件加载，仅在本地无Cookie或Cookie失效时才要求用户提供。

## Execution

### Step 1: 加载Cookie

先尝试从本地持久化文件加载Cookie。

运行Cookie加载脚本：
```
"正确的Python路径" scripts/cookie_manager.py load
```

> ⚠️ **Windows 注意事项**：Windows 系统自带的 `python3` 命令可能指向 Windows Apps Store 占位程序，导致异常退出（exit code 49）。**必须使用完整 Python 路径**（如 `D:/Dev_env/Python/Python3/python.exe`），或确认 `python` 命令可用。

判断返回结果：

- 如果 `success` 为 `true`：使用加载到的Cookie，跳到 Step 2。
- 如果 `success` 为 `false` 且 `message` 包含"不存在"：提示用户提供Cookie，然后执行保存操作：
  ```
  "Python路径" scripts/cookie_manager.py save --sessdata "SESSDATA值" --dedeuserid_ckmd5 "DedeUserID__ckMd5值"
  ```
  保存成功后继续 Step 2。
- 如果 `success` 为 `false` 且 `message` 包含"格式错误"或"不完整"：提示用户Cookie文件已损坏，需要删除后重新提供。先执行删除：
  ```
  "Python路径" scripts/cookie_manager.py delete
  ```
  然后提示用户提供新的Cookie并保存。

### Step 2: 验证Cookie有效性

使用已加载的Cookie验证登录状态。

```
"Python路径" scripts/verify_cookie.py "SESSDATA" "DedeUserID__ckMd5"
```

判断返回结果：

- 如果 `is_login` 为 `true`：记录用户名，继续 Step 3。
- 如果 `is_login` 为 `false`（Cookie失效）：
  1. 删除本地失效的Cookie文件：`"Python路径" scripts/cookie_manager.py delete`
  2. 提示用户："Cookie已失效，请重新登录B站并更新Cookie数据，需要提供 SESSDATA 和 DedeUserID__ckMd5"
  3. 等待用户提供新Cookie后，执行保存：`"Python路径" scripts/cookie_manager.py save --sessdata "新值" --dedeuserid_ckmd5 "新值"`
  4. 保存成功后重新验证，验证通过则继续 Step 3；仍然失败则停止执行。

### Step 3: 获取视频数据

使用Cookie爬取指定视频的数据。

```
"Python路径" scripts/fetch_video_data.py "SESSDATA" "DedeUserID__ckMd5" "BV号"
```

脚本会返回JSON格式的视频数据，包含以下字段（**所有比率字段均为数值类型**）：

- title: 视频标题
- views: 播放量
- likes: 点赞量
- favorites: 收藏量
- cover_click_rate: 封标点击率（数值，如 3.0 表示 3.0 星）
- bounce_rate_3s: 3秒跳出率（数值，如 32.02 表示 32.02%）
- interaction_rate: 互动率（数值）
- fan_conversion_rate: 播转粉率（数值）
- tourist_ratio: 游客占比（数值）
- fan_view_rate: 粉丝观看率（数值）
- avg_play_completion_rate: 平均播放占总时长率（数值）
- stat_date: 统计日期（YYYY-MM-DD格式）

如果视频不存在或无权访问：
- 停止执行
- 提示用户检查BV号是否正确，或确认该视频是否在当前账号的创作中心中

### Step 4: 计算衍生指标

根据获取的数据计算：
- 收播率 = 收藏量 / 播放量 × 100%
- 点赞率 = 点赞量 / 播放量 × 100%

### Step 5: 更新腾讯文档表格

**重要**：数据将输出到腾讯文档，存放在名为"几何节点视频数据"的文件夹中。每个视频标题对应一个独立的腾讯文档在线表格，多次爬取同一视频时自动追加新行。

**推荐方式（云端 Agent 直接使用 MCP 工具）**：

1. 首先搜索"几何节点视频数据"文件夹是否存在：
   - 使用 `mcporter call "tencent-docs" "manage.folder_list"` 查看根目录
   - 如果文件夹不存在，使用 `mcporter call "tencent-docs" "manage.create_file" --args '{"file_type":"folder","title":"几何节点视频数据"}'` 创建

2. 在该文件夹下搜索与视频标题同名的表格：
   - 使用 `mcporter call "tencent-docs" "manage.folder_list" --args '{"folder_id":"<文件夹ID>"}'`

3. 如果表格不存在：创建新表格
   - 使用 `mcporter call "tencent-docs" "manage.create_file" --args '{"file_type":"sheet","title":"<视频标题>","parent_id":"<文件夹ID>"}'`

4. 如果表格已存在：读取现有表格，将新数据追加为新的行
   - 使用 `mcporter call "tencent-docs" "sheet.get_sheet_info" --args '{"file_id":"<表格file_id>"}'` 获取 sheet_id
   - 使用 `mcporter call "tencent-docs" "sheet.set_range_value"` 写入数据

**备用方式（使用 Python 脚本）**：
   ```
   "Python路径" scripts/update_tencent_docs.py "视频标题" 'JSON数据'
   ```

脚本行为：
1. 检查腾讯文档中是否存在名为"几何节点视频数据"的文件夹，不存在则自动创建
2. 在该文件夹下搜索与视频标题同名的在线表格
3. 如果表格不存在：创建新表格，写入表头和数据
4. 如果表格已存在：读取现有表格，将新数据追加为新的行

**严格按照以下腾讯文档表格列顺序：**

| 列号 | 字段名 | 格式说明 |
|------|--------|----------|
| 1 | 统计日期 | 文本 |
| 2 | 播放量 | 整数 |
| 3 | 点赞量 | 整数 |
| 4 | 收藏量 | 整数 |
| 5 | 收播率(%) | 数值 |
| 6 | 点赞率(%) | 数值 |
| 7 | 封标点击率(星) | 数值，如 3.0 |
| 8 | 3秒跳出率(%) | 数值 |
| 9 | 互动率(%) | 数值 |
| 10 | 播转粉率(%) | 数值 |
| 11 | 游客占比(%) | 数值 |
| 12 | 粉丝观看率(%) | 数值 |
| 13 | 平均播放占总时长率(%) | 数值 |

### Step 6: 输出结果

向用户报告：
- 数据爬取成功的视频标题
- 统计日期
- 腾讯文档表格的链接（可直接点击查看）
- 说明数据存储在"几何节点视频数据"文件夹中
- 如果是首次爬取该视频：告知已创建新表格；如果是追加数据：告知已追加新行
- 确认所有数据均为数值类型，可在腾讯文档中直接用于计算

## Error Handling

Cookie文件不存在：
- 自动提示用户提供Cookie并保存到本地
- 保存后无需再次手动输入，后续执行自动加载

Cookie失效：
- 自动删除本地失效Cookie文件
- 提示用户重新登录B站并更新Cookie数据
- 用户更新后自动保存，后续执行自动加载

Cookie文件损坏：
- 提示用户文件格式错误
- 自动删除损坏文件
- 提示用户重新提供Cookie

视频不存在：
- 错误信息：视频不存在或无权访问，请检查BV号是否正确
- 解决方式：确认BV号正确且视频在当前账号的创作中心中

网络错误：
- 重试3次后仍失败，提示用户检查网络连接

腾讯文档API错误：
- 错误信息：腾讯文档API调用失败，请检查tencent-docs connector连接状态
- 解决方式：确认tencent-docs已正确配置并连接
- 文件夹创建失败：检查腾讯文档权限
- 表格写入失败：重试操作

## Resources

### scripts/

cookie_manager.py - Cookie持久化管理
- load: 从本地文件加载Cookie
- save: 保存Cookie到本地文件（需要 --sessdata 和 --dedeuserid_ckmd5 参数）
- delete: 删除本地Cookie文件
- check: 检查Cookie文件是否存在
- 存储路径: ~/.bilibili_cookie.json

verify_cookie.py - 验证Cookie有效性
- 输入：SESSDATA, DedeUserID__ckMd5
- 输出：登录状态（JSON格式）

fetch_video_data.py - 爬取视频数据
- 输入：SESSDATA, DedeUserID__ckMd5, BV号
- 输出：视频数据（JSON格式，所有比率字段为数值）

update_tencent_docs.py - 更新腾讯文档表格（已替代原 update_feishu.py）
- 输入：视频标题, JSON数据
- 输出：腾讯文档表格URL和状态
- 自动管理"几何节点视频数据"文件夹，每个视频独立表格，自动追加数据
- 使用腾讯文档 MCP 工具操作

### references/

api_reference.md - B站创作中心API文档
- 接口地址和参数说明
- 响应字段解释
- 错误码对照表
