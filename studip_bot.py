import os
import json
import pickle

import studip_utility

import logging
import discord
from discord.ext import commands


logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


studIPBot = commands.Bot(command_prefix='!')


@studIPBot.event
async def on_ready():
    print('Logged in as')
    print(studIPBot.user.name)
    print(studIPBot.user.id)
    print('------')
    await studIPBot.change_presence(activity=discord.Streaming(name="Python Programming!", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"))


@studIPBot.group()
async def studip(ctx):
    if ctx.invoked_subcommand is None:
        print(ctx.author)
        await ctx.send('Help is on the way!')


@studip.command()
async def files(ctx):
    await ctx.send('Files are on the way!')


@studip.command()
async def forum(ctx):
    await ctx.send('Not yet implemented!')


@studip.command()
async def news(ctx):
    await ctx.send(embed=studip_utility.get_news(str(ctx.author)))


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

studip_utility.init()
with open('token', 'r') as token_file:
    token = token_file.readline()
studIPBot.run(token)
