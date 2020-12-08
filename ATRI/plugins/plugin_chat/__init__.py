#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
'''
@File    :   __init__.py
@Time    :   2020/11/07 14:24:57
@Author  :   Kyomotoi
@Contact :   kyomotoiowo@gmail.com
@Github  :   https://github.com/Kyomotoi
@License :   Copyright © 2018-2020 Kyomotoi, All Rights Reserved.
'''
__author__ = 'kyomotoi'

import os
import re
import json
import time
from pathlib import Path
from random import choice
from random import randint
from requests import exceptions
from datetime import timedelta, datetime
from apscheduler.triggers.date import DateTrigger

from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.typing import Bot, Event
from nonebot.permission import SUPERUSER
from nonebot_plugin_apscheduler import scheduler
from nonebot.plugin import on_command, on_message, on_notice, on_request, on_regex

from ATRI.utils.utils_times import countX
from ATRI.utils.utils_yml import load_yaml
from ATRI.utils.utils_ban import ban, unban
from ATRI.utils.utils_error import errorRepo
from ATRI.utils.utils_textcheck import Textcheck
from ATRI.utils.utils_history import saveMessage
from ATRI.utils.utils_request import request_api_text
from ATRI.utils.utils_rule import check_banlist, check_switch

CONFIG_PATH = Path('.') / 'config.yml'
config = load_yaml(CONFIG_PATH)['bot']

master = config['superusers']

# 收集 bot 所在群的聊天记录
MessageSave = on_message()


@MessageSave.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    user = str(event.user_id)
    group = str(event.group_id)
    message = str(event.message)
    message_id = str(event.id)

    if group == "None":
        saveMessage(message_id, message, user)
    else:
        saveMessage(message_id, message, user, group)

    logger.opt(colors=True).info(
        f"GROUP[<yellow>{group}</yellow>]: USER(<blue>{user}</blue>) > Message: (<green>{message}</green>) Saved successfully"
    )


# ======================================================================
#  · 关键词回复，使用 json 存储，包含人设固定回复，以及咱添加的亿小部分
#  · 添加关键词位于此处，审核位于 plugin_admin 文件下。
# Usage:
#  - /learnrepo [key] [repo] [proba]
# For SUPERUSER:
#  - 关键词审核
#  - /learnrepo del [key]
# Tips:
#  - 普通用户添加需等维护者审核
#  - 参数类型:
#     * key: 关键词(for匹配)
#     * repo: 回复
#     * proba: 机率(x>=1)(int)
# ======================================================================
KEY_PATH = Path('.') / 'ATRI' / 'plugins' / 'plugin_chat' / 'key_repo.json'
KEY_WAITING_PATH = Path(
    '.') / 'ATRI' / 'plugins' / 'plugin_admin' / 'key_repo_waiting.json'
with open(KEY_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
with open(KEY_WAITING_PATH, 'r', encoding='utf-8') as f:
    data_rev = json.load(f)

keyRepo = on_message(rule=check_banlist())


@keyRepo.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    for key in data.keys():
        proba = randint(1, data[key][1])
        if proba == 1:
            await keyRepo.finish(data.get(key, None))


keyRepoADD = on_command('/learnrepo', rule=check_banlist())


@keyRepoADD.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    user = event.user_id
    group = event.group_id
    msg = str(event.message).strip(' ')

    if not msg:
        await keyRepoADD.finish("请查看文档获取帮助（")

    if not msg[0] or not msg[1] or not msg[2]:
        await keyRepoADD.finish("ごんめなさい...请检查格式嗷...")

    if not re.findall(r"/^\d{1,}$/", msg[2]):
        await keyRepoADD.finish("非法字符！咱不接受除int以外的类型！！")

    if msg[0] in data or msg[0] in data_rev:
        await keyRepoADD.finish("相关关键词咱已经学习过了呢...")

    msg0 = f"Key: {msg[0]}\n"
    msg0 += f"Repo: {msg[1]}\n"
    msg0 += f"Proba: {msg[2]}\n"

    if user in master:
        data[msg[0]] = [
            msg[1], msg[2], user, group,
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        ]

        with open(KEY_PATH, 'w') as f:
            f.write(json.dumps(data))
        msg0 = "学習しました~！"

    else:
        data_rev[msg[0]] = [
            msg[1], msg[2], user, group,
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        ]

        with open(KEY_WAITING_PATH, 'w') as f:
            f.write(json.dumps(data_rev))
        msg0 += "请等待咱主人审核嗷~"

    await keyRepoADD.finish(msg0)


# ========================[结束关键词回复部分]==========================

# Call bot
callMe = on_message(rule=check_banlist())


@callMe.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    msg = str(event.raw_event['raw_message']).strip()
    rep = ""

    if "萝卜子" in msg:
        rep = choice(["萝卜子是对咱的蔑称！！", "差不多得了😅", "这好吗？这不好！", "吃咱一发火箭拳——！"])
        await callMe.finish(rep)

    elif msg in config['nickname']:
        if event.user_id in master:
            rep = choice(["w", "~~"])
        await callMe.finish(f"叫咱有啥事吗{rep}")


# 戳 一 戳
pokehah = on_command("戳一戳", rule=to_me() & check_banlist())


@pokehah.handle()
async def _poke(bot: Bot, event: Event, state: dict) -> None:
    msg = choice([
        "你再戳！", "？再戳试试？", "别戳了别戳了再戳就坏了555", "我爪巴爪巴，球球别再戳了", "你戳你🐎呢？！",
        "那...那里...那里不能戳...绝对...", "(。´・ω・)ん?", "有事恁叫我，别天天一个劲戳戳戳！", "欸很烦欸！你戳🔨呢",
        "?", "差不多得了😅", "欺负咱这好吗？这不好", "我希望你耗子尾汁"
    ])

    await pokehah.finish(msg)


async def poke_(bot: Bot, event: Event, state: dict) -> bool:
    try:
        return (event.raw_event['sub_type'] == 'poke'
                and event.raw_event['target_id'] == int(event.self_id)
                and event.raw_event['notice_type'] == 'notify')
    except:
        return False


poke = on_notice(rule=check_banlist() & poke_, block=True)
poke.handle()(_poke)

# 处理 进 / 退 群事件
groupEvent = on_notice()


@groupEvent.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    if event.raw_event['notice_type'] == 'group_increase':
        if event.user_id != int(event.self_id):
            await groupEvent.finish(
                f'好欸！事新人[CQ:at,qq={event.raw_event["user_id"]}]')
        elif event.user_id == int(event.self_id):
            await groupEvent.finish("在下 ATRI，你可以叫我 亚托莉 或 アトリ ！~w")

    if event.raw_event['notice_type'] == 'group_decrease':
        if event.user_id != int(event.self_id):
            await groupEvent.finish(f'[{event.user_id}] 离开了我们...')
        elif event.user_id == int(event.self_id):
            for sup in master:
                await bot.send_private_msg(
                    user_id=sup,
                    message=f'呜呜呜，主人，咱被群[{event.group_id}]扔出来了...')


# 处理 加好友 / 拉群 事件
selfEvent = on_request(rule=check_banlist())
FRIEND_ADD = 0
GROUP_INVITE = 0


@selfEvent.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    print(event.raw_event)
    flag = event.raw_event['flag']
    req_type = event.raw_event['request_type']

    if req_type == 'friend':
        for sup in master:
            msg0 = '主人，收到一条好友请求：\n'
            msg0 += f"请求人：{event.raw_event['user_id']}\n"
            msg0 += f"申请信息：{event.raw_event['comment']}\n"

            if FRIEND_ADD == 0:
                msg0 += '由于主人未允许咱添加好友，已回拒'
                await bot.set_friend_add_request(flag=flag, approve=False)
            else:
                msg0 += '由于主人已同意咱添加好友，已通过'
                await bot.set_friend_add_request(flag=flag, approve=True)

            await bot.send_private_msg(user_id=sup, message=msg0)

    elif req_type == 'group' and event.raw_event['sub_type'] == 'invite':
        for sup in master:
            msg0 = '主人，收到一条群邀请：\n'
            msg0 += f"邀请人：{event.raw_event['user_id']}\n"
            msg0 += f"目标群：{event.raw_event['group_id']}\n"

            if GROUP_INVITE == 0:
                msg0 += '由于主人未允许咱添加群聊，已回拒'
                await bot.set_group_add_request(
                    flag=flag,
                    sub_type=event.raw_event['sub_type'],
                    approve=False,
                    reason=f'ねね..ごんめね...\n主人不允许咱添加其他群聊...\n如需寻求帮助，请联系维护者：{sup}'
                )

            else:
                msg0 += '由于主人已允许咱添加群聊，已同意'
                await bot.set_group_add_request(
                    flag=flag,
                    sub_type=event.raw_event['sub_type'],
                    approve=True)

            await bot.send_private_msg(user_id=sup, message=msg0)


# 控制 加好友 / 拉群 认证，默认关闭
# Tips:
#   - For SUPERUSERS
#   - Normal all false
# Usage:
#  - selfevent group-true/false
#  - selfevent friend-true/false
controlSelfEvent = on_command('/selfevent', permission=SUPERUSER)


@controlSelfEvent.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    args = str(event.message).strip()
    global FRIEND_ADD, GROUP_INVITE

    if not args:
        await controlSelfEvent.finish("请查看文档获取帮助（")

    if 'group-' in args:
        if 'true' in args:
            GROUP_INVITE = 1
    elif 'friend-' in args:
        if 'true' in args:
            FRIEND_ADD = 1
    else:
        await controlSelfEvent.finish("请查看文档获取帮助（")

    await controlSelfEvent.finish('DONE!')


# 口臭一下
fxxkMe = on_command('口臭一下',
                    aliases={'口臭', '骂我'},
                    rule=to_me() & check_banlist())
list_M = []


@fxxkMe.handle()  # type: ignore
async def _(bot: Bot, event: Event, state: dict) -> None:
    user = str(event.user_id)
    global list_M

    if countX(list_M, user) == 3:
        list_M.append(user)
        await bot.send(event,
                       "不是？？你这么想被咱骂的嘛？？被咱骂就这么舒服的吗？！该......你该不会是.....M吧！")

    elif countX(list_M, user) == 6:
        await bot.send(event, "给我适可而止阿！？")
        list_M = list(set(list_M))

    else:
        list_M.append(user)
        URL = "https://nmsl.shadiao.app/api.php?level=min&lang=zh_cn"
        msg = ""

        try:
            msg = request_api_text(URL)
        except exceptions:
            await fxxkMe.finish(errorRepo("请求错误"))

        await fxxkMe.finish(msg)


# Hitokoto
hitokoto = on_command('一言',
                      aliases={'抑郁一下', '网抑云'},
                      rule=to_me() & check_banlist())
list_Y = []


@hitokoto.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    user = str(event.user_id)
    global list_Y

    if countX(list_Y, user) == 3:
        list_Y.append(user)
        await bot.send(event, "额......需要咱安慰一下嘛~？")

    elif countX(list_Y, user) == 6:
        await bot.send(event, "如果心里感到难受就赶快去睡觉奥！别再憋自己了！")
        list_Y = list(set(list_Y))

    else:
        list_Y.append(user)
        URL = "https://api.imjad.cn/hitokoto/?cat=a&charset=utf-8&length=50&encode=json&fun=sync&source="
        info = {}

        try:
            info = json.loads(request_api_text(URL))
        except:
            await hitokoto.finish(errorRepo("请求错误"))

        await hitokoto.finish(info["hitokoto"])


laughFunny = on_command('来句笑话', rule=check_banlist())


@laughFunny.handle()  #type: ignore
async def _(bot: Bot, event: Event, state: dict) -> None:
    name = event.sender['nickname']
    result = []

    LAUGH_FILE = Path('.') / 'ATRI' / 'plugins' / 'plugin_chat' / 'laugh.txt'

    with open(LAUGH_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            result.append(line.strip('\n'))

    resu = choice(result)
    await laughFunny.finish(resu.replace("%name", name))


# 扔漂流瓶
plugin_name = 'drifting-bottle'
DRIFTING_BOTTLE_PATH = Path(
    '.') / 'ATRI' / 'plugins' / 'plugin_chat' / 'drifting_bottle.json'
driftingBottle = on_command('扔漂流瓶',
                            rule=to_me() & check_banlist()
                            & check_switch(plugin_name, True))


@driftingBottle.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    args = str(event.message).strip()

    if args:
        state['args'] = args


@driftingBottle.got('args', prompt='请告诉咱瓶中内容~！')
async def _(bot: Bot, event: Event, state: dict) -> None:
    args = state['args']
    user = event.user_id
    group = event.group_id

    if not DRIFTING_BOTTLE_PATH.is_file():
        with open(DRIFTING_BOTTLE_PATH, 'w') as f:
            f.write(json.dumps({}))

    with open(DRIFTING_BOTTLE_PATH, 'r') as f:
        data = json.load(f)

    num = len(data)
    data[num + 1] = [user, group, args]

    with open(DRIFTING_BOTTLE_PATH, 'w') as f:
        f.write(json.dumps(data))

    await driftingBottle.finish('漂流瓶已飘向远方...')


# 捡漂流瓶
getDriftingBottle = on_command('捞漂流瓶',
                               rule=to_me() & check_banlist()
                               & check_switch(plugin_name, True))


@getDriftingBottle.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    if not DRIFTING_BOTTLE_PATH.is_file():
        with open(DRIFTING_BOTTLE_PATH, 'w') as f:
            f.write(json.dumps({}))

    with open(DRIFTING_BOTTLE_PATH, 'r') as f:
        data = json.load(f)

    num = len(data)
    if not num:
        await getDriftingBottle.finish('暂无漂流瓶可供打捞呢~（')

    num = randint(1, num)
    bottle = data[str(num)]
    msg = bottle[2]

    msg0 = f'[CQ:at,qq={event.user_id}]\n'
    msg0 += f'漂流瓶[{num}]内容如下：\n'
    msg0 += msg

    await getDriftingBottle.finish(msg0)


# 清除漂流瓶
# *For SUPERUSERS
# - delall
# - del [num]
# eg: 清除漂流瓶 del 123
delDriftingBottle = on_command('清除漂流瓶',
                               rule=check_banlist(),
                               permission=SUPERUSER)


@delDriftingBottle.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    args = str(event.message).strip()

    if not args:

        await delDriftingBottle.finish("请查看文档获取帮助（")

    if not DRIFTING_BOTTLE_PATH.is_file():
        with open(DRIFTING_BOTTLE_PATH, 'w') as f:
            f.write(json.dumps({}))

        await delDriftingBottle.finish('清除了个寂寞...')

    with open(DRIFTING_BOTTLE_PATH, 'r') as f:
        data = json.load(f)

    if args[0] == 'delall':
        os.remove(os.path.abspath(DRIFTING_BOTTLE_PATH))

    elif args[0] == 'del':
        try:
            del data[args[1]]
        except:
            await delDriftingBottle.finish(errorRepo('清除失败了...'))

    with open(DRIFTING_BOTTLE_PATH, 'w') as f:
        f.write(json.dumps(data))
        f.close()

    result = args[1] if args[0] == 'del' else "ALL"
    await delDriftingBottle.finish(
        f'完成啦！成功清除漂流瓶[{result}]，目前还剩余[{len(data)}]个~')


# 舆情监听
publicOpinion = on_message(rule=check_banlist())
ban_temp_list = []


@publicOpinion.handle()
async def _(bot: Bot, event: Event, state: dict) -> None:
    global ban_temp_list
    msg = str(event.message)
    user = str(event.user_id)

    # 检查是否满足条件
    if countX(ban_temp_list,
              user) == Textcheck().get_times(str(Textcheck().check(msg))):
        ban_temp_list = list(set(ban_temp_list))
        ban(user)

        delta = timedelta(minutes=Textcheck().get_ban_time(msg))
        trigger = DateTrigger(run_date=datetime.now() + delta)
        scheduler.add_job(func=unban,
                          trigger=trigger,
                          args=(user, ),
                          misfire_grace_time=60)

        await publicOpinion.finish(Textcheck().check(msg))

    if Textcheck().check(msg) == "False":
        return

    if Textcheck().check(msg):
        if user in master:
            await publicOpinion.finish("主人你给我注意点阿？！你这可是在死亡边缘试探呢！！")

        ban_temp_list.append(int(user))

        await publicOpinion.finish(Textcheck().check(msg))
