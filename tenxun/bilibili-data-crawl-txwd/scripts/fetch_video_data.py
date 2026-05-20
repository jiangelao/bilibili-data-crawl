#!/usr/bin/env python3
"""爬取B站创作中心视频数据"""

import sys
import requests
import json
from datetime import datetime


def fetch_video_data(sessdata: str, dedeuserid_ckmd5: str, bvid: str, max_retries: int = 3) -> dict:
    """爬取指定视频的数据

    Args:
        sessdata: SESSDATA cookie值
        dedeuserid_ckmd5: DedeUserID__ckMd5 cookie值
        bvid: 视频BV号
        max_retries: 最大重试次数

    Returns:
        dict: 视频数据字典，所有比率字段均为 float 数值
    """
    cookies = {
        'SESSDATA': sessdata,
        'DedeUserID__ckMd5': dedeuserid_ckmd5,
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://member.bilibili.com/',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    # 标准化BV号
    bvid = bvid.strip()
    if not bvid.startswith('BV'):
        bvid = 'BV' + bvid

    result = {
        'success': False,
        'title': '',
        'views': 0,
        'likes': 0,
        'favorites': 0,
        'cover_click_rate': 0.0,       # 数值(星), 如 3.0
        'bounce_rate_3s': 0.0,         # 数值(百分比)
        'interaction_rate': 0.0,       # 数值(百分比)
        'fan_conversion_rate': 0.0,    # 数值(百分比)
        'tourist_ratio': 0.0,          # 数值(百分比)
        'fan_view_rate': 0.0,          # 数值(百分比)
        'avg_play_completion_rate': 0.0, # 数值(百分比)
        'stat_date': datetime.now().strftime('%Y-%m-%d'),
        'message': ''
    }

    for attempt in range(max_retries):
        try:
            # 1. 先获取视频基本信息
            video_info_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
            response = requests.get(video_info_url, cookies=cookies, headers=headers, timeout=15)
            response.raise_for_status()
            video_data = response.json()

            if video_data.get('code') != 0:
                result['message'] = f'获取视频信息失败：{video_data.get("message", "未知错误")}'
                continue

            data = video_data.get('data', {})
            result['title'] = data.get('title', '')
            result['views'] = data.get('stat', {}).get('view', 0)
            result['likes'] = data.get('stat', {}).get('like', 0)
            result['favorites'] = data.get('stat', {}).get('favorite', 0)

            # 2. 获取创作中心诊断对比数据
            diagnose_url = f'https://member.bilibili.com/x/web/data/archive_diagnose/compare?bvid={bvid}'
            try:
                response = requests.get(diagnose_url, cookies=cookies, headers=headers, timeout=15)
                response.raise_for_status()
                api_data = response.json()

                if api_data.get('code') == 0:
                    video_list = api_data.get('data', {}).get('list', [])
                    for item in video_list:
                        if item.get('bvid') == bvid:
                            stat = item.get('stat', {})
                            # 所有比率字段为整数值（万分比），除以100转换为百分比值
                            # 封标点击率（星级，值为整数的十分之一）
                            tm_star = stat.get('tm_star', 0)
                            result['cover_click_rate'] = tm_star / 10
                            # 3秒跳出率
                            crash_rate = stat.get('crash_rate', 0)
                            result['bounce_rate_3s'] = crash_rate / 100
                            # 互动率
                            interact_rate = stat.get('interact_rate', 0)
                            result['interaction_rate'] = interact_rate / 100
                            # 播转粉率
                            play_trans_fan = stat.get('play_trans_fan_rate', 0)
                            result['fan_conversion_rate'] = play_trans_fan / 100
                            # 粉丝观看率
                            play_fan_rate = stat.get('play_fan_rate', 0)
                            result['fan_view_rate'] = play_fan_rate / 100
                            # 游客占比 = 100% - 粉丝观看率
                            tourist = 10000 - play_fan_rate
                            result['tourist_ratio'] = tourist / 100
                            # 平均播放占总时长率
                            full_play_ratio = stat.get('full_play_ratio', 0)
                            result['avg_play_completion_rate'] = full_play_ratio / 100
                            break
            except requests.exceptions.RequestException:
                pass

            result['success'] = True
            result['message'] = '数据获取成功'
            return result

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                continue
            result['message'] = f'网络请求失败（已重试{max_retries}次）：{str(e)}'
            return result
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                continue
            result['message'] = f'响应解析失败：{str(e)}'
            return result

    return result


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(json.dumps({
            'success': False,
            'message': '参数不足，需要提供 SESSDATA、DedeUserID__ckMd5 和 BV号'
        }, ensure_ascii=False))
        sys.exit(1)

    sessdata = sys.argv[1]
    dedeuserid_ckmd5 = sys.argv[2]
    bvid = sys.argv[3]

    result = fetch_video_data(sessdata, dedeuserid_ckmd5, bvid)
    print(json.dumps(result, ensure_ascii=False))

    sys.exit(0 if result['success'] else 1)
