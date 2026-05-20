#!/usr/bin/env python3
"""验证B站Cookie有效性"""

import sys
import requests
import json


def verify_cookie(sessdata: str, dedeuserid_ckmd5: str) -> dict:
    """验证Cookie是否有效
    
    Args:
        sessdata: SESSDATA cookie值
        dedeuserid_ckmd5: DedeUserID__ckMd5 cookie值
        
    Returns:
        dict: 包含登录状态和用户信息的字典
    """
    cookies = {
        'SESSDATA': sessdata,
        'DedeUserID__ckMd5': dedeuserid_ckmd5,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
    }
    
    try:
        response = requests.get(
            'https://api.bilibili.com/x/web-interface/nav',
            cookies=cookies,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get('data', {}).get('isLogin', False):
            return {
                'success': True,
                'is_login': True,
                'username': data['data'].get('uname', ''),
                'mid': data['data'].get('mid', ''),
                'message': f"登录成功，用户：{data['data'].get('uname', '')}"
            }
        else:
            return {
                'success': False,
                'is_login': False,
                'username': '',
                'mid': '',
                'message': 'Cookie已失效，请重新登录B站并更新Cookie数据'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'is_login': False,
            'username': '',
            'mid': '',
            'message': f'网络请求失败：{str(e)}'
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'is_login': False,
            'username': '',
            'mid': '',
            'message': f'响应解析失败：{str(e)}'
        }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(json.dumps({
            'success': False,
            'message': '参数不足，需要提供 SESSDATA 和 DedeUserID__ckMd5'
        }, ensure_ascii=False))
        sys.exit(1)
    
    sessdata = sys.argv[1]
    dedeuserid_ckmd5 = sys.argv[2]
    
    result = verify_cookie(sessdata, dedeuserid_ckmd5)
    print(json.dumps(result, ensure_ascii=False))
    
    sys.exit(0 if result['success'] else 1)
