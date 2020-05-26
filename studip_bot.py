import os
import json

import discord


with open('commands.json', 'r') as commands_file:
    COMMANDS = json.load(commands_file)


class StudIPBot(discord.Client):
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
                command, parameters = message.content, None
            command.pop(0)
            await COMMANDS.get(command).get('action')(parameters, message, self)


client = StudIPBot()
client.run('token')
