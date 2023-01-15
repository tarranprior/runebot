from templates.bot import Bot
from utils import *

import asyncio

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Purge(commands.Cog, name='purge'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Deletes a specified number of messages in the context channel.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param limit: (Integer) - Represents the number of messages to delete.
    '''

    @commands.slash_command(
        name='purge',
        description='Clears a specific number of bot response messages.',
        options=[
            Option(
                name='limit',
                description='Specify a number of messages to purge.',
                type=OptionType.integer,
                required=True)])
    async def purge(self, inter: ApplicationCommandInteraction, limit: int):
        if not inter.user.id == inter.guild.owner_id:
            raise exceptions.NoAdministratorPermissions
        messages = await inter.channel.purge(limit=int(limit), check=lambda x: (x.author.id == self.bot.user.id))
        await inter.send(f'{len(messages)} messages have been purged.')
        await asyncio.sleep(1)
        await inter.delete_original_message()


def setup(bot) -> None:
    bot.add_cog(Purge(bot))
