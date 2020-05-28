import pickle
import discord
import studip_utility


class CommandHandler:

    def __init__(self, client):
        self.client = client
        with open('commands.pickle', 'rb') as commands_file:
            self.commands = pickle.load(commands_file)
        print(type(self.commands))
        print(self)

    async def handle_command(self, command, parameters, message):
        print(self.commands.get(command))
        print(self)
        await self.commands.get(command).get('action')(parameters=parameters, message=message)

    async def hello_command(self, parameters, message):
        print(self)
        await message.channel.send(parameters)

    async def help_command(self, parameters, message):
        print(self)
        await message.channel.send(parameters)

    def file_browser(self, parameters, message):
        return None

    def news_command(self, parameters, message):
        return None

    def update_command(self, parameters, message):
        return None

    def forum_browser(self, parameters, message):
        return None