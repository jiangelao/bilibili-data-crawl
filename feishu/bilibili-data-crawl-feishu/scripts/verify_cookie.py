#!/usr/bin/env python3
"""验证B站Cookie有效性"""

import sys
import json
import requests
from typing import Any


def verify_cookie(sessdata: str, dedeuserid_ckmd5: str) -> dict[str, Any]:
    """验证Cookie是否有效。

    调用 B站 `x/web-interface/nav` 接口检测登录状态。

    Args:
        sessdata: SESSDATA cookie值。
        dedeuserid_ckmd5: DedeUserID__ckMd5 cookie值。

    Returns:
        dict: 包含登录状态和用户信息的字典。
    """
    cookies: dict[str, str] = {
        'SESSDATA': sessdata,
        'DedeUserID__ckMd5': dedeuserid_ckmd5,
    }

    headers: dict[str, str] = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Referer': 'https://www.bilibili.com/',
    }

    try:
        response = requests.get(
            'https://api.bilibili.com/x/web-interface/nav',
            cookies=cookies,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()

        # B站 API code 不为 0 表示接口级别错误
        api_code = data.get('code', -1)
        if api_code != 0:
            return {
                'success': False,
                'is_login': False,
                'username': '',
                'mid': '',
                'message': f'B站API返回错误 (code={api_code}): {data.get("message", "未知错误")}',
            }

        nav_data = data.get('data', {})
        if nav_data.get('isLogin', False):
            return {
                'success': True,
                'is_login': True,
                'username': nav_data.get('uname', ''),
                'mid': nav_data.get('mid', ''),
                'message': f"登录成功，用户：{nav_data.get('uname', '')}",
            }
        else:
            return {
                'success': False,
                'is_login': False,
                'username': '',
                'mid': '',
                'message': 'Cookie已失效，请重新登录B站并更新Cookie数据',
            }

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'is_login': False,
            'username': '',
            'mid': '',
            'message': '网络请求超时（10秒），请检查网络连接',
        }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'is_login': False,
            'username': '',
            'mid': '',
            'message': f'网络请求失败：{str(e)}',
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'is_login': False,
            'username': '',
            'mid': '',
            'message': f'响应解析失败：{str(e)}',
        }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        result: dict[str, Any] = {
            'success': False,
            'message': '参数不足，需要提供 SESSDATA 和 DedeUserID__ckMd5',
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    sessdata: str = sys.argv[1]
    dedeuserid_ckmd5: str = sys.argv[2]

    result = verify_cookie(sessdata, dedeuserid_ckmd5)
    print(json.dumps(result, ensure_ascii=False))

    sys.exit(0 if result.get('success', False) else 1)
