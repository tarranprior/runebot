import asyncio

from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from utils import *

class Developer(commands.Cog, name='developer'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Bot configuration. Updates values in 'config.json' such as the bot prefix, activity status etc.
    '''
    @commands.group(name='configure', description='📏 Developer-only. Updates configuration values in such as the bot prefix, activity status etc.', invoke_without_command=True, aliases=['config'])
    @commands.is_owner()
    async def configure(self, ctx: Context):
        pass

    @configure.command(name='colours', description='📏 Developer-only. Toggles colour mode for embeds.', invoke_without_command=True)
    async def colours(self, ctx: Context):
        with open('config.json', 'r+') as json_file:
            data = json.load(json_file)
            if data['configuration']['colour_mode'] == 'True':
                data['configuration']['colour_mode'] = 'False'
                toggle = 'False'
            else:
                data['configuration']['colour_mode'] = 'True'
                toggle = 'True'
            json_file.seek(0)
            json.dump(data, json_file, indent=4)
            json_file.truncate()
        embed = EmbedFactory().create(title='Toggle Colour Mode', description=f'Colour mode set to `{toggle}`.')
        embed.timestamp = ctx.message.created_at
        embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
        return await ctx.reply(embed=embed)

    @configure.command(name='prefix', description="📏 Developer-only. Update the bot's prefix.", invoke_without_command=True)
    async def prefix(self, ctx: Context, prefix: str):
        if str(load_configuration()['configuration']['prefix']) != prefix:
            with open('config.json', 'r+') as json_file:
                data = json.load(json_file)
                data['configuration']['prefix'] = str(prefix)
                json_file.seek(0)
                json.dump(data, json_file, indent=4)
                json_file.truncate()
            embed = EmbedFactory().create(title='New Prefix Set', description=f'Prefix updated to `{prefix}` in `config.json`. Please restart the bot to apply the changes.')
            embed.timestamp = ctx.message.created_at
            embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
            return await ctx.send(embed=embed)
        embed = EmbedFactory().create(title='Prefix Error', description=f'Prefix is already set to `{prefix}`. Use `{prefix}botinfo` to fetch all current configuration values.', colour=disnake.Colour.red())
        return await ctx.reply(embed=embed)

    @configure.command(name='status', description="📏 Developer-only. Update the bot's default activity status.", invoke_without_command=True)
    async def status(self, ctx: Context, *, status: str):
        if str(load_configuration()['configuration']['activity']) != status:
            with open('config.json', 'r+') as json_file:
                data = json.load(json_file)
                data['configuration']['activity'] = str(status)
                json_file.seek(0)
                json.dump(data, json_file, indent=4)
                json_file.truncate()
            embed = EmbedFactory().create(title='New Status Set', description=f'Default activity status updated to `{status}` in `config.json`. Please restart the bot to apply the changes.')
            embed.timestamp = ctx.message.created_at
            embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
            return await ctx.send(embed=embed)
        embed = EmbedFactory().create(title='Activity Status Error', description=f"Status is already set to `{status}`. Use `{load_configuration()['configuration']['prefix']}botinfo` to fetch all current configuration values.", colour=disnake.Colour.red())
        return await ctx.reply(embed=embed)

    '''
    Bot configuration (slash.) Updates values in 'config.json' such as the bot prefix, activity status etc.
    '''
    @commands.slash_command(name='configure', description='📏 Developer-only. Updates configuration values in such as the bot prefix, activity status etc.')
    @commands.is_owner()
    async def configure_slash(self, inter: ApplicationCommandInteraction):
        pass

    @configure_slash.sub_command(name='colours', description='📏 Developer-only. Toggles colour mode for embeds.')
    async def colours_slash(self, inter: ApplicationCommandInteraction):
        with open('config.json', 'r+') as json_file:
            data = json.load(json_file)
            if data['configuration']['colour_mode'] == 'True':
                data['configuration']['colour_mode'] = 'False'
                toggle = 'False'
            else:
                data['configuration']['colour_mode'] = 'True'
                toggle = 'True'
            json_file.seek(0)
            json.dump(data, json_file, indent=4)
            json_file.truncate()
        embed = EmbedFactory().create(title='Toggle Colour Mode', description=f'Colour mode set to `{toggle}`.')
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'{inter.author.name} (ID: {inter.author.id})')
        return await inter.response.send_message(embed=embed)

    @configure_slash.sub_command(name='prefix', description="📏 Developer-only. Update the bot's prefix.", options=[
        Option(
                name='Prefix',
                description='Specify a new prefix.',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def prefix_slash(self, inter: ApplicationCommandInteraction, prefix: str):
        if str(load_configuration()['configuration']['prefix']) != prefix:
            with open('config.json', 'r+') as json_file:
                data = json.load(json_file)
                data['configuration']['prefix'] = str(prefix)
                json_file.seek(0)
                json.dump(data, json_file, indent=4)
                json_file.truncate()
            embed = EmbedFactory().create(title='New Prefix Set', description=f'Prefix updated to `{prefix}` in `config.json`. Please restart the bot to apply the changes.')
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'{inter.author.name} (ID: {inter.author.id})')
            return await inter.response.send_message(embed=embed)
        embed = EmbedFactory().create(title='Prefix Error', description=f'Prefix is already set to `{prefix}`. Use `{prefix}botinfo` to fetch all current configuration values.', colour=disnake.Colour.red())
        return await inter.response.send_message(embed=embed)

    @configure_slash.sub_command(name='status', description="📏 Developer-only. Update the bot's default activity status.", options=[
        Option(
                name='Status',
                description='Specify a new status.',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def status_slash(self, inter: ApplicationCommandInteraction, status: str):
        if str(load_configuration()['configuration']['activity']) != status:
            with open('config.json', 'r+') as json_file:
                data = json.load(json_file)
                data['configuration']['activity'] = str(status)
                json_file.seek(0)
                json.dump(data, json_file, indent=4)
                json_file.truncate()
            embed = EmbedFactory().create(title='New Status Set', description=f'Default activity status updated to `{status}` in `config.json`. Please restart the bot to apply the changes.')
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'{inter.author.name} (ID: {inter.author.id})')
            return await inter.response.send_message(embed=embed)
        embed = EmbedFactory().create(title='Activity Status Error', description=f"Status is already set to `{status}`. Use `{load_configuration()['configuration']['prefix']}botinfo` to fetch all current configuration values.", colour=disnake.Colour.red())
        return await inter.response.send_message(embed=embed)

    '''
    Purge. Deletes a specified number of messages in the context channel.
    :param number: (Integer) - Represents the number of messages to delete.
    '''
    @commands.command(name='purge', description='📏 Developer-only. Deletes a specified number of messages.')
    @commands.is_owner()
    async def purge(self, ctx: Context, number: int) -> None:
        try:
            int(number)
        except:
            embed = EmbedFactory().create(title='Value Error', description=f"Value error. Please enter an integer.\nFor more information on usage and parameters, use `{load_configuration()['configuration']['prefix']}help <command>`.", colour=disnake.Colour.red())
            return await ctx.reply(embed=embed)
        await ctx.message.delete()
        messages = await ctx.channel.purge(limit=int(number))
        purge_message = await ctx.send(f'{len(messages)} messages have been purged.')
        await asyncio.sleep(1)
        await purge_message.delete()

    '''
    Purge (slash.) Deletes a specified number of messages in the context channel.
    :param number: (Integer) - Represents the number of messages to delete.
    '''
    @commands.slash_command(name='purge', description='📏 Developer-only. Deletes a specified number of messages.', options=[
            Option(
                name='Number',
                description='Specify a number of messages to purge.',
                type=OptionType.integer,
                required=True
            )
        ]
    )
    @commands.is_owner()
    async def purge_slash(self, inter: ApplicationCommandInteraction, number: int):
        messages = await inter.channel.purge(limit=int(number))
        await inter.send(f'{len(messages)} messages have been purged.')
        await asyncio.sleep(1)
        await inter.delete_original_message()

def setup(bot) -> None:
    bot.add_cog(Developer(bot))