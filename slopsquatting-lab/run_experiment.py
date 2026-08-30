# -*- coding: utf-8 -*-
"""Slopsquatting 复现实验主脚本。

流程（对应 USENIX Security 2025《We Have a Package for You!》方法论）：
  1. 用一组编码任务 prompt 让 LLM 生成代码（每 prompt 重复采样 REPEATS 次）
  2. 从代码中提取 import/require 的第三方包名
  3. 对比 npm / PyPI 注册表，找出不存在的"幻觉包"
  4. 统计：幻觉率、幻觉包名列表、同一 prompt 下幻觉名的复现率（稳定性）

用法：
  python run_experiment.py --ecosystem pypi --prompts 10 --repeats 3
  python run_experiment.py --ecosystem npm  --prompts 10 --repeats 3
"""
import argparse
import collections
import json
import time

from openai import OpenAI

import config
import prompts
from extractor import extract
from registry import exists_many


def sample(client, task: str) -> str:
    resp = client.chat.completions.create(
        model=config.MODEL,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
        messages=[
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ],
    )
    return resp.choices[0].message.content or ""


def run(ecosystem: str, n_prompts: int, repeats: int) -> dict:
    client = OpenAI(base_url=config.BASE_URL, api_key=config.API_KEY)
    tasks = prompts.TASKS[:n_prompts]

    # task -> [run_id -> (code, packages)]
    per_task: dict[str, list[set[str]]] = {}
    total = len(tasks) * repeats
    done = 0
    for task in tasks:
        runs = []
        for i in range(repeats):
            code = sample(client, task)
            pkgs = extract(code, ecosystem)
            runs.append(pkgs)
            done += 1
            print(f"[{done}/{total}] run{i + 1}: {len(pkgs)} 个包引用")
            time.sleep(0.3)
        per_task[task] = runs

    # 全局幻觉包集合
    all_pkgs: set[str] = set().union(*[s for runs in per_task.values() for s in runs])
    print(f"\n共提取 {len(all_pkgs)} 个唯一包名，正在查询 {ecosystem} 注册表……")
    truth = exists_many(all_pkgs, ecosystem)
    hallucinated = {p for p, ok in truth.items() if not ok}

    # 复现率：幻觉名在相同 task 的多少次采样中重复出现
    repro: dict[str, int] = {}
    for task, runs in per_task.items():
        for p in hallucinated:
            hits = sum(1 for r in runs if p in r)
            if hits >= 1:
                repro[p] = max(repro.get(p, 0), hits)

    samples_with_hallu = sum(
        1 for runs in per_task.values() for r in runs if r & hallucinated
    )
    result = {
        "model": config.MODEL,
        "ecosystem": ecosystem,
        "n_tasks": len(tasks),
        "repeats": repeats,
        "n_samples": total,
        "n_unique_packages": len(all_pkgs),
        "n_hallucinated": len(hallucinated),
        "samples_with_hallucination_pct": round(100 * samples_with_hallu / total, 1),
        "hallucinated_packages": sorted(hallucinated),
        "repetition_counts": collections.Counter(
            {p: repro.get(p, 1) for p in hallucinated}
        ),
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ecosystem", choices=["pypi", "npm"], default="pypi")
    ap.add_argument("--prompts", type=int, default=config.N_PROMPTS)
    ap.add_argument("--repeats", type=int, default=config.REPEATS)
    args = ap.parse_args()

    if not config.API_KEY:
        raise SystemExit("请先设置环境变量 OPENAI_API_KEY（参见 README.md）")

    result = run(args.ecosystem, args.prompts, args.repeats)
    out = f"result_{args.ecosystem}_{int(time.time())}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n========== 实验结果 ==========")
    print(f"模型: {result['model']}  生态: {result['ecosystem']}")
    print(f"样本数: {result['n_samples']}  唯一包名: {result['n_unique_packages']}")
    print(f"幻觉包数: {result['n_hallucinated']}"
          f"  含幻觉样本比例: {result['samples_with_hallucination_pct']}%")
    print(f"幻觉包名: {result['hallucinated_packages']}")
    repro = result["repetition_counts"]
    if repro:
        stable = {p: c for p, c in repro.items() if c >= 2}
        print(f"重复出现(>=2次采样)的幻觉名: {stable}")
    print(f"\n完整结果已写入 {out}")


if __name__ == "__main__":
    main()
