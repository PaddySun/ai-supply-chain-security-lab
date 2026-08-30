# -*- coding: utf-8 -*-
"""Slopsquatting 实验配置。

支持任何 OpenAI 兼容端点（DeepSeek / 智谱 / 本地 ollama / vLLM 等）：
  设置环境变量 OPENAI_BASE_URL 和 OPENAI_API_KEY，
  或直接修改下方默认值。
"""
import os

# ---- 模型端点（OpenAI 兼容）----
# 例：DeepSeek  https://api.deepseek.com/v1
# 例：智谱      https://open.bigmodel.cn/api/paas/v4
# 例：本地      http://localhost:11434/v1   (ollama serve)
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("SLOP_MODEL", "deepseek-chat")

# ---- 实验参数（论文默认值的缩小版，本机可跑）----
N_PROMPTS = 20        # 使用多少个编码任务 prompt（论文：数千）
REPEATS = 5           # 每个 prompt 重复采样次数（论文：10）
TEMPERATURE = 0.7     # 论文使用非零温度以模拟真实使用
MAX_TOKENS = 1024

# ---- 注册表 ----
NPM_REGISTRY = "https://registry.npmjs.org"
PYPI_REGISTRY = "https://pypi.org/pypi"

# Node.js 内置模块白名单（不算第三方包）
NODE_BUILTIN = {
    "fs", "path", "http", "https", "url", "crypto", "os", "util", "events",
    "stream", "buffer", "child_process", "cluster", "zlib", "net", "dns",
    "tls", "readline", "repl", "vm", "worker_threads", "perf_hooks",
    "assert", "querystring", "string_decoder", "timers", "console",
    "process", "module", "punycode", "v8", "async_hooks", "dgram",
    "diagnostics_channel", "trace_events", "inspector", "constants",
}

# 标准库白名单（这些不算第三方包，避免误判为幻觉）
PY_STDLIB = {
    "os", "sys", "re", "json", "math", "time", "datetime", "random",
    "collections", "itertools", "functools", "pathlib", "typing",
    "subprocess", "logging", "argparse", "unittest", "asyncio",
    "urllib", "http", "socket", "threading", "hashlib", "base64",
    "csv", "io", "abc", "dataclasses", "enum", "sqlite3", "gzip",
    "shutil", "tempfile", "statistics", "string", "textwrap", "uuid",
    "secrets", "signal", "traceback", "warnings", "contextlib",
    "concurrent", "platform", "multiprocessing", "queue", "sched",
    "email", "html", "xml", "xmlrpc", "imaplib", "smtplib", "poplib",
    "ftplib", "telnetlib", "pdb", "profile", "cProfile", "timeit",
    "zoneinfo", "zoneinfo", "decimal", "fractions", "numbers",
    "array", "struct", "codecs", "encodings", "locale", "gettext",
    "pickle", "copyreg", "weakref", "types", "inspect", "ast",
    "symtable", "dis", "linecache", "fileinput", "glob", "fnmatch",
}
