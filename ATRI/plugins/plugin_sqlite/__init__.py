#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   __init__.py
@Time    :   2020/10/25 15:01:29
@Author  :   Kyomotoi
@Contact :   kyomotoiowo@gmail.com
@Github  :   https://github.com/Kyomotoi
@License :   Copyright © 2018-2020 Kyomotoi, All Rights Reserved.
'''
__author__ = 'kyomotoi'

import os
import json
import sqlite3
from pathlib import Path
from nonebot.typing import Bot, Event
from aiohttp import client_exceptions
from nonebot.plugin import on_command
from nonebot.permission import SUPERUSER

from ATRI.utils.utils_error import errorRepo
from ATRI.utils.utils_request import aio_get_bytes

SetuData = on_command('setu', permission=SUPERUSER)


@SetuData.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    msg0 = "-==ATRI Setu Data System==-\n"
    msg0 += "Upload:\n"
    msg0 += " - setu [type] [pid]\n"
    msg0 += " * type: normal, nearR18 r18\n"
    msg0 += "Delete:\n"
    msg0 += " - setu-delete [pid]"
    await SetuData.finish(msg0)


UploadSetu = on_command('setu-upload', permission=SUPERUSER)


@UploadSetu.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    msg = str(event.message).strip().split(' ')

    if not msg[0] and not msg[1]:
        msg0 = "请检查格式奥~！\n"
        msg0 += "setu-upload [type] [pid]\n"
        msg0 += "type: normal, nearR18, r18"
        await UploadSetu.finish(msg0)

    if msg[0] not in ["normal", "nearR18", "nearr18", "r18", "R18"]:
        msg0 = "请检查类型~！\n"
        msg0 += "type: normal, nearR18, r18"
        await UploadSetu.finish(msg0)

    s_type = msg[0]
    pid = msg[1]

    URL = f'https://api.imjad.cn/pixiv/v1/?type=illust&id={pid}'
    info = {}

    try:
        info = json.loads(await aio_get_bytes(URL))
    except client_exceptions:
        await UploadSetu.finish(errorRepo("网络请求出错"))

    info = info["response"][0]
    title = info["title"]
    tags = info["tags"]
    account = info["user"]["account"]
    name = info["user"]["name"]
    u_id = info["user"]["id"]
    user_link = f'https://www.pixiv.net/users/{u_id}'
    IMG = info["iamge_urls"]["large"]
    IMG = IMG.replace("i.pximg.net", "i.pixiv.cat")

    data_setu = (f'{pid}', f'{title}', f'{tags}', f'{account}', f'{name}',
                 f'{u_id}', f'{user_link}', f'{IMG}')

    if s_type == "nearr18":
        s_type = "nearR18"
    elif s_type == "R18":
        s_type = "r18"
    else:
        pass

    os.makedirs('ATRI/data/data_Sqlite/setu', exist_ok=True)

    if os.path.exists(f'ATRI/data/data_Sqlite/setu/{s_type}.db'):
        print('数据文件存在！')
    else:
        await DeleteSetu.finish("数据库都不在添加🔨！？罢了我现创一个")
        con = sqlite3.connect(
            Path('.') / 'ATRI' / 'data' / 'data_Sqlite' / 'setu' /
            f'{s_type}.db')
        cur = con.cursor()
        cur.execute(
            f'CREATE TABLE {s_type}(pid PID, title TITLE, tags TAGS, account ACCOUNT, name NAME, u_id UID, user_link USERLINK, img IMG, UNIQUE(pid, title, tags, account, name, u_id, user_link, img))'
        )
        con.commit()
        cur.close()
        await bot.send(event, '完成')

    con = sqlite3.connect(
        Path('.') / 'ATRI' / 'data' / 'data_Sqlite' / 'setu' / f'{s_type}.db')
    cur = con.cursor()
    cur.execute(
        f'INSERT INTO {s_type}(pid, title, tags, account, name, u_id, user_link, img) VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
        data_setu)
    con.commit()
    cur.close()

    await UploadSetu.finish(f"数据上传完成~！\n涩图库[{s_type}]涩图 +1")


DeleteSetu = on_command('setu-delete', permission=SUPERUSER)


@DeleteSetu.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    msg = str(event.message).strip().split(' ')

    if not msg[0] and not msg[1]:
        msg0 = "请检查格式奥~！\n"
        msg0 += "setu-delete [type] [pid]\n"
        msg0 += "type: normal, nearR18, r18"
        await DeleteSetu.finish(msg0)

    if msg[0] not in ["normal", "nearR18", "nearr18", "r18", "R18"]:
        msg0 = "请检查类型~！\n"
        msg0 += "type: normal, nearR18, r18"
        await UploadSetu.finish(msg0)

    s_type = msg[0]
    pid = msg[1]

    if s_type == "nearr18":
        s_type = "nearR18"
    elif s_type == "R18":
        s_type = "r18"
    else:
        pass

    if os.path.exists(f'ATRI/data/data_Sqlite/setu/{s_type}.db'):
        print('数据文件存在！')
    else:
        await DeleteSetu.finish("数据库都不在删🔨！？")

    con = sqlite3.connect(
        Path('.') / 'ATRI' / 'data' / 'data_Sqlite' / 'setu' / f'{s_type}.db')
    cur = con.cursor()
    cur.execute(f'DELETE FROM {s_type} WHERE pid = {pid}')
    con.commit()
    con.close()

    await UploadSetu.finish(f"数据删除完成~！\n涩图库[{s_type}]涩图 -1")
