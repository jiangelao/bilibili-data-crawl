# B站创作中心API参考文档

## 认证方式

使用Cookie认证，需要以下Cookie：
- `SESSDATA`: 登录会话凭证（httpOnly）
- `DedeUserID__ckMd5`: 用户ID校验值

## API端点

### 1. 验证登录状态

**URL**: `https://api.bilibili.com/x/web-interface/nav`

**方法**: GET

**响应示例**:
```json
{
  "code": 0,
  "message": "0",
  "ttl": 1,
  "data": {
    "isLogin": true,
    "email_verified": 1,
    "face": "...",
    "level_info": {...},
    "mid": 123456,
    "mobile_verified": 1,
    "money": 0,
    "moral": 70,
    "official": {...},
    "officialVerify": {...},
    "pendant": {...},
    "scores": 0,
    "uname": "用户名",
    "vipDueDate": 0,
    "vipStatus": 0,
    "vipType": 0,
    "vip_pay_type": 0,
    "vip_theme_type": 0,
    "vip_label": {...},
    "vip_avatar_subscript": 0,
    "vip_nickname_color": "",
    "vip": {...},
    "wallet": {...},
    "has_shop": false,
    "shop_url": "",
    "answer_status": 0,
    "is_senior_member": 0
  }
}
```

### 2. 视频基本信息

**URL**: `https://api.bilibili.com/x/web-interface/view?bvid={bvid}`

**方法**: GET

**参数**:
- `bvid`: 视频BV号

**响应字段**:
- `data.title`: 视频标题
- `data.stat.view`: 播放量
- `data.stat.like`: 点赞量
- `data.stat.favorite`: 收藏量
- `data.stat.coin`: 投币数
- `data.stat.share`: 分享数
- `data.stat.reply`: 评论数
- `data.stat.danmaku`: 弹幕数

### 3. 创作中心视频诊断对比

**URL**: `https://member.bilibili.com/x/web/data/archive_diagnose/compare?bvid={bvid}`

**方法**: GET

**说明**: 获取视频的诊断数据，包括封标点击率、跳出率等指标

**响应字段**:
- `data.diagnose.cover_click`: 封标点击率
- `data.diagnose.bounce_rate`: 3秒跳出率
- `data.diagnose.interaction_rate`: 互动率
- `data.diagnose.fan_conversion`: 播转粉率
- `data.diagnose.tourist_ratio`: 游客占比
- `data.diagnose.fan_view_rate`: 粉丝观看率
- `data.diagnose.play_completion`: 平均播放占总时长率

### 4. 创作中心视频分析图表

**URL**: `https://member.bilibili.com/x/web/data/v2/archive/analyze/graph?bvid={bvid}`

**方法**: GET

**说明**: 获取视频的详细分析数据

## 错误码

| 错误码 | 说明 |
|--------|------|
| -101 | 账号未登录 |
| -111 | CSRF校验失败 |
| -400 | 请求错误 |
| -404 | 视频不存在 |
| -500 | 服务器错误 |
| 0 | 成功 |

## 数据字段说明

### 封标点击率
表示封面和标题的吸引力，通常显示为星级（如"2.9星"）或超过同类稿件的百分比。

### 3秒跳出率
用户在3秒内离开视频的比例，越低越好。

### 互动率
用户与视频互动的比例，包括点赞、评论、分享等。

### 播转粉率
观看视频后关注成为粉丝的比例。

### 游客占比
未登录用户观看的比例。

### 粉丝观看率
粉丝观看视频的比例。

### 平均播放占总时长率
用户平均观看视频时长的百分比。

### 收播率（计算值）
收藏量 / 播放量 × 100%

### 点赞率（计算值）
点赞量 / 播放量 × 100%


---

## lark-cli 命令返回结构参考

`update_feishu.py` 涉及的 lark-cli 命令及其返回结构如下：

### drive +search

搜索云空间资源。

```
lark-cli drive +search --query "名称" --doc-types "folder" --only-title --page-size 5
```

返回结构：
```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "results": [
      {"title": "几何节点视频数据", "url": "https://.../folder/xxx"}
    ]
  }
}
```

**关键**: 结果在 `data.results` 中，非顶层 `results`。

### drive +create-folder

创建文件夹。

```
lark-cli drive +create-folder --name "几何节点视频数据"
```

返回结构：
```json
{
  "data": {
    "folder_token": "xxx"
  }
}
```

或：
```json
{
  "folder_token": "xxx"
}
```

### sheets +create

创建电子表格。

```
lark-cli sheets +create --title "视频标题" --folder-token "xxx"
```

返回结构：
```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "spreadsheet": {
      "spreadsheet": {
        "token": "xxx",
        "url": "https://.../sheets/xxx",
        "title": "视频标题"
      }
    }
  }
}
```

**关键**: spreadsheet_token 在 `data.spreadsheet.spreadsheet.token`（3 层嵌套），非顶层 `spreadsheet_token`。

### sheets +info

获取电子表格信息。

```
lark-cli sheets +info --spreadsheet-token "xxx"
```

返回结构：
```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "sheets": {
      "sheets": [
        {"sheet_id": "xxx", "title": "Sheet1", "index": 0}
      ]
    },
    "spreadsheet": {
      "spreadsheet": {
        "token": "xxx",
        "title": "视频标题",
        "url": "https://.../sheets/xxx"
      }
    }
  }
}
```

**关键**: sheet_id 在 `data.sheets.sheets[0].sheet_id`（2 层嵌套）。

### sheets +write

写入数据到表格。

```
lark-cli sheets +write --spreadsheet-token "xxx" --sheet-id "xxx" --range "A1" --values "[[...]]"
```

返回：成功时通常返回 `{"ok": true}` 或空对象。stdout 可能为空，仅 stderr 包含 JSON。

### sheets +append

追加数据到表格。

```
lark-cli sheets +append --spreadsheet-token "xxx" --sheet-id "xxx" --range "A1" --values "[[...]]"
```

返回：同 `sheets +write`。
