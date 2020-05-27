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
            command[1:]
            print(type(message))
            print(message)
            for x in message:
                print(x)
            #await COMMANDS.get(command).get('action')(parameters, message, self)


async def update_command(parameters, client):
    return None


async def forum_command(parameters, client):
    return None


client = StudIPBot()
client.run('')
