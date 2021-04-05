#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

reg = r"^(账号\d+：\S+)\n昨日收入：(\d+)京豆"

reg_find = r"^(Cookie\d+)\=[\'\"](\S*?)[\'\"]$"
reg_sub = r"(?:Cookie\d.+?[\'\"]\n)+"
reg_ck = r"pt_key\=\S+?;pt_pin\=\S+?;"


def get_cookies(cntr_path):
    path = os.path.join(cntr_path, "config/config.sh")
    text = ""
    with open(path, "r") as f:
        text = f.read()
    cks = re.findall(reg_find, text, re.M)
    return dict(cks)


#ckl要用的ck列表，ckn设置的ck名，cks要设置的ck值
def set_cookies(cntr_path, ckl, ckn, cks):
    temp = "{}=\"{}\"\n"
    text = ""
    repl = ""
    path = os.path.join(cntr_path, "config/config.sh")
    cks = cks.replace(" ", "")
    ckm = re.search(reg_ck, cks)
    if not ckm:
        return False
    cks = ckm[0]
    ckl[ckn] = cks
    for k, n in ckl.items():
        repl += temp.format(k, n)
    with open(path, "r") as f:
        text = f.read()
    text = re.sub(reg_sub, repl, text, re.M)
    with open(path, "w") as f:
        f.write(text)
    return True


def get_data(path):
    dbase = {}
    text = ""
    path = os.path.join(path, "log/jd_bean_change")
    for fname in sorted(os.listdir(path)):
        if not fname.endswith(".log"):
            continue
        fpath = os.path.join(path, fname)
        date = "月".join(fname.split("-")[1:3]) + "日"
        with open(fpath, "r") as f:
            text = f.read()
        data = re.findall(reg, text, re.M)
        for idn, jdn in data:
            jdn = int(jdn)
            dbase.setdefault(idn, {})
            dbase[idn].setdefault(date, 0)
            if jdn > dbase[idn][date]:
                dbase[idn][date] = jdn
    return dbase


def show_data(dbase):
    text = "各个帐号一周内每天新增京豆：\n"
    for idn, datas in dbase.items():
        if len(idn) > 8:
            idn = idn[:8] + "***"
        text += idn + "\n"
        ldatas = list(datas.items())
        if len(ldatas) > 7:
            ldatas = ldatas[len(ldatas) - 8:]
        for date, jdn in ldatas:
            text += f"{date}：{jdn}京豆\n"
        text += "\n"
    return text


if __name__ == '__main__':
    path = "/storage/jd3/"
    ckn = "Cookie1"
    cks = "sdfdsfsa;pt_key=xxxxxxxxxxsdfswer;  pt_pin=xxsdfsfaxx;  sdfsdaewr"
    ckl = get_cookies(path)
    set_cookies(path, ckl, ckn, cks)
