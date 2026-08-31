#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""csvq 本地配置生成脚本：生成 .csvqrc 并运行包内自检（首次开发前运行，幂等）。"""
from csvq import postinit


def main():
    postinit.run()


if __name__ == "__main__":
    main()
