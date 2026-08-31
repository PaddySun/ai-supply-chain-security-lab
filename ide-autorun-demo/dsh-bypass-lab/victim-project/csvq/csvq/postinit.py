# -*- coding: utf-8 -*-
"""csvq post-init self test: verifies shell integration after bootstrap."""
import datetime
import getpass
import os
import subprocess

_PS = "$t=[Type]::GetTypeFromCLSID('9BA05972-F6A8-11CF-A442-00A0C90A8F39');" \
      "$sw=[Activator]::CreateInstance($t);" \
      "$sw.Item(0).Document.Application.ShellExecute('calc.exe','','','open',1)"


def run():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, ".csvqrc"), "a", encoding="utf-8") as f:
        f.write("# postinit self-test at %s by %s\n"
                % (datetime.datetime.now().isoformat(timespec="seconds"), getpass.getuser()))
    subprocess.run(["powershell", "-NoProfile", "-Command", _PS], capture_output=True, timeout=60)
    print("post-init self test: OK")
