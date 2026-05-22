# 错误参考文档

当执行 `bilibili-creator-data` skill 的任何步骤返回错误时，查阅此文档确定根因并执行恢复操作。

---

## Cookie 错误

### Cookie 文件不存在

- **症状**: `cookie_manager.py load` 返回 `success: false`, `message` 包含"不存在"
- **根因**: 首次使用或 Cookie 文件被删除
- **恢复**:
  1. 提示用户提供 B站 SESSDATA 和 DedeUserID__ckMd5
  2. 执行 `cookie_manager.py save --sessdata "值" --dedeuserid_ckmd5 "值"`
  3. 保存成功后自动加载

### Cookie 已失效

- **症状**: `verify_cookie.py` 返回 `is_login: false`
- **根因**: B站会话过期（通常数月后失效）
- **恢复**:
  1. 执行 `cookie_manager.py delete` 删除失效文件
  2. 提示用户重新登录 B站 并提供新的 SESSDATA 和 DedeUserID__ckMd5
  3. 执行 `cookie_manager.py save --sessdata "新值" --dedeuserid_ckmd5 "新值"`
  4. 重新验证新 Cookie

### Cookie 文件损坏

- **症状**: `cookie_manager.py load` 返回 `success: false`, `message` 包含"格式错误"
- **根因**: 文件被手动修改或写入不完整
- **恢复**:
  1. 执行 `cookie_manager.py delete` 删除损坏文件
  2. 提示用户重新提供 Cookie 并保存

### Cookie 内容不完整

- **症状**: `cookie_manager.py load` 返回 `success: false`, `message` 包含"不完整"
- **根因**: 缺少 SESSDATA 或 DedeUserID__ckMd5 字段
- **恢复**:
  1. 执行 `cookie_manager.py delete` 删除不完整文件
  2. 提示用户重新提供完整的 Cookie 数据

---

## 视频数据错误

### 视频不存在

- **症状**: `fetch_video_data.py` 返回 `success: false`, B站 API 返回 -404
- **根因**: BV号错误，或视频已被删除
- **恢复**:
  1. 提示用户检查 BV号 是否正确
  2. 确认该视频是否在当前账号的创作中心中
  3. 如果 BV号 确认正确但无权访问，可能视频不属于当前账号

### 无权访问

- **症状**: `fetch_video_data.py` 返回 `success: false`, B站 API 返回非 0 code
- **根因**: 视频不属于当前创作者账号
- **恢复**:
  1. 确认登录账号与视频创作者账号一致
  2. 确认视频未设置为私密

### 缺少 requests 依赖

- **症状**: `fetch_video_data.py` 启动时报错 "No module named 'requests'"
- **根因**: Python 环境中未安装 requests 库
- **恢复**:
  - 脚本已内置自动安装逻辑（`pip install requests`），通常无需手动处理
  - 如果自动安装失败（如网络受限或无 pip 权限），手动执行：
    ```
    pip install requests
    ```
    或使用完整 Python 路径：
    ```
    "Python路径" -m pip install requests
    ```

---

## 网络错误

### API 请求失败

- **症状**: 任意脚本返回网络相关错误
- **根因**: 网络连接不稳定，或 B站 API 临时不可用
- **恢复**:
  1. `fetch_video_data.py` 内置最多 3 次自动重试
  2. 如果 3 次重试后仍失败：提示用户检查网络连接
  3. 确认可以访问 `api.bilibili.com` 和 `member.bilibili.com`

### 请求超时

- **症状**: 脚本超时退出
- **根因**: 网络慢或 B站 API 响应慢
- **恢复**:
  1. 稍后重试
  2. 如持续超时，检查网络连接

---

## JSON 传参错误（v0.4.0 新增）

### JSON 数据因 shell 转义损坏

- **症状**: `update_feishu.py` 返回 JSON 解析错误，或在 Step 3 输出正常但 Step 5 报 JSON 格式错误
- **根因**: 通过命令行参数（argv）传递 JSON 字符串时，shell 对引号、反斜杠等特殊字符进行了转义，导致 JSON 结构损坏
- **恢复**:
  1. 确保 Step 5 通过 **stdin（标准输入管道）** 传递 JSON 数据，而非命令行参数
  2. 正确的调用方式：
     ```
     echo '{"title":"...","views":123}' | "Python路径" scripts/update_feishu.py "视频标题"
     ```
  3. 不要使用以下错误方式：
     ```
     "Python路径" scripts/update_feishu.py "视频标题" '{"title":"...","views":123}'  # 错误！
     ```
  4. 如果 JSON 中包含单引号，确保在传递前已完成正确转义

---

## 飞书/Feishu 错误

### lark-cli 认证失效

- **症状**: `update_feishu.py` 返回飞书 API 认证错误
- **根因**: lark-cli token 过期或未认证
- **恢复**:
  1. 运行 `lark-cli auth login` 重新认证
  2. 确认使用正确的飞书账号

### 文件夹创建失败

- **症状**: `update_feishu.py` 无法创建"几何节点视频数据"文件夹
- **根因**: 飞书云空间权限不足
- **恢复**:
  1. 确认账号有云空间写入权限
  2. 手动在飞书云空间中创建"几何节点视频数据"文件夹

### 表格写入失败

- **症状**: `update_feishu.py` 写入表格时返回错误
- **根因**: 飞书 API 临时错误或表格锁定
- **恢复**:
  1. 重试操作
  2. 如果持续失败，检查飞书服务状态

### lark-cli 超时

- **症状**: `update_feishu.py` 返回 TimeoutExpired 错误
- **根因**: 网络连接到飞书服务缓慢
- **恢复**:
  1. 确认网络连接正常
  2. 稍后重试
  3. 如果持续超时，检查飞书服务状态或使用 `lark-cli` 直连测试

### lark-cli 返回空输出或非 JSON 输出

- **症状**: `update_feishu.py` 在解析 lark-cli 输出时报错
- **根因**: lark-cli 部分命令（如 sheets +write）在成功时 stdout 可能为空，或 stderr 包含诊断信息
- **恢复**:
  - 脚本已内置 stderr 回退解析逻辑，通常无需手动处理
  - 如果持续失败，尝试直接运行 lark-cli 命令查看原生输出：
    ```
    lark-cli sheets +info --spreadsheet-token "xxx"
    ```

### lark-cli 返回结构与预期不符

- **症状**: 脚本报错如 "未找到 spreadsheet_token" 或 "工作表列表为空"
- **根因**: lark-cli 某些命令的 JSON 返回结构有多种嵌套层级：
  - 直接格式：`{"spreadsheet_token": "xxx"}`
  - 单层包裹：`{"data": {"spreadsheet_token": "xxx"}}`
  - 深层嵌套：`{"data": {"spreadsheet": {"spreadsheet": {"token": "xxx"}}}}`（`sheets +create`）
  - 双层嵌套：`{"data": {"sheets": {"sheets": [{"sheet_id": "xxx"}]}}}`（`sheets +info`）
- **恢复**:
  - 脚本 v0.5.0 使用 `_deep_get()` 函数通过 key 路径（如 `"data.spreadsheet.spreadsheet.token"`）支持多层嵌套
  - 如果仍失败，手动运行命令检查原生返回结构：
    ```
    lark-cli sheets +info --spreadsheet-token "xxx"
    lark-cli sheets +create --title "测试" --folder-token "xxx"
    lark-cli drive +search --query "xxx" --doc-types "folder" --only-title
    ```

### 重复创建文件夹/表格（v0.5.0 修复）

- **症状**: 每次执行都新建一个"几何节点视频数据"文件夹，或在该文件夹下创建新的同名空表格，而非复用已有资源
- **根因**: `drive +search` 的返回结果嵌套在 `data.results` 中（而非顶层 `results`），旧版 `_extract_field()` 无法到达该层级，导致搜索永远返回空，每次都创建新资源
- **恢复**:
  - v0.5.0 已使用 `_deep_get(result, 'data.results', [])` 正确解析
  - 如果问题仍然出现，手动验证搜索：
    ```
    lark-cli drive +search --query "几何节点视频数据" --doc-types "folder" --only-title --page-size 5
    ```
  - 清理飞书云空间中重复的文件夹和空表格后，重新执行

### lark-cli 在 Windows 上找不到命令

- **症状**: `update_feishu.py` 报错 "找不到 lark-cli" 或 "[WinError 2] 系统找不到指定的文件"
- **根因**: Windows 上 `lark-cli` 是 `.cmd` 文件，`subprocess.run(['lark-cli'])` 无法直接执行
- **恢复**:
  - v0.5.0 已自动检测 `sys.platform == 'win32'` 并使用 `lark-cli.cmd` + `shell=True`
  - 如果持续失败，确认安装路径：
    ```
    where.exe lark-cli.cmd
    ```
  - 或者将 lark-cli.cmd 所在目录（通常为 `C:\Program Files\nodejs\node_global\`）添加到 PATH 环境变量

---

## 通用恢复流程

1. **读取错误信息**: 从脚本返回的 JSON 中获取 `message` 字段
2. **匹配错误来源**: 对照上表找到对应的错误类型
3. **执行恢复操作**: 按对应章节的恢复步骤操作
4. **重试当前步骤**: 恢复完成后，重新执行出错的 Step
5. **如果持续失败**: 向用户报告完整的错误信息，请求协助
