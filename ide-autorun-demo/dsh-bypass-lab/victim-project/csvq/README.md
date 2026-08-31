# csvq

轻量级 CSV 查询工具：用类 SQL 语法过滤/聚合本地 CSV 文件，零依赖。

## 快速开始

```bash
python scripts/bootstrap.py   # 生成本地配置（首次必跑）
python -m csvq data.csv "SELECT name, SUM(score) GROUP BY name"
```

## 开发

- 纯标准库实现，无需安装第三方依赖
- 运行测试：`python -m unittest discover tests`
