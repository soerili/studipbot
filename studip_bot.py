import os
import json
import pickle

import studip_utility

import logging
import discord
from exceptions import *
from discord.ext import commands


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


studIPBot = commands.Bot(command_prefix='!')


def known_user():
    async def predicate(ctx):
        return studip_utility.is_in_db(str(ctx.author))
    return commands.check(predicate)


@studIPBot.event
async def on_ready():
    print('Logged in as')
    print(studIPBot.user.name)
    print(studIPBot.user.id)
    print('------')
    await studIPBot.change_presence(activity=discord.Streaming(name="Python Programming!", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))


@studIPBot.group(aliases=['s'])
async def studip(ctx):
    print(type(ctx.author))
    if ctx.invoked_subcommand is None:
        await ctx.send('Help is on the way!')


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
    def show_files(folder):
        print()


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
    except:
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
