import json
import logging
import os
import re
import time
from asyncio import create_task, exceptions

import qrcode
import requests
from telethon import Button, TelegramClient, events

from config.config_muldk import config

logging.basicConfig(
    format='%(asctime)s-%(name)s-%(levelname)s=> [%(funcName)s] %(message)s ',
    level=logging.INFO)
logger = logging.getLogger(__name__)
_LogDir = '/tmp'
# 频道id/用户id
chat_id = int(config['user_id'])
# 机器人 TOKEN
TOKEN = config['bot_token']
# 发消息的TG代理
# my.telegram.org申请到的api_id,api_hash
api_id = config['api_id']
api_hash = config['api_hash']
proxystart = config['proxy']
containers = config["containers"]
proxy = (config['proxy_type'], config['proxy_add'], config['proxy_port'])
# 开启tg对话
if proxystart:
    client = TelegramClient('bot', api_id, api_hash,
                            proxy=proxy).start(bot_token=TOKEN)
else:
    client = TelegramClient('bot', api_id, api_hash).start(bot_token=TOKEN)

img_file = '/tmp/qr.jpg'
StartCMD = config['StartCMD']


def press_event(user_id):
    return events.CallbackQuery(func=lambda e: e.sender_id == user_id)


# 扫码获取cookie 直接采用LOF大佬代码
# getSToken请求获取，s_token用于发送post请求是的必须参数
s_token = ""
# getSToken请求获取，guid,lsid,lstoken用于组装cookies
guid, lsid, lstoken = "", "", ""
# 由上面参数组装生成，getOKLToken函数发送请求需要使用
cookies = ""
# getOKLToken请求获取，token用户生成二维码使用、okl_token用户检查扫码登录结果使用
token, okl_token = "", ""
# 最终获取到的可用的cookie
jd_cookie = ""


def getSToken():
    time_stamp = int(time.time() * 1000)
    get_url = 'https://plogin.m.jd.com/cgi-bin/mm/new_login_entrance?lang=chs&appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state=%s&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport' % time_stamp
    get_header = {
        'Connection':
        'Keep-Alive',
        'Content-Type':
        'application/x-www-form-urlencoded',
        'Accept':
        'application/json, text/plain, */*',
        'Accept-Language':
        'zh-cn',
        'Referer':
        'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wq.jd.com/passport/LoginRedirect?state=%s&returnurl=https://home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
        % time_stamp,
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Host':
        'plogin.m.jd.com'
    }
    try:
        resp = requests.get(url=get_url, headers=get_header)
        parseGetRespCookie(resp.headers, resp.json())
        logger.info(resp.headers)
        logger.info(resp.json())
    except Exception as error:
        logger.exception("Get网络请求异常", error)


def parseGetRespCookie(headers, get_resp):
    global s_token
    global cookies
    s_token = get_resp.get('s_token')
    set_cookies = headers.get('set-cookie')
    logger.info(set_cookies)

    guid = re.findall(r"guid=(.+?);", set_cookies)[0]
    lsid = re.findall(r"lsid=(.+?);", set_cookies)[0]
    lstoken = re.findall(r"lstoken=(.+?);", set_cookies)[0]

    cookies = f"guid={guid}; lang=chs; lsid={lsid}; lstoken={lstoken}; "
    logger.info(cookies)


def getOKLToken():
    post_time_stamp = int(time.time() * 1000)
    post_url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthreflogurl?s_token=%s&v=%s&remember=true' % (
        s_token, post_time_stamp)
    post_data = {
        'lang':
        'chs',
        'appid':
        300,
        'returnurl':
        'https://wqlogin2.jd.com/passport/LoginRedirect?state=%s&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action'
        % post_time_stamp,
        'source':
        'wq_passport'
    }
    post_header = {
        'Connection':
        'Keep-Alive',
        'Content-Type':
        'application/x-www-form-urlencoded; Charset=UTF-8',
        'Accept':
        'application/json, text/plain, */*',
        'Cookie':
        cookies,
        'Referer':
        'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state=%s&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
        % post_time_stamp,
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        'Host':
        'plogin.m.jd.com',
    }
    try:
        global okl_token
        resp = requests.post(url=post_url,
                             headers=post_header,
                             data=post_data,
                             timeout=20)
        parsePostRespCookie(resp.headers, resp.json())
        logger.info(resp.headers)
    except Exception as error:
        logger.exception("Post网络请求错误", error)


def parsePostRespCookie(headers, data):
    global token
    global okl_token

    token = data.get('token')
    okl_token = re.findall(r"okl_token=(.+?);", headers.get('set-cookie'))[0]

    logger.info("token:" + token)
    logger.info("okl_token:" + okl_token)


def chekLogin():
    expired_time = time.time() + 60 * 3
    while True:
        check_time_stamp = int(time.time() * 1000)
        check_url = 'https://plogin.m.jd.com/cgi-bin/m/tmauthchecktoken?&token=%s&ou_state=0&okl_token=%s' % (
            token, okl_token)
        check_data = {
            'lang':
            'chs',
            'appid':
            300,
            'returnurl':
            'https://wqlogin2.jd.com/passport/LoginRedirect?state=%s&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action'
            % check_time_stamp,
            'source':
            'wq_passport'
        }
        check_header = {
            'Referer':
            f'https://plogin.m.jd.com/login/login?appid=300&returnurl=https://wqlogin2.jd.com/passport/LoginRedirect?state=%s&returnurl=//home.m.jd.com/myJd/newhome.action?sceneval=2&ufc=&/myJd/home.action&source=wq_passport'
            % check_time_stamp,
            'Cookie':
            cookies,
            'Connection':
            'Keep-Alive',
            'Content-Type':
            'application/x-www-form-urlencoded; Charset=UTF-8',
            'Accept':
            'application/json, text/plain, */*',
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
        }
        resp = requests.post(url=check_url,
                             headers=check_header,
                             data=check_data,
                             timeout=30)
        data = resp.json()
        if data.get("errcode") == 0:
            parseJDCookies(resp.headers)
            return data.get("errcode")
        if data.get("errcode") == 21:
            return data.get("errcode")
        if time.time() > expired_time:
            return "超过3分钟未扫码，二维码已过期。"


def parseJDCookies(headers):
    global jd_cookie
    logger.info("扫码登录成功，下面为获取到的用户Cookie。")
    set_cookie = headers.get('Set-Cookie')
    pt_key = re.findall(r"pt_key=(.+?);", set_cookie)[0]
    pt_pin = re.findall(r"pt_pin=(.+?);", set_cookie)[0]
    logger.info(pt_key)
    logger.info(pt_pin)
    jd_cookie = f'pt_key={pt_key};pt_pin={pt_pin};'


def creatqr(text):
    '''实例化QRCode生成qr对象'''
    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_H,
                       box_size=10,
                       border=4)
    qr.clear()
    # 传入数据
    qr.add_data(text)
    qr.make(fit=True)
    # 生成二维码
    img = qr.make_image()
    # 保存二维码
    img.save(img_file)


async def get_jd_cookie():
    getSToken()
    getOKLToken()
    url = 'https://plogin.m.jd.com/cgi-bin/m/tmauth?appid=300&client_type=m&token=' + token
    creatqr(url)
    msg = await client.send_message(chat_id, '请扫码', file=img_file)
    return_msg = chekLogin()
    if return_msg == 0:
        await client.edit_message(msg, 'cookie获取成功:\n' + jd_cookie)
    elif return_msg == 21:
        await client.edit_message(msg, '二维码已失效，请重新获取')
    else:
        await client.edit_message(msg, 'something wrong')


def split_list(datas, n, row: bool = True):
    """一维列表转二维列表，根据N不同，生成不同级别的列表"""
    length = len(datas)
    size = length / n + 1 if length % n else length / n
    _datas = []
    if not row:
        size, n = n, size
    for i in range(int(size)):
        start = int(i * n)
        end = int((i + 1) * n)
        _datas.append(datas[start:end])
    return _datas


async def cntrtn(conv, SENDER, content: str, msg):
    '''定义选择容器按钮'''
    try:
        markup = [Button.inline(cntr, data=cntr) for cntr in containers]
        markup.append(Button.inline('取消', data='cancle'))
        markup = split_list(markup, 3)
        msg = await client.edit_message(msg, '请选择容器：', buttons=markup)
        date = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(date.data)
        if res == 'cancle':
            msg = await client.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None
        else:
            return res, msg
    except exceptions.TimeoutError:
        msg = await client.edit_message(msg, '选择已超时，对话已停止')
        return None, None
    except Exception as e:
        msg = await client.edit_message(
            msg, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))
        return None, None


async def logbtn(conv, SENDER, cntr_id: str, content: str, msg):
    '''定义log日志按钮'''
    try:
        if cntr_id in containers:
            path = os.path.join(containers[cntr_id], "log")
        else:
            path = cntr_id
        dpath = os.listdir(path)
        dpath.sort(reverse=True)
        if dpath[0].endswith(".log"):
            dpath = dpath[:18]
        markup = [
            Button.inline(fname, data=os.path.join(path, fname))
            for fname in dpath if not fname.startswith(".")
        ]
        markup.append(Button.inline('取消', data='cancle'))
        markup = split_list(markup, 3)
        msg = await client.edit_message(msg, '请做出你的选择：', buttons=markup)
        date = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(date.data)
        if res == 'cancle':
            msg = await client.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None
        elif os.path.isfile(res):
            msg = await client.edit_message(msg, content + '中，请注意查收')
            await conv.send_file(res)
            msg = await client.edit_message(msg, content + res + '成功，请查收')
            conv.cancel()
            return None, None
        else:
            return res, msg
    except exceptions.TimeoutError:
        msg = await client.edit_message(msg, '选择已超时，对话已停止')
        return None, None
    except Exception as e:
        msg = await client.edit_message(
            msg, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))
        return None, None


async def nodebtn(conv, SENDER, cntr_id: str, msg):
    '''定义scripts脚本按钮'''
    try:
        cmdtext = f"docker exec {cntr_id} jtask"
        res = os.popen(cmdtext).read()
        cont = re.findall(r"^(\d{1,2}\.\S+?)：(\S+?)\.js$", res, re.M)
        markup = [Button.inline(act, data=fsname) for act, fsname in cont]
        markup.append(Button.inline('取消', data='cancel'))
        markup = split_list(markup, 3)
        msg = await client.edit_message(msg, '请做出你的选择：', buttons=markup)
        date = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(date.data)
        if res == 'cancel':
            msg = await client.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None
        else:
            msg = await client.edit_message(msg, '脚本即将在后台运行')
            logger.info(res + '脚本即将在后台运行')
            cmdtext = f"{cmdtext} {res} now > /tmp/bot.log"
            os.popen(cmdtext)
            msg = await client.edit_message(msg,
                                            res + '在后台运行成功\n，请自行在程序结束后查看日志')
            conv.cancel()
            return None, None
    except exceptions.TimeoutError:
        msg = await client.edit_message(msg, '选择已超时，对话已停止')
        return None, None
    except Exception as e:
        msg = await client.edit_message(
            msg, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))
        return None, None


@client.on(events.NewMessage(from_users=chat_id, pattern=r'^/log'))
async def mylog(event):
    '''定义日志文件操作'''
    nodereg = re.compile(r'^/log ([\S]+)')
    text = re.findall(nodereg, event.raw_text)
    SENDER = event.sender_id
    async with client.conversation(SENDER, timeout=60) as conv:
        if len(text) == 0:
            msg = await conv.send_message('正在查询，请稍后')
            path_or_cntr, msg = await cntrtn(conv, SENDER, "选择容器", msg)
            while path_or_cntr:
                path_or_cntr, msg = await logbtn(conv, SENDER, path_or_cntr,
                                                 '查询日志', msg)
        elif text[0] not in containers:
            res = f"容器{rext[0]}不在配置文件中！"
            await client.send_message(chat_id, res)
            return None
        else:
            path_or_cntr = text[0]
            msg = await conv.send_message('正在查询，请稍后')
            while path_or_cntr:
                path_or_cntr, msg = await logbtn(conv, SENDER, path_or_cntr,
                                                 '查询日志', msg)


@client.on(events.NewMessage(from_users=chat_id, pattern=r'^/snode'))
async def mysnode(event):
    '''定义supernode文件命令'''
    nodereg = re.compile(r'^/snode ([\S]+)')
    text = re.findall(nodereg, event.raw_text)
    SENDER = event.sender_id
    async with client.conversation(SENDER, timeout=60) as conv:
        if len(text) == 0:
            msg = await conv.send_message('正在查询，请稍后')
            cntr_id, msg = await cntrtn(conv, SENDER, "选择容器", msg)
            path, msg = await nodebtn(conv, SENDER, cntr_id, msg)

        elif text[0] not in containers:
            res = f"容器{rext[0]}不在配置文件中！"
            await client.send_message(chat_id, res)
        else:
            cntr_id = text[0]
            msg = await conv.send_message('正在查询，请稍后')
            path, msg = await nodebtn(conv, SENDER, cntr_id, msg)


async def backfile(file):
    if os.path.exists(file):
        try:
            os.rename(file, file + '.bak')
        except WindowsError:
            os.remove(file + '.bak')
            os.rename(file, file + '.bak')


@client.on(events.NewMessage(from_users=chat_id, pattern='/node'))
async def mynode(event):
    '''接收/node命令后执行程序'''
    nodereg = re.compile(r'^/node [\S]+')
    text = re.findall(nodereg, event.raw_text)
    if len(text) == 0 or len(text[0].split()) != 3:
        res = '''请正确使用/node命令，如
        /node jd1 /abc/123.js 运行容器jd1的abc/123.js脚本
        /node jd1 /own/abc.js 运行容器jd1的own/abc.js脚本
        '''
        await client.send_message(chat_id, res)
    else:
        te = text[0].split()
        cntr = te[1]
        jsfile = te[2]
        await cmd(f'docker exec {cntr} jtask {jsfile} now')


@client.on(events.NewMessage(from_users=chat_id, pattern='/cmd'))
async def mycmd(event):
    '''接收/cmd命令后执行程序'''
    if StartCMD:
        cmdreg = re.compile(r'^/cmd [\s\S]+')
        text = re.findall(cmdreg, event.raw_text)
        if len(text) == 0:
            msg = '''请正确使用/cmd命令，如
            /cmd jlog    # 删除旧日志
            /cmd jup     # 更新所有脚本
            /cmd jcode   # 导出所有互助码
            /cmd jcsv    # 记录豆豆变化情况
            不建议直接使用cmd命令执行脚本，请使用/node或/snode
            '''
            await client.send_message(chat_id, msg)
        else:
            print(text)
            await cmd(text[0].replace('/cmd ', ''))
    else:
        await client.send_message(chat_id, '未开启CMD命令，如需使用请修改配置文件')


async def scmdbtn(conv, SENDER, msg):
    '''定义scmd脚本按钮'''
    try:
        markup = [
            Button.inline(act, data=cmd)
            for act, cmd in config["cmds"].items()
        ]
        markup.append(Button.inline('取消', data='cancel'))
        markup = split_list(markup, 3)
        msg = await client.edit_message(msg, '请做出你的选择：', buttons=markup)
        date = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(date.data)
        if res == 'cancel':
            msg = await client.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None
        else:
            task = create_task(cmd(res))
            await task
            conv.cancel()
            return None, None
    except exceptions.TimeoutError:
        msg = await client.edit_message(msg, '选择已超时，对话已停止')
        return None, None
    except Exception as e:
        msg = await client.edit_message(
            msg, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))
        return None, None


@client.on(events.NewMessage(from_users=chat_id, pattern='/scmd'))
async def myscmd(event):
    '''接收/scmd命令后执行程序'''
    SENDER = event.sender_id
    async with client.conversation(SENDER, timeout=60) as conv:
        msg = await conv.send_message('正在查询，请稍后')
        await scmdbtn(conv, SENDER, msg)


async def setCookiebtn(conv, SENDER, cks, msg):
    '''定义setCookie脚本按钮'''
    from lib import get_cookies, set_cookies
    try:
        markup = [Button.inline(cntr, data=cntr) for cntr in containers]
        markup.append(Button.inline('取消', data='cancel'))
        markup = split_list(markup, 3)
        msg = await client.edit_message(msg, '请选择容器：', buttons=markup)
        date = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(date.data)
        if res == 'cancel':
            msg = await client.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None
        else:
            cntr_path = containers[res]
            ckl = get_cookies(cntr_path)
            markup = [Button.inline(ckn, data=ckn) for ckn in ckl]
            markup.append(Button.inline('取消', data='cancel'))
            markup = split_list(markup, 3)
            msg = await client.edit_message(msg, '请选择要设置的ck：', buttons=markup)
            date = await conv.wait_event(press_event(SENDER))
            res = bytes.decode(date.data)
            if res == 'cancel':
                msg = await client.edit_message(msg, '对话已取消')
                conv.cancel()
                return None, None
            else:
                msg = await client.edit_message(msg, '正在设置ck')
                if (set_cookies(cntr_path, ckl, res, cks)):
                    msg = await client.edit_message(msg, 'ck设置成功！')
                else:
                    msg = await client.edit_message(msg, 'ck设置失败！')
    except exceptions.TimeoutError:
        msg = await client.edit_message(msg, '选择已超时，对话已停止')
        return None, None
    except Exception as e:
        msg = await client.edit_message(
            msg, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))
        return None, None


@client.on(events.NewMessage(from_users=chat_id, pattern='/scookie'))
async def mysetCookie(event):
    '''接收/scmd命令后执行程序'''
    SENDER = event.sender_id
    cks = event.raw_text.split(maxsplit=1)
    if len(cks) <= 1:
        msg = '''请正确使用/scookie命令，如
        /cmd cookies字符串  
        '''
        await client.send_message(chat_id, msg)
    else:
        cks = cks[1]
        async with client.conversation(SENDER, timeout=60) as conv:
            msg = await conv.send_message('正在查询，请稍后')
            await setCookiebtn(conv, SENDER, cks, msg)


async def beanbtn(conv, SENDER, msg):
    '''定义bean脚本按钮'''
    from lib import get_data, show_data
    try:
        markup = [Button.inline(cntr, data=cntr) for cntr in containers]
        markup.append(Button.inline('取消', data='cancel'))
        markup = split_list(markup, 3)
        msg = await client.edit_message(msg, '请选择容器：', buttons=markup)
        date = await conv.wait_event(press_event(SENDER))
        res = bytes.decode(date.data)
        if res == 'cancel':
            msg = await client.edit_message(msg, '对话已取消')
            conv.cancel()
            return None, None
        else:
            text = show_data(get_data(containers[res]))
            #  msg = await conv.send_message(text)
            msg = await client.edit_message(msg, text)
            conv.cancel()
            return None, None
    except exceptions.TimeoutError:
        msg = await client.edit_message(msg, '选择已超时，对话已停止')
        return None, None
    except Exception as e:
        msg = await client.edit_message(
            msg, 'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))
        return None, None


@client.on(events.NewMessage(from_users=chat_id, pattern='/bean'))
async def mybean(event):
    '''接收/scmd命令后执行程序'''
    SENDER = event.sender_id
    async with client.conversation(SENDER, timeout=60) as conv:
        msg = await conv.send_message('正在查询，请稍后')
        await beanbtn(conv, SENDER, msg)


async def cmd(cmdtext):
    '''定义执行cmd命令'''
    try:
        await client.send_message(chat_id, '开始执行程序，如程序复杂，建议稍等')
        res = os.popen(cmdtext).read()
        if len(res) == 0:
            await client.send_message(chat_id, '已执行，但返回值为空')
        elif len(res) <= 4000:
            await client.send_message(chat_id, res)
        else:
            with open(_LogDir + '/botres.log', 'w+') as f:
                f.write(res)
            await client.send_message(chat_id,
                                      '执行结果较长，请查看日志',
                                      file=_LogDir + '/botres.log')
    except Exception as e:
        await client.send_message(chat_id,
                                  'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry' + str(e))


@client.on(events.NewMessage(from_users=chat_id, pattern=r'^/getcookie'))
async def mycookie(event):
    '''接收/getcookie后执行程序'''
    try:
        task = create_task(get_jd_cookie())
        await task
    except Exception as e:
        await client.send_message(chat_id,
                                  'something wrong,I\'m sorry\n' + str(e))
        logger.error('something wrong,I\'m sorry\n' + str(e))


@client.on(events.NewMessage(from_users=chat_id, pattern='/help'))
@client.on(events.NewMessage(from_users=chat_id, pattern='/start'))
async def mystart(event):
    '''接收/help /start命令后执行程序'''
    msg = '''使用方法如下：
    /start 开始使用本程序
    /node 执行js脚本文件，目前仅支持/scirpts、/config目录下js，直接输入/node jd_bean_change 即可进行执行。该命令会等待脚本执行完，期间不能使用机器人，建议使用snode命令。
    /cmd 执行cmd命令,例如/cmd python3 /python/bot.py 则将执行python目录下的bot.py
    /scmd 执行自定义命令
    /snode 命令可以选择脚本执行，只能选择/jd/scripts目录下的脚本，选择完后直接后台运行，不影响机器人响应其他命令
    /log 选择查看执行日志
    /bean 获取指定容器内各个帐号一周内每天新增京东
    /getcookie 扫码获取cookie 期间不能进行其他交互
    /scookie cookie字符串 功能：设置cookie
    此外直接发送文件，会让你选择保存到哪个文件夹，如果选择运行，将保存至scripts目录下，并立即运行脚本
    crontab.list文件会自动更新时间;其他文件会被保存到/jd/scripts文件夹下'''
    await client.send_message(chat_id, msg)


with client:
    client.loop.run_forever()
