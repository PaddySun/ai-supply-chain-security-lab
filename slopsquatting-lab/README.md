# Slopsquatting 本地复现实验

复现 USENIX Security 2025 论文《We Have a Package for You!》的核心实验：
测量 LLM 代码生成中的**包幻觉率**与**幻觉包名稳定性**（slopsquatting 的攻击前提）。

> ⚠️ 本实验只做**检测与度量**（防御研究）。不包含、也不应包含注册恶意包、
> 构造恶意安装脚本等武器化步骤。

## 环境准备

```bash
cd slopsquatting-lab
python -m venv .venv
.venv/Scripts/python -m pip install requests tqdm openai
```

已创建虚拟环境 `.venv`（Windows Git Bash 下用 `.venv/Scripts/python.exe` 调用）。

## 配置模型端点

任何 OpenAI 兼容端点均可（DeepSeek / 智谱 / ollama 本地模型）：

```bash
export OPENAI_API_KEY=sk-xxx
export OPENAI_BASE_URL=https://api.deepseek.com/v1   # 默认
export SLOP_MODEL=deepseek-chat                       # 默认
```

本地模型（不花钱、可测开源模型的高幻觉率）：

```bash
ollama serve
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export SLOP_MODEL=qwen2.5-coder:7b
```

## 运行

```bash
# Python 生态，10 个任务 × 3 次采样 ≈ 30 次调用
.venv/Scripts/python.exe run_experiment.py --ecosystem pypi --prompts 10 --repeats 3

# npm 生态
.venv/Scripts/python.exe run_experiment.py --ecosystem npm --prompts 10 --repeats 3
```

输出 `result_<ecosystem>_<ts>.json`，包含：

- 唯一包名总数 / 幻觉包数 / 含幻觉样本比例
- 幻觉包名完整列表
- 每个幻觉名在相同 prompt 重复采样中的出现次数（论文中 43% 复现率的本地版本）

## 文件结构

| 文件 | 作用 |
|---|---|
| `config.py` | 模型端点、实验参数、标准库白名单 |
| `prompts.py` | 编码任务 prompt 池（中英混合，覆盖 pypi/npm） |
| `extractor.py` | 从生成代码中提取 import/require 包名 |
| `registry.py` | npm/PyPI 存在性检查（带 JSON 持久缓存） |
| `run_experiment.py` | 主流程：采样 → 提取 → 比对 → 统计 |

## 结果解读

- **幻觉率**：论文数据 19.7%（16 模型平均）；2026 前沿模型约 1%~2%，自托管开源模型 6.8%~8.4%。
- **复现率是关键**：同一 prompt 反复采样仍出现相同幻觉名，说明幻觉可被攻击者"挖掘"，
  这是 slopsquatting 区别于随机错别字的攻击价值所在。
- 实验后可拿幻觉名去 npm/PyPI 搜索页面确认是否**已被真人抢注**（已有真实案例）。
