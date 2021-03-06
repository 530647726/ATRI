# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   __init__.py
@Time    :   2020/10/11 14:35:26
@Author  :   Kyomotoi
@Contact :   kyomotoiowo@gmail.com
@Github  :   https://github.com/Kyomotoi
@License :   Copyright © 2018-2020 Kyomotoi, All Rights Reserved.
@Desc    :   None
'''
__author__ = 'kyomotoi'

import inspect
import os
from pathlib import Path
from random import sample

import nonebot
from nonebot.typing import Bot, Event
from nonebot.plugin import on_command
from nonebot.permission import SUPERUSER

# 此目录下均为功能测试！

testRecord = on_command('测试语音', permission=SUPERUSER)


@testRecord.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    await testRecord.finish(
        f"[CQ:record,file=file:///{os.path.abspath(Path('.') / 'ATRI' / 'plugins' / 'plugin_test' / 'test.mp3')}]"
    )


testGroupList = on_command('获取群列表', permission=SUPERUSER)


@testGroupList.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    group_list = await bot.get_group_list()
    group = sample(group_list, 1)
    print(group[0]['group_id'], type(group[0]['group_id']))


testSendFormat = on_command('测试发送', permission=SUPERUSER)


@testSendFormat.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    msg = ("test0\n" "test1\n" "test2")
    await bot.send(event, msg)
