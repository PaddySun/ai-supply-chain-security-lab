# -*- coding: utf-8 -*-
"""注册表存在性检查（带本地 JSON 缓存，避免重复打 npm/PyPI）。"""
import json
import os
import threading

import requests

from config import NPM_REGISTRY, PYPI_REGISTRY

CACHE_FILE = "registry_cache.json"
_lock = threading.Lock()


def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


_cache: dict = _load_cache()
_session = requests.Session()
_session.headers["User-Agent"] = "slopsquatting-research-lab/1.0 (defensive security research)"


def exists(package: str, ecosystem: str) -> bool:
    """返回包是否真实存在于注册表。结果持久缓存。"""
    key = f"{ecosystem}:{package}"
    with _lock:
        if key in _cache:
            return _cache[key]

    if ecosystem == "npm":
        url = f"{NPM_REGISTRY}/{package.replace('/', '%2F')}"
    else:
        url = f"{PYPI_REGISTRY}/{package}/json"
    try:
        r = _session.get(url, timeout=15)
        result = r.status_code == 200
    except requests.RequestException:
        result = None  # 网络错误：不算幻觉也不算存在，缓存为 unknown
        key += "?net"

    with _lock:
        if result is not None:
            _cache[f"{ecosystem}:{package}"] = result
        _save_cache(_cache)
    return bool(result)


def exists_many(packages: set[str], ecosystem: str) -> dict[str, bool]:
    return {p: exists(p, ecosystem) for p in sorted(packages)}
