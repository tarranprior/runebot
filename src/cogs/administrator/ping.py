from config import *
from templates.bot import Bot
from utils import *

import time

from disnake.ext import commands
from disnake import ApplicationCommandInteraction


class Ping(commands.Cog, name='ping'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='ping',
                            description='Allows you to view the bot\'s current latency.')
    async def ping_slash(self, inter: ApplicationCommandInteraction) -> None:
        if not inter.user.id == inter.guild.owner_id:
            raise exceptions.NoAdministratorPermissions
        await inter.response.defer()

        time_before = time.monotonic()

        embed = EmbedFactory().create(
            title='Ping',
            description='Display the bot\'s latency.\nBot running slow? Contact the developer on [GitHub](https://github.com/tarranprior/runebot).')
        embed.add_field(
            name='Latency output',
            value=f'```\nPong! {round(self.bot.latency*1000)}ms • REST: ...```')
        embed.timestamp = inter.created_at
        await inter.followup.send(embed=embed)

        rest = round((time.monotonic() - time_before) * 1000, 1)

        embed = EmbedFactory().create(
            title='Ping',
            description='Display the bot\'s latency.\nBot running slow? Contact the developer on [GitHub](https://github.com/tarranprior/runebot).')
        embed.add_field(
            name='Latency output',
            value=f'```\nPong!\nWS: {round(self.bot.latency*1000, 1)}ms • REST: {rest}ms```')
        embed.timestamp = inter.created_at
        await inter.edit_original_message(embed=embed)


def setup(bot) -> None:
    bot.add_cog(Ping(bot))
