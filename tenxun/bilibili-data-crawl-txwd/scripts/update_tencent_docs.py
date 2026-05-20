#!/usr/bin/env python3
"""将B站视频数据写入腾讯文档表格（替代原 update_feishu.py）"""

import sys
import json
import subprocess
from datetime import datetime

# 严格按照 skill 规范定义的列顺序
HEADERS = [
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

FOLDER_NAME = '几何节点视频数据'


def calculate_rates(data: dict) -> dict:
    """计算收播率和点赞率"""
    views = data.get('views', 0)
    likes = data.get('likes', 0)
    favorites = data.get('favorites', 0)

    result = {}
    if views > 0:
        result['favorite_rate'] = round(favorites / views * 100, 2)
        result['like_rate'] = round(likes / views * 100, 2)
    else:
        result['favorite_rate'] = 0.0
        result['like_rate'] = 0.0
    return result


def build_row(data: dict) -> list:
    """按 HEADERS 顺序构建数据行，百分比字段返回数值"""
    rates = calculate_rates(data)
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


def call_mcp(tool_name: str, args: dict = None, timeout: int = 60) -> dict:
    """调用腾讯文档 MCP 工具"""
    cmd = ['mcporter', 'call', 'tencent-docs', tool_name]
    if args:
        import shlex
        cmd.extend(['--args', shlex.quote(json.dumps(args))])
    else:
        cmd.extend(['--args', '{}'])

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.stdout:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {'raw': result.stdout, 'error': '', 'stderr': result.stderr}
    return {'error': result.stderr or 'No output', 'raw': result.stdout}


def call_mcp_with_json_args(tool_name: str, args: dict = None, timeout: int = 60) -> dict:
    """调用腾讯文档 MCP 工具（直接传递 JSON 参数）"""
    import shlex

    args_str = json.dumps(args) if args else '{}'
    cmd = ['mcporter', 'call', 'tencent-docs', tool_name, '--args', args_str]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    try:
        if result.stdout:
            return json.loads(result.stdout)
    except json.JSONDecodeError:
        pass
    return {'error': result.stderr or 'No output', 'raw': result.stdout}


def find_folder(folder_name: str) -> str:
    """搜索"几何节点视频数据"文件夹，返回 folder_id"""
    # 先搜索根目录
    result = call_mcp_with_json_args('manage.folder_list', {'folder_id': ''})
    if result and isinstance(result, list):
        for item in result:
            if item.get('name') == folder_name:
                return item.get('id', item.get('folder_id', ''))
    return None


def create_folder(folder_name: str) -> dict:
    """创建"几何节点视频数据"文件夹，返回 {folder_id, url}"""
    result = call_mcp_with_json_args('manage.create_file', {
        'file_type': 'folder',
        'title': folder_name
    })
    if result:
        return {
            'folder_id': result.get('file_id', result.get('folder_id', '')),
            'url': result.get('url', '')
        }
    return None


def find_file_in_folder(folder_id: str, file_name: str, file_type: str = 'sheet') -> dict:
    """在指定文件夹中搜索文件，返回 {file_id, url} 或 None"""
    result = call_mcp_with_json_args('manage.folder_list', {'folder_id': folder_id})
    if result and isinstance(result, list):
        for item in result:
            if item.get('name') == file_name:
                return {
                    'file_id': item.get('id', item.get('file_id', '')),
                    'url': item.get('url', '')
                }
    return None


def create_sheet(title: str, parent_id: str) -> dict:
    """创建腾讯文档在线表格，返回 {file_id, url}"""
    result = call_mcp_with_json_args('manage.create_file', {
        'file_type': 'sheet',
        'title': title,
        'parent_id': parent_id
    })
    if result:
        return {
            'file_id': result.get('file_id', ''),
            'url': result.get('url', '')
        }
    return None


def get_sheet_id(file_id: str) -> str:
    """获取在线表格的第一个工作表 ID"""
    result = call_mcp_with_json_args('sheet.get_sheet_info', {'file_id': file_id})
    if result and isinstance(result, dict):
        sheets = result.get('sheets', [])
        if sheets:
            return sheets[0].get('sheet_id', 'sheet0')
        # 尝试其他可能的字段名
        return result.get('sheet_id', result.get('id', 'sheet0'))
    return 'sheet0'


def get_sheet_row_count(file_id: str, sheet_id: str) -> int:
    """获取表格当前行数，用于追加数据"""
    result = call_mcp_with_json_args('sheet.get_sheet_info', {'file_id': file_id})
    if result and isinstance(result, dict):
        for sheet in result.get('sheets', []):
            if sheet.get('sheet_id') == sheet_id:
                return sheet.get('row_count', 0)
    return 0


def build_cell_values(headers: list, row_data: list, start_row: int = 0, is_new: bool = False) -> list:
    """构建单元格值列表"""
    values = []
    row_idx = start_row

    # 如果是新表格，先写入表头
    if is_new:
        for col_idx, header in enumerate(headers):
            values.append({
                'row': row_idx,
                'col': col_idx,
                'value_type': 'STRING',
                'string_value': str(header)
            })
        row_idx += 1

    # 写入数据行
    for col_idx, value in enumerate(row_data):
        if isinstance(value, str):
            values.append({
                'row': row_idx,
                'col': col_idx,
                'value_type': 'STRING',
                'string_value': value
            })
        elif isinstance(value, int):
            values.append({
                'row': row_idx,
                'col': col_idx,
                'value_type': 'NUMBER',
                'number_value': float(value)
            })
        elif isinstance(value, float):
            values.append({
                'row': row_idx,
                'col': col_idx,
                'value_type': 'NUMBER',
                'number_value': value
            })

    return values


def write_data(file_id: str, sheet_id: str, values: list) -> bool:
    """向表格写入数据"""
    result = call_mcp_with_json_args('sheet.set_range_value', {
        'file_id': file_id,
        'sheet_id': sheet_id,
        'values': values
    })
    return result and result.get('error') == ''


def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            'success': False,
            'message': '参数不足，需要 视频标题 JSON数据'
        }, ensure_ascii=False))
        sys.exit(1)

    title = sys.argv[1]
    data_json = sys.argv[2]

    try:
        data = json.loads(data_json)
        row_data = build_row(data)

        # 1. 搜索"几何节点视频数据"文件夹
        folder_id = find_folder(FOLDER_NAME)

        # 如果文件夹不存在，创建它
        if not folder_id:
            folder_result = create_folder(FOLDER_NAME)
            if folder_result:
                folder_id = folder_result.get('folder_id', '')
                folder_url = folder_result.get('url', '')
            else:
                print(json.dumps({
                    'success': False,
                    'message': '创建"几何节点视频数据"文件夹失败'
                }, ensure_ascii=False))
                sys.exit(1)

        # 2. 在文件夹中搜索同名表格
        existing_file = find_file_in_folder(folder_id, title)
        is_new = False
        file_id = ''
        url = ''

        if existing_file:
            file_id = existing_file.get('file_id', '')
            url = existing_file.get('url', '')
        else:
            # 创建新表格
            sheet_result = create_sheet(title, folder_id)
            if sheet_result:
                file_id = sheet_result.get('file_id', '')
                url = sheet_result.get('url', '')
                is_new = True
            else:
                print(json.dumps({
                    'success': False,
                    'message': f'创建表格"{title}"失败'
                }, ensure_ascii=False))
                sys.exit(1)

        # 3. 获取 sheet_id
        sheet_id = get_sheet_id(file_id)

        # 4. 写入数据
        if is_new:
            # 新表格：同时写入表头和数据行
            values = build_cell_values(HEADERS, row_data, start_row=0, is_new=True)
        else:
            # 已有表格：追加新行
            current_rows = get_sheet_row_count(file_id, sheet_id)
            values = build_cell_values(HEADERS, row_data, start_row=current_rows, is_new=False)

        success = write_data(file_id, sheet_id, values)

        if success:
            msg = f'已{"创建新腾讯文档表格并写入初始数据" if is_new else "在现有腾讯文档表格中追加新行"}，视频标题：{title}'
            print(json.dumps({
                'success': True,
                'url': url,
                'file_id': file_id,
                'message': msg,
            }, ensure_ascii=False))
        else:
            print(json.dumps({
                'success': False,
                'message': '写入数据失败'
            }, ensure_ascii=False))
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(json.dumps({
            'success': False,
            'message': f'JSON解析失败：{str(e)}'
        }, ensure_ascii=False))
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(json.dumps({
            'success': False,
            'message': 'mcporter 调用超时（60秒），请检查网络连接'
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            'success': False,
            'message': f'操作失败：{str(e)}'
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
