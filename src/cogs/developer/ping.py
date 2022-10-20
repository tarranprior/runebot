import time

from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction

from templates.bot import Bot
from config import *
from utils import *


class Ping(commands.Cog, name='ping'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot    

    '''
    📏 DEVELOPER-ONLY (Owner.) Displays the bot's latency.
    '''
    @commands.command(name='ping', description="📏 Developer-only. Display the bot's latency.")
    @commands.is_owner()
    async def ping(self, ctx: Context) -> None:
        time_before = time.monotonic()

        embed = EmbedFactory().create(
                                    title='Ping',
                                    description="Display the bot's latency.\nBot running slow? Contact the developer on [GitHub](https://github.com/tarranprior/runebot)."
        )
        embed.timestamp = ctx.message.created_at
        embed.set_footer(text='📏 Developer-only')
        embed.add_field(name="Latency output", value=f"```\nPong! {round(self.bot.latency*1000)}ms • REST: ...```")
        message = await ctx.send(embed=embed)
        rest = round((time.monotonic() - time_before) * 1000, 1)

        embed = EmbedFactory().create(
                                    title='Ping',
                                    description="Display the bot's latency.\nBot running slow? Contact the developer on [GitHub](https://github.com/tarranprior/runebot)."
            )
        embed.add_field(name="Latency output", value=f"```\nPong!\nWS: {round(self.bot.latency*1000, 1)}ms • REST: {rest}ms```")
        embed.timestamp = ctx.message.created_at
        embed.set_footer(text='📏 Developer-only')
        await message.edit(embed=embed)

    @commands.slash_command(name="ping", description="📏 Developer-only. Display the bot's latency.")
    @commands.is_owner()
    async def ping_slash(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        time_before = time.monotonic()

        embed = EmbedFactory().create(
                                    title='Ping',
                                    description="Display the bot's latency.\nBot running slow? Contact the developer on [GitHub](https://github.com/tarranprior/runebot).",
            )
        embed.timestamp = inter.created_at
        embed.set_footer(text='📏 Developer-only')
        embed.add_field(name="Latency output", value=f"```\nPong! {round(self.bot.latency*1000)}ms • REST: ...```")
        message = await inter.followup.send(embed=embed)
        rest = round((time.monotonic() - time_before) * 1000, 1)

        embed = EmbedFactory().create(
                                    title='Ping',
                                    description="Display the bot's latency.\nBot running slow? Contact the developer on [GitHub](https://github.com/tarranprior/runebot)."
            )
        embed.add_field(name="Latency output", value=f"```\nPong!\nWS: {round(self.bot.latency*1000, 1)}ms • REST: {rest}ms```")
        embed.timestamp = inter.created_at
        embed.set_footer(text='📏 Developer-only')
        await message.edit(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Ping(bot))