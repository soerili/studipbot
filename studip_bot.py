import os
import json
import pickle

from command_handler import CommandHandler

import discord


class StudIPBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.ch = CommandHandler(self)
        print('Added CommandHandler')

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        if message.author.id is self.user.id:
            return

        if message.content.startswith('!'):

            try:
                command, parameters = message.content.split(' ', 1)
            except ValueError:
                command, parameters = message.content, ""
            await self.ch.handle_command(command[1:], parameters, message)


client = StudIPBot()
with open('token', 'r') as token_file:
    token = token_file.readline()
client.run(token)
