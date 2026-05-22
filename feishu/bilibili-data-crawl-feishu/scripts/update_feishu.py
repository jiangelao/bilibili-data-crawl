#!/usr/bin/env python3
"""将B站视频数据写入飞书表格（v0.6.0）

★ v0.6.0 修复搜索命令错误（2026-05-21）
1. 修复：使用 lark-cli docs +search 替代不存在的 drive +search
2. 修复：移除 --only-title 和 --folder-tokens 参数（docs +search 不支持）
3. 修复：doc_types 过滤改为客户端过滤（API 不支持该参数）
"""

import sys
import json
import subprocess
import re
from datetime import datetime
from typing import Any


# 严格按照 skill 规范定义的列顺序
HEADERS: list[str] = [
    '统计日期',
    '播放量',
    '点赞量',
    '收藏量',
    '收播率(%)',
    '点赞率(%)',
    '封标点击率(星)',
    '3秒跳出率(%)',
    '互动率(%)',
    '播转粉率(%)',
    '游客占比(%)',
    '粉丝观看率(%)',
    '平均播放占总时长率(%)',
]

FOLDER_NAME: str = '几何节点视频数据'

# 列数 = len(HEADERS) = 13
_COL_RANGE_WRITE = 'A1:M2'   # 写入：2行（表头+数据行）× 13列


# ============================================================
# 工具函数
# ============================================================

def _deep_get(obj: Any, key_path: str, default: Any = None) -> Any:
    """对嵌套 dict 进行深层键路径查找。"""
    if not isinstance(obj, dict):
        return default
    keys: list[str] = key_path.split('.')
    current: Any = obj
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    return current


def _strip_html(text: str) -> str:
    """去除字符串中的 HTML 标签，如 '<h>文本</h>' -> '文本'"""
    return re.sub(r'<[^>]+>', '', text)


def call_lark(args: list[str]) -> dict[str, Any]:
    """调用 lark-cli 并智能解析输出。

    Windows 兼容: 使用 lark-cli.cmd + shell=True。
    """
    if sys.platform == 'win32':
        cmd_list: list[str] = ['lark-cli.cmd'] + args
        run_kwargs: dict[str, Any] = {'shell': True}
    else:
        cmd_list = ['lark-cli'] + args
        run_kwargs = {}

    try:
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=60,
            **run_kwargs,
        )
    except FileNotFoundError:
        return {
            '_error': f'找不到 lark-cli，请确认已安装（命令: {cmd_list[0]}）',
            '_exit_code': -1,
        }

    stdout_text: str = (result.stdout or '').strip()
    if stdout_text:
        try:
            return json.loads(stdout_text)
        except json.JSONDecodeError:
            pass

    stderr_text: str = (result.stderr or '').strip()
    if stderr_text:
        try:
            return json.loads(stderr_text)
        except json.JSONDecodeError:
            pass

    return {
        '_raw_stdout': stdout_text,
        '_raw_stderr': stderr_text,
        '_exit_code': result.returncode,
    }


def calculate_rates(data: dict[str, Any]) -> dict[str, float]:
    views: int = data.get('views', 0) or 0
    likes: int = data.get('likes', 0) or 0
    favorites: int = data.get('favorites', 0) or 0
    result: dict[str, float] = {}
    if views > 0:
        result['favorite_rate'] = round(favorites / views * 100, 2)
        result['like_rate'] = round(likes / views * 100, 2)
    else:
        result['favorite_rate'] = 0.0
        result['like_rate'] = 0.0
    return result


def build_row(data: dict[str, Any]) -> list[Any]:
    rates: dict[str, float] = calculate_rates(data)
    return [
        data.get('stat_date', datetime.now().strftime('%Y-%m-%d')),
        data.get('views', 0),
        data.get('likes', 0),
        data.get('favorites', 0),
        rates['favorite_rate'],
        rates['like_rate'],
        data.get('cover_click_rate', 0.0),
        data.get('bounce_rate_3s', 0.0),
        data.get('interaction_rate', 0.0),
        data.get('fan_conversion_rate', 0.0),
        data.get('tourist_ratio', 0.0),
        data.get('fan_view_rate', 0.0),
        data.get('avg_play_completion_rate', 0.0),
    ]


# ============================================================
# lark-cli 驱动函数 - 飞书搜索/创建操作
# ============================================================

def _match_search_result(item: dict[str, Any], expected_title: str, expected_type: str) -> bool:
    """判断 docs +search 返回项是否匹配标题和类型。

    返回结构: {title_highlighted: "<h>标题</h>", result_meta: {doc_types: "FOLDER", token: "xxx", url: "..."}}
    """
    meta: dict[str, Any] = item.get('result_meta', {}) if isinstance(item.get('result_meta'), dict) else {}
    if meta.get('doc_types', '') != expected_type:
        return False
    raw_title: str = item.get('title_highlighted', '') or ''
    clean_title: str = _strip_html(raw_title).strip()
    return clean_title == expected_title


def _get_result_meta_token(item: dict[str, Any]) -> str:
    meta: dict[str, Any] = item.get('result_meta', {}) if isinstance(item.get('result_meta'), dict) else {}
    return meta.get('token', '') or ''


def _get_result_meta_url(item: dict[str, Any]) -> str:
    meta: dict[str, Any] = item.get('result_meta', {}) if isinstance(item.get('result_meta'), dict) else {}
    return meta.get('url', '') or ''


def _search_docs(
    query: str,
    doc_types: str,
    *,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """搜索飞书云空间，返回匹配的 results 列表。

    使用 docs +search 命令（drive +search 不存在）。
    doc_types 过滤在返回后手动处理（API 不支持 --doc-types 参数）。
    """
    args: list[str] = [
        'docs', '+search',
        '--query', query,
        '--page-size', str(page_size),
    ]

    result: dict[str, Any] = call_lark(args)
    # 实际返回结构: {"ok": true, "data": {"results": [...]}}
    results: list[dict[str, Any]] = _deep_get(result, 'data.results', [])

    # 按 doc_types 过滤
    filtered: list[dict[str, Any]] = []
    for item in results:
        meta: dict[str, Any] = item.get('result_meta', {}) if isinstance(item.get('result_meta'), dict) else {}
        if meta.get('doc_types', '') == doc_types:
            filtered.append(item)
    return filtered


def _find_matching_item(
    results: list[dict[str, Any]],
    expected_title: str,
    expected_type: str,
) -> tuple[str, str]:
    """在搜索结果列表中查找匹配项，返回 (token, url)。"""
    for item in results:
        if _match_search_result(item, expected_title, expected_type):
            token: str = _get_result_meta_token(item)
            url: str = _get_result_meta_url(item)
            if token:
                return token, url
    return '', ''


def ensure_folder() -> str:
    """确保「几何节点视频数据」文件夹存在。"""
    results: list[dict[str, Any]] = _search_docs(FOLDER_NAME, 'FOLDER', page_size=20)
    token, _ = _find_matching_item(results, FOLDER_NAME, 'FOLDER')
    if token:
        return token

    # 都没找到 -> 新建
    cr: dict[str, Any] = call_lark([
        'drive', '+create-folder', '--name', FOLDER_NAME,
    ])

    folder_token: str | None = _deep_get(cr, 'data.folder_token')
    if not folder_token:
        folder_token = cr.get('folder_token', '')
    if not folder_token:
        raise Exception(f'创建文件夹失败：{json.dumps(cr, ensure_ascii=False)}')
    return folder_token


def _search_sheet_anywhere(title: str) -> tuple[str, str]:
    """搜索指定标题的表格，返回 (token, url)。"""
    results = _search_docs(title, 'SHEET', page_size=20)
    token, url = _find_matching_item(results, title, 'SHEET')
    if token:
        return token, url

    return '', ''


def find_or_create_sheet(folder_token: str, title: str) -> tuple[str, str, bool]:
    """找到或创建飞书表格，返回 (spreadsheet_token, url, is_new)。"""
    token, url = _search_sheet_anywhere(title)
    if token:
        return token, url, False

    cr: dict[str, Any] = call_lark([
        'sheets', '+create',
        '--title', title,
        '--folder-token', folder_token,
    ])

    spreadsheet_token: str | None = _deep_get(cr, 'data.spreadsheet_token')
    if not spreadsheet_token:
        spreadsheet_token = cr.get('spreadsheet_token', '')
    if not spreadsheet_token:
        raise Exception(f'创建表格失败：{json.dumps(cr, ensure_ascii=False)}')

    url = _deep_get(cr, 'data.url', '')
    if not url:
        url = cr.get('url', '')

    return spreadsheet_token, url, True


def get_first_sheet_id(spreadsheet_token: str) -> str:
    """获取电子表格的第一个工作表 ID。"""
    info: dict[str, Any] = call_lark([
        'sheets', '+info',
        '--spreadsheet-token', spreadsheet_token,
    ])

    sheets_list: list[dict[str, Any]] = _deep_get(info, 'data.sheets.sheets', [])
    if not sheets_list:
        sheets_container = info.get('sheets', {})
        if isinstance(sheets_container, dict):
            sheets_list = sheets_container.get('sheets', [])

    if not sheets_list:
        raise Exception(f'工作表列表为空：{json.dumps(info, ensure_ascii=False)}')

    sheet_id: str = sheets_list[0].get('sheet_id', '')
    if not sheet_id:
        raise Exception(f'未找到 sheet_id：{json.dumps(sheets_list[0], ensure_ascii=False)}')
    return sheet_id


# ============================================================
# 主流程
# ============================================================

def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'message': '参数不足，需要 视频标题。JSON数据请通过stdin传递'}, ensure_ascii=False))
        sys.exit(1)

    title: str = sys.argv[1]

    try:
        data_json: str = sys.stdin.read().strip()
        if not data_json:
            print(json.dumps({'success': False, 'message': 'stdin 为空，请通过管道传递JSON数据'}, ensure_ascii=False))
            sys.exit(1)
        data: dict[str, Any] = json.loads(data_json)
    except json.JSONDecodeError as e:
        print(json.dumps({'success': False, 'message': f'stdin JSON 解析失败：{str(e)}'}, ensure_ascii=False))
        sys.exit(1)

    row_data: list[Any] = build_row(data)

    try:
        folder_token: str = ensure_folder()
        sheet_token, url, is_new = find_or_create_sheet(folder_token, title)
        sheet_id: str = get_first_sheet_id(sheet_token)

        if is_new:
            result = call_lark([
                'sheets', '+write',
                '--spreadsheet-token', sheet_token,
                '--sheet-id', sheet_id,
                '--range', _COL_RANGE_WRITE,
                '--values', json.dumps([HEADERS, row_data], ensure_ascii=False),
            ])
            if not result.get('ok', False):
                err_msg = result.get('error', {}).get('message', str(result))
                raise Exception(f'写入表格失败：{err_msg}')
            msg = '已创建新飞书表格并写入初始数据'
        else:
            # 读取A列（统计日期），找到最后一个有实际数据的行号
            read_result = call_lark([
                'sheets', '+read',
                '--spreadsheet-token', sheet_token,
                '--sheet-id', sheet_id,
                '--range', 'A:A',
            ])
            if not read_result.get('ok', False):
                err_msg = read_result.get('error', {}).get('message', str(read_result))
                raise Exception(f'读取表格失败：{err_msg}')

            values_col_a = _deep_get(read_result, 'data.valueRange.values', [])
            last_data_row = 1  # 表头在第1行
            for i, cell in enumerate(values_col_a):
                if cell and isinstance(cell, list) and len(cell) > 0 and cell[0] is not None and cell[0] != '':
                    last_data_row = i + 1  # 1-based row

            next_row = last_data_row + 1
            range_write = f'A{next_row}:M{next_row}'

            result = call_lark([
                'sheets', '+write',
                '--spreadsheet-token', sheet_token,
                '--sheet-id', sheet_id,
                '--range', range_write,
                '--values', json.dumps([row_data], ensure_ascii=False),
            ])
            if not result.get('ok', False):
                err_msg = result.get('error', {}).get('message', str(result))
                raise Exception(f'追加数据失败：{err_msg}')
            msg = f'已在现有飞书表格中追加新行（第{next_row}行）'

        print(json.dumps({'success': True, 'url': url, 'spreadsheet_token': sheet_token, 'message': f'{msg}，视频标题：{title}'}, ensure_ascii=False))
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(json.dumps({'success': False, 'message': 'lark-cli 调用超时（60秒），请检查网络连接后重试'}, ensure_ascii=False))
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(json.dumps({'success': False, 'message': f'JSON解析失败：{str(e)}'}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'success': False, 'message': f'飞书操作失败：{str(e)}'}, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
