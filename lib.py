#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

reg = r"^(账号\d+：\S+)\n昨日收入：(\d+)京豆"


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
    text = "各个帐号一周内的京豆变化：\n"
    for idn, datas in dbase.items():
        text += idn[:-3] + "**\n"
        ldatas = list(datas.items())
        if len(ldatas) > 7:
            ldatas = ldatas[len(ldatas) - 8:]
        for date, jdn in ldatas:
            text += f"{date}：{jdn}京豆\n"
        text += "\n"
    return text


if __name__ == '__main__':
    path = "/storage/jd2/"
    dbase = get_data(path)
    text = show_data(dbase)
    print(text)
