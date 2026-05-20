#!/usr/bin/env python3
"""B站Cookie持久化管理模块

负责Cookie的本地存储、读取、验证和更新。
Cookie以JSON格式存储在skill目录内部，避免每次手动输入。

存储路径: <skill-dir>/scripts/.bilibili_cookie.json
"""

import json
import os
import sys
from pathlib import Path


# 默认Cookie存储路径（skill脚本所在目录，兼容云端Agent部署）
_DEFAULT_COOKIE_PATH = None


def _get_default_cookie_path() -> Path:
    """获取默认Cookie文件存储路径（动态解析，延迟到首次调用）

    Returns:
        Path: Cookie文件的完整路径，位于skill的scripts/目录下
    """
    global _DEFAULT_COOKIE_PATH
    if _DEFAULT_COOKIE_PATH is None:
        _DEFAULT_COOKIE_PATH = Path(__file__).resolve().parent / ".bilibili_cookie.json"
    return _DEFAULT_COOKIE_PATH


def get_cookie_path() -> Path:
    """获取Cookie文件存储路径

    Returns:
        Path: Cookie文件的完整路径
    """
    return _get_default_cookie_path()


def save_cookie(sessdata: str, dedeuserid_ckmd5: str, cookie_path: str = None) -> dict:
    """保存Cookie到本地文件

    Args:
        sessdata: SESSDATA cookie值
        dedeuserid_ckmd5: DedeUserID__ckMd5 cookie值
        cookie_path: 可选的自定义存储路径

    Returns:
        dict: 操作结果 {success, message, path}
    """
    path = Path(cookie_path) if cookie_path else _get_default_cookie_path()

    try:
        cookie_data = {
            "sessdata": sessdata,
            "dedeuserid_ckmd5": dedeuserid_ckmd5,
            "updated_at": __import__('datetime').datetime.now().isoformat()
        }

        path.write_text(json.dumps(cookie_data, ensure_ascii=False, indent=2), encoding='utf-8')

        return {
            "success": True,
            "message": f"Cookie已保存到 {path}",
            "path": str(path)
        }
    except PermissionError:
        return {
            "success": False,
            "message": f"无权限写入文件：{path}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"保存Cookie失败：{str(e)}"
        }


def load_cookie(cookie_path: str = None) -> dict:
    """从本地文件加载Cookie

    Args:
        cookie_path: 可选的自定义存储路径

    Returns:
        dict: {success, sessdata, dedeuserid_ckmd5, message}
              如果文件不存在或格式错误，success为False
    """
    path = Path(cookie_path) if cookie_path else _get_default_cookie_path()

    if not path.exists():
        return {
            "success": False,
            "sessdata": "",
            "dedeuserid_ckmd5": "",
            "message": "Cookie文件不存在，需要用户提供Cookie"
        }

    try:
        content = path.read_text(encoding='utf-8')
        cookie_data = json.loads(content)

        sessdata = cookie_data.get("sessdata", "")
        dedeuserid_ckmd5 = cookie_data.get("dedeuserid_ckmd5", "")

        if not sessdata or not dedeuserid_ckmd5:
            return {
                "success": False,
                "sessdata": "",
                "dedeuserid_ckmd5": "",
                "message": "Cookie文件内容不完整，缺少SESSDATA或DedeUserID__ckMd5"
            }

        return {
            "success": True,
            "sessdata": sessdata,
            "dedeuserid_ckmd5": dedeuserid_ckmd5,
            "updated_at": cookie_data.get("updated_at", "未知"),
            "message": f"已从本地加载Cookie（更新时间：{cookie_data.get('updated_at', '未知')}）"
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "sessdata": "",
            "dedeuserid_ckmd5": "",
            "message": "Cookie文件格式错误，请删除后重新提供Cookie"
        }
    except Exception as e:
        return {
            "success": False,
            "sessdata": "",
            "dedeuserid_ckmd5": "",
            "message": f"读取Cookie失败：{str(e)}"
        }


def delete_cookie(cookie_path: str = None) -> dict:
    """删除本地Cookie文件

    Args:
        cookie_path: 可选的自定义存储路径

    Returns:
        dict: 操作结果
    """
    path = Path(cookie_path) if cookie_path else _get_default_cookie_path()

    if not path.exists():
        return {
            "success": True,
            "message": "Cookie文件不存在，无需删除"
        }

    try:
        path.unlink()
        return {
            "success": True,
            "message": f"Cookie文件已删除：{path}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"删除Cookie文件失败：{str(e)}"
        }


def cookie_exists(cookie_path: str = None) -> bool:
    """检查Cookie文件是否存在

    Args:
        cookie_path: 可选的自定义存储路径

    Returns:
        bool: Cookie文件是否存在
    """
    path = Path(cookie_path) if cookie_path else _get_default_cookie_path()
    return path.exists()


if __name__ == '__main__':
    # CLI接口
    import argparse

    parser = argparse.ArgumentParser(description="B站Cookie管理工具")
    parser.add_argument("action", choices=["save", "load", "delete", "check"],
                        help="操作：save(保存) / load(读取) / delete(删除) / check(检查是否存在)")
    parser.add_argument("--sessdata", help="SESSDATA值（save时必填）")
    parser.add_argument("--dedeuserid_ckmd5", help="DedeUserID__ckMd5值（save时必填）")
    parser.add_argument("--path", help="自定义Cookie文件路径")

    args = parser.parse_args()

    if args.action == "save":
        if not args.sessdata or not args.dedeuserid_ckmd5:
            print(json.dumps({"success": False, "message": "save操作需要 --sessdata 和 --dedeuserid_ckmd5 参数"},
                             ensure_ascii=False))
            sys.exit(1)
        result = save_cookie(args.sessdata, args.dedeuserid_ckmd5, args.path)
    elif args.action == "load":
        result = load_cookie(args.path)
    elif args.action == "delete":
        result = delete_cookie(args.path)
    elif args.action == "check":
        exists = cookie_exists(args.path)
        result = {"success": True, "exists": exists,
                  "message": f"Cookie文件{'存在' if exists else '不存在'}：{get_cookie_path()}"}

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("success", False) else 1)
