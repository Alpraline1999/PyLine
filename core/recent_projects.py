"""
最近项目记录模块 - 持久保存最近打开的项目路径
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Dict, Optional


_RECENT_FILE = os.path.join(os.path.expanduser("~"), ".pyline_recent.json")
_MAX_RECENT = 10


def load_recent() -> List[Dict]:
    """
    读取最近项目列表。

    返回格式：
    [
      {"path": "/a/b/c.pyl", "name": "项目名", "opened_at": "2024-01-01T12:00:00"},
      ...
    ]
    按最新打开时间倒序排列。
    """
    if not os.path.exists(_RECENT_FILE):
        return []
    try:
        with open(_RECENT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        # 过滤掉已不存在的文件
        return [item for item in data if os.path.exists(item.get("path", ""))]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def add_recent(path: str, name: str) -> None:
    """
    添加（或更新）一条最近项目记录。
    若该 path 已存在则移到列表最前并更新时间；否则插入到最前。
    超过 _MAX_RECENT 条时丢弃末尾旧记录。
    """
    items = load_recent()
    # 移除已存在的同路径记录
    items = [item for item in items if item.get("path") != path]
    # 插入到最前
    items.insert(0, {
        "path": path,
        "name": name,
        "opened_at": datetime.now().isoformat(),
    })
    # 截断
    items = items[:_MAX_RECENT]
    _save(items)


def remove_recent(path: str) -> None:
    """移除指定路径的记录"""
    items = load_recent()
    items = [item for item in items if item.get("path") != path]
    _save(items)


def clear_recent() -> None:
    """清空最近项目列表"""
    _save([])


def _save(items: List[Dict]) -> None:
    try:
        with open(_RECENT_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # 忽略写入失败（权限问题等）
