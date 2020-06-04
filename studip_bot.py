import asyncio
import os
import json
import pickle

import studip_utility

import logging
import discord
from exceptions import *
from discord.ext import tasks, commands
import yaml


studIPBot = commands.Bot(command_prefix='!')
with open('tasks.yml', 'r') as file:
    task_list = yaml.load(file, Loader=yaml.Loader)
if task_list is None:
    task_list = []
tasks_index = 0


def known_user():
    async def predicate(ctx):
        return studip_utility.is_in_db(str(ctx.author))
    return commands.check(predicate)


@tasks.loop(minutes=5)
async def check_for_updates():
    if not task_list:
        return
    i = check_for_updates.current_loop % len(task_list)
    print(task_list[i][0], task_list[i][1], task_list[i][2])
    new_files = studip_utility.check_new_files(task_list[i][0], task_list[i][1])
    if not new_files:
        return
    course_name = studip_utility.get_course_name(task_list[i][0])
    channel = studIPBot.get_channel(int(task_list[i][2]))
    await channel.send(f'In {course_name} gibt es neue Dateien')
    await channel.send(files=new_files)

@studIPBot.event
async def on_ready():
    print('Logged in as')
    print(studIPBot.user.name)
    print(studIPBot.user.id)
    print('------')
    await studIPBot.change_presence(activity=discord.Streaming(name="Python Programming!", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
    check_for_updates.start()


@studIPBot.group(aliases=['s'])
async def studip(ctx):
    print(type(ctx.author))
    if ctx.invoked_subcommand is None:
        await ctx.send('Help is on the way!')


@studip.command()
@known_user()
async def task(ctx, arg):
    studip_id = studip_utility.alias_resolver.get(arg)
    add = True
    if task_list:
        for items in task_list:
            if studip_id in items:
                items[0] = studip_id
                items[1] = str(ctx.author)
                items[2] = ctx.channel.id
                add = False
    if add:
        task_list.append([studip_id, str(ctx.author), ctx.channel.id])
    with open('tasks.yml', 'w') as out_file:
        data = yaml.dump(task_list, out_file)
    course_name = studip_utility.get_course_name(studip_id)
    await ctx.send(f'Ich habe für {course_name} einen Update Task gestartet.\nNeue Ankündigungen und Dateien werden in diesen Channel gepostet.')


@studip.command()
@known_user()
async def update(ctx, arg):
    file_list = studip_utility.check_new_files(arg, str(ctx.author))
    print(file_list)
    if file_list:
        await ctx.send('Es gibt folgende neue Dateien für dich:')
        await ctx.send(files=file_list)


@studip.command()
@known_user()
async def files(ctx, arg):
    studip_utility.get_local_folders(arg)

    async def show_folder(folder):
        msg = await ctx.send('123')
        # await msg.add_reaction('\N{THUMBS UP SIGN}')

        def check(reaction, user):
            print(reaction.message + '###' + msg)
            return reaction.message is msg and user is ctx.author
        try:
            reaction, user = studIPBot.wait_for('reaction_add', timeout=20.0, check=check)
            print(reaction.message + '###' + user)
        except asyncio.TimeoutError:
            await ctx.send('nenenene')
        else:
            await ctx.send('jajajaja')
    await show_folder(arg)


@studip.command()
@known_user()
async def forum(ctx):
    await ctx.send('Not yet implemented!')


@studip.command()
@known_user()
async def news(ctx, arg1=None, arg2=1):
    try:
        arg1_int = int(arg1)
        arg2 = arg1_int
        arg1 = None
    except ValueError:
        pass
    except TypeError:
        pass
    embed_news = studip_utility.get_news(str(ctx.author), arg1, arg2)
    await ctx.send(embed=embed_news)


@studip.command()
@known_user()
async def alias(ctx, arg1, arg2):
    name = studip_utility.add_alias(arg1, arg2)
    await ctx.send(f'Alias {arg1} für {name} erfolgreich hinzugefügt.')


@studip.command()
async def login(ctx):
    await ctx.send('Bitte schreib mir deinen StudIP login per privater Nachricht mit Leerzeichen getrennt!')

    def check(message):
        return message.channel.type == discord.ChannelType.private

    try:
        msg = await studIPBot.wait_for('message', timeout=30, check=check)
    except asyncio.TimeoutError:
        await ctx.send('Timeout für Login Eingabe abgelaufen, bitte versuche es erneut')
        return
    if msg is None:
        return
    user, password = msg.content.split(' ')
    if studip_utility.setup_user(str(ctx.author), user, password):
        await ctx.send('Login war erfolgreich, viel Spaß beim benutzen des Bots!')
    else:
        await ctx.send('Probier es bitte nochmal!')


@news.error
@update.error
@forum.error
async def studip_error(ctx, error):
    if type(error.original) is AliasError:
        await ctx.send(error.original.message + '\n' + studip_utility.formatted_courses_list())
    else:
        await ctx.send(error.original.message)


studip_utility.init()
with open('token', 'r') as token_file:
    token = token_file.readline()
studIPBot.run(token)
