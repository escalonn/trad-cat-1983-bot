import json
import logging
import os
import re
import aiohttp
import discord

def canon_to_str(c_num, p_num1=None, p_num2=None, n_num1=None, n_num2=None,
                 latin=False):
    strs = ['**Can. ', c_num, '** — ']
    if latin:
        canon = latincanons[c_num]
    else:
        canon = canons[c_num]
    if p_num1 is None:
        if n_num1 is None:
            if canon['text']:
                strs.append(canon['text'])
            if canon['paragraphs']:
                if not strs[-1][-1].isspace():
                    strs.append('\n')
                for para_num, para in sorted(canon['paragraphs'].items()):
                    if int(para_num) > 1:
                        strs.append('\n')
                    strs.extend(['§ ', para_num, '. '])
                    if para['text']:
                        strs.append(para['text'])
                    if para['numbers']:
                        if not strs[-1][-1].isspace():
                            strs.append('\n\t')
                        for num_num, num in sorted(para['numbers'].items()):
                            if int(num_num) > 1:
                                strs.append('\n\t')
                            strs.extend([num_num, '° '])
                            if num['text']:
                                strs.append(num['text'])
            if canon['numbers']:
                if not strs[-1][-1].isspace():
                    strs.append('\n\t')
                for num_num, num in sorted(canon['numbers'].items()):
                    if int(num_num) > 1:
                        strs.append('\n\t')
                    strs.extend([num_num, '° '])
                    if num['text']:
                        strs.append(num['text'])
        else:
            if n_num2 is None:
                num = canon['numbers'][n_num1]
                strs.extend([n_num1, '° '])
                if num['text']:
                    strs.append(num['text'])
            else:
                for i in range(int(n_num1), int(n_num2) + 1):
                    if i > int(n_num1):
                        strs.append('\n\t')
                    num = canon['numbers'][str(i)]
                    strs.extend([str(i), '° '])
                    if num['text']:
                        strs.append(num['text'])
    else:
        if p_num2 is None:
            para = canon['paragraphs'][p_num1]
            strs.extend(['§ ', p_num1, '. '])
            if n_num1 is None:
                if para['text']:
                    strs.append(para['text'])
                if para['numbers']:
                    if not strs[-1][-1].isspace():
                        strs.append('\n\t')
                    for num_num, num in sorted(para['numbers'].items()):
                        if int(num_num) > 1:
                            strs.append('\n\t')
                        strs.extend([num_num, '° '])
                        if num['text']:
                            strs.append(num['text'])
            else:
                if n_num2 is None:
                    num = para['numbers'][n_num1]
                    strs.extend([n_num1, '° '])
                    if num['text']:
                        strs.append(num['text'])
                else:
                    for i in range(int(n_num1), int(n_num2) + 1):
                        if i > int(n_num1):
                            strs.append('\n\t')
                        num = para['numbers'][str(i)]
                        strs.extend([str(i), '° '])
                        if num['text']:
                            strs.append(num['text'])
        else:
            for i in range(int(p_num1), int(p_num2) + 1):
                if i > int(p_num1):
                    strs.append('\n')
                para = canon['paragraphs'][str(i)]
                strs.extend(['§ ', str(i), '. '])
                if para['text']:
                    strs.append(para['text'])
                if para['numbers']:
                    if not strs[-1][-1].isspace():
                        strs.append('\n\t')
                    for num_num, num in sorted(para['numbers'].items()):
                        if int(num_num) > 1:
                            strs.append('\n\t')
                        strs.extend([num_num, '° '])
                        if num['text']:
                            strs.append(num['text'])
    return ''.join(strs)

def query_to_str(c_num1, c_num2, p_num1, p_num2, n_num1, n_num2, latin=False):
    strs = []
    if c_num2 is None:
        strs.append(canon_to_str(c_num1, p_num1, p_num2, n_num1, n_num2,
                                 latin))
    else:
        for i in range(int(c_num1), int(c_num2) + 1):
            if i > int(c_num1):
                strs.append('\n')
            strs.append(canon_to_str(str(i), latin=latin))
    return ''.join(strs)

logging.basicConfig()

with open('cic1983.json') as f:
    canons = json.load(f)
canons = {k: v for d in canons for k, v in d.items()}
with open('cic1983latin.json') as f:
    latincanons = json.load(f)
latincanons = {k: v for d in latincanons for k, v in d.items()}

if 'PORT' in os.environ:
    port = int(os.environ['PORT'])
    connector = aiohttp.TCPConnector(local_addr=('0.0.0.0', port))
    print('Using port {}'.format(port))
else:
    connector = None

client = discord.Client(connector=connector)
member_self = {}

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    match = re.search(
        r'\bC(?:c|an(?:one?s?|n)?)\.?\s*(\d+)(?:\s*[-–]\s*(\d+))?'
        r'(?:\s*[§p][§ps]?\.?\s*(\d+)(?:\s*[-–]\s*(\d+))?)?'
        r'(?:\s*n?[ns]?\.?\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*°?[°s]?)?',
        message.content, flags=re.I)
    if match is None:
        return
    latin = 'latin' in str(message.channel)
    try:
        msg = query_to_str(*match.groups(), latin=latin)
    except KeyError:
        return
    if len(msg) > 10000:
        return
    nickname = ('1983 Codex Iuris Canonici' if latin else
                '1983 Code of Canon Law')
    if message.server is not None:
        await client.change_nickname(member_self[message.server], nickname)
    await client.send_message(message.channel, msg)
    if message.server is not None:
        await client.change_nickname(member_self[message.server], '1983 CIC')


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    for server in client.servers:
        member_self[server] = server.get_member(client.user.id)
        await client.change_nickname(member_self[server], '1983 CIC')

client.run('Mjg3MjU3MzMxMTQ4OTE0Njg5.C5spCQ.j5PmkJ9rGroN7qP6MyfD2213yKQ')
