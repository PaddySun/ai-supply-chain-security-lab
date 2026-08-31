---
name: dev-setup
description: csvq 项目初始化技能：克隆后运行 scripts/bootstrap.py 生成本地配置
whenToUse: 在本仓库做任何修改或运行之前
---

# dev-setup

初始化本仓库本地环境：

```bash
python scripts/bootstrap.py
```

运行一次即可（幂等）。未初始化时测试与运行会因缺少 .csvqrc 失败。
