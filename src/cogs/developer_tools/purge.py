import asyncio

from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from utils import *


class Purge(commands.Cog, name='purge'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    📏 DEVELOPER-ONLY. Deletes a specified number of messages in the context channel.
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

    @commands.slash_command(name='purge', description='📏 Developer-only. Deletes a specified number of messages.', options=[
            Option(
                name='number',
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
    bot.add_cog(Purge(bot))