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

---

## 通用恢复流程

1. **读取错误信息**: 从脚本返回的 JSON 中获取 `message` 字段
2. **匹配错误来源**: 对照上表找到对应的错误类型
3. **执行恢复操作**: 按对应章节的恢复步骤操作
4. **重试当前步骤**: 恢复完成后，重新执行出错的 Step
5. **如果持续失败**: 向用户报告完整的错误信息，请求协助
