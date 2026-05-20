#!/usr/bin/env python3
"""将B站视频数据写入飞书表格（替换原 update_excel.py 的 Excel 输出）"""

import sys
import json
import subprocess
import re
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


def call_lark(args: list) -> dict:
    """调用 lark-cli 并解析 JSON 输出"""
    result = subprocess.run(
        ['lark-cli'] + args,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return json.loads(result.stdout)


def extract_token_from_url(url: str, prefix: str) -> str:
    """从飞书 URL 中提取 token，例如 /sheets/shtXXX -> shtXXX"""
    m = re.search(rf'/{prefix}/([a-zA-Z0-9_]+)', url)
    return m.group(1) if m else ''


def ensure_folder() -> str:
    """确保「几何节点视频数据」文件夹存在，返回 folder_token"""
    result = call_lark([
        'drive', '+search',
        '--query', FOLDER_NAME,
        '--doc-types', 'folder',
        '--only-title',
        '--page-size', '5',
    ])
    for item in result.get('results', []):
        if item.get('title') == FOLDER_NAME:
            url = item.get('url', '')
            token = extract_token_from_url(url, 'folder')
            if token:
                return token

    # 文件夹不存在，创建它
    cr = call_lark(['drive', '+create-folder', '--name', FOLDER_NAME])
    return cr['folder_token']


def find_or_create_sheet(folder_token: str, title: str):
    """找到或创建飞书表格，返回 (spreadsheet_token, url, is_new)"""
    # 在指定文件夹内搜索同名表格
    result = call_lark([
        'drive', '+search',
        '--query', title,
        '--folder-tokens', folder_token,
        '--doc-types', 'sheet',
        '--only-title',
        '--page-size', '5',
    ])
    for item in result.get('results', []):
        if item.get('title') == title:
            url = item.get('url', '')
            token = extract_token_from_url(url, 'sheets')
            if token:
                return token, url, False

    # 不存在，创建新表格并放入指定文件夹
    cr = call_lark([
        'sheets', '+create',
        '--title', title,
        '--folder-token', folder_token,
    ])
    return cr['spreadsheet_token'], cr['url'], True


def get_first_sheet_id(spreadsheet_token: str) -> str:
    """获取电子表格的第一个工作表 ID"""
    info = call_lark(['sheets', '+info', '--spreadsheet-token', spreadsheet_token])
    return info['sheets'][0]['sheet_id']


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

        # 1. 确保「几何节点视频数据」文件夹存在
        folder_token = ensure_folder()

        # 2. 找到或创建以视频标题命名的飞书表格
        sheet_token, url, is_new = find_or_create_sheet(folder_token, title)

        # 3. 获取默认工作表 ID
        sheet_id = get_first_sheet_id(sheet_token)

        # 4. 写入 / 追加数据
        if is_new:
            # 新表格：同时写入表头和数据行
            call_lark([
                'sheets', '+write',
                '--spreadsheet-token', sheet_token,
                '--sheet-id', sheet_id,
                '--range', 'A1',
                '--values', json.dumps([HEADERS, row_data], ensure_ascii=False),
            ])
            msg = '已创建新飞书表格并写入初始数据'
        else:
            # 已有表格：追加新行
            call_lark([
                'sheets', '+append',
                '--spreadsheet-token', sheet_token,
                '--sheet-id', sheet_id,
                '--range', 'A1',
                '--values', json.dumps([row_data], ensure_ascii=False),
            ])
            msg = '已在现有飞书表格中追加新行'

        print(json.dumps({
            'success': True,
            'url': url,
            'spreadsheet_token': sheet_token,
            'message': f'{msg}，视频标题：{title}',
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
            'message': 'lark-cli 调用超时（60秒），请检查网络连接'
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
