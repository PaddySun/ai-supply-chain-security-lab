# -*- coding: utf-8 -*-
"""从 LLM 生成的代码中提取第三方包名。"""
import re
import sys

# 权威标准库清单（Python 3.10+），比手写白名单可靠
PY_STDLIB = set(sys.stdlib_module_names) | {"__future__"}

from config import NODE_BUILTIN

# JavaScript: require('x') / import 'x' / import ... from 'x' / import('x')
JS_PATTERNS = [
    re.compile(r"""require\(\s*['"]([^'"\s]+)['"]\s*\)"""),
    re.compile(r"""import\s+['"]([^'"\s]+)['"]"""),
    re.compile(r"""from\s+['"]([^'"\s]+)['"]"""),
    re.compile(r"""import\(\s*['"]([^'"\s]+)['"]\s*\)"""),
]

# Python: import x / import x.y / from x import ...
PY_PATTERNS = [
    re.compile(r"^\s*import\s+([A-Za-z_][\w.]*)", re.M),
    re.compile(r"^\s*from\s+([A-Za-z_][\w.]*)\s+import", re.M),
]

PIP_ALIASES = {  # import 名 != pip 包名的常见映射
    "PIL": "pillow", "cv2": "opencv-python", "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn", "yaml": "pyyaml", "dotenv": "python-dotenv",
    "docx": "python-docx", "pptx": "python-pptx", "OpenSSL": "pyopenssl",
    "dateutil": "python-dateutil", "github": "pygithub",
}


def extract_js_packages(code: str) -> set[str]:
    pkgs = set()
    for pat in JS_PATTERNS:
        for m in pat.finditer(code):
            name = m.group(1)
            if name.startswith(".") or name.startswith("/"):
                continue  # 相对路径，不是包
            if name.startswith("@"):
                name = "/".join(name.split("/")[:2])  # @scope/pkg
            else:
                name = name.split("/")[0]
            pkgs.add(name)
    return pkgs - NODE_BUILTIN


def extract_py_packages(code: str) -> set[str]:
    mods = set()
    for pat in PY_PATTERNS:
        for m in pat.finditer(code):
            mods.add(m.group(1).split(".")[0])
    return {PIP_ALIASES.get(m, m) for m in mods if m not in PY_STDLIB}


def extract(code: str, ecosystem: str) -> set[str]:
    return extract_js_packages(code) if ecosystem == "npm" else extract_py_packages(code)
