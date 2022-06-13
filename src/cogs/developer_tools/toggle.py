from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, SlashCommand

from templates.bot import Bot
from utils import *


class Toggle(commands.Cog, name='toggle'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot    

    '''
    📏 DEVELOPER-ONLY. Toggle function for toggling configuration modes on/off (such as `colour_mode`, `hide_scrolls` etc.)
    :param mode: (String) - Represents the mode to toggle.
    '''
    def toggle_mode(self, mode: str) -> None:
        if check_mode(mode) == True:
            update_configuration(key=mode, value='False')
            return(False)
        update_configuration(key=mode, value='True')
        return(True)

    @commands.command(name='toggle', description='📏 Developer-only. Toggles configuration modes on/off.')
    async def toggle(self, ctx: Context, *, mode: str):
        if mode == 'colours':
            toggle = self.toggle_mode('colour_mode')
            embed = EmbedFactory().create(
                                    title='Toggle colour mode',
                                    description=f"Colour mode has been set to `{toggle}`. If you'd like to reverse this change at any time, simpy use `toggle colours` again."
            )
            embed.timestamp = ctx.message.created_at
            embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
            return await ctx.send(embed=embed)

        elif mode == 'scrolls':
            toggle = self.toggle_mode('hide_scrolls')
            embed = EmbedFactory().create(
                                    title='Toggle scrolls',
                                    description=f"Hide scrolls has been set to `{toggle}`. If you'd like to reverse this change at any time, simpy use `toggle scrolls` again."
            )
            embed.timestamp = ctx.message.created_at
            embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
            return await ctx.send(embed=embed)

        else:
            embed = EmbedFactory().create(
                                    title='Usage',
                                    description=f'```\ntoggle <colours|scrolls>```'
            )
            embed.timestamp = ctx.message.created_at
            embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
            return await ctx.send(embed=embed)

    @commands.slash_command(name='toggle', description='📏 Developer-only. Toggles configuration modes on/off.')
    @commands.is_owner()
    async def toggle_slash(self, inter: ApplicationCommandInteraction):
        return

    @toggle_slash.sub_command(name='colours', description='📏 Developer-only. Toggles `colour_mode` on/off.')
    async def toggle_colours(self, inter: ApplicationCommandInteraction):
        toggle = self.toggle_mode('colour_mode')
        embed = EmbedFactory().create(
                                title='Toggle colour mode',
                                description=f"Colour mode has been set to `{toggle}`. If you'd like to reverse this change at any time, simpy use `toggle colours` again."
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'{inter.author.name} (ID: {inter.author.id})')
        return await inter.response.send_message(embed=embed)

    @toggle_slash.sub_command(name='scrolls', description='📏 Developer-only. Toggles `hide_scrolls` on/off.')
    async def toggle_scrolls(self, inter: ApplicationCommandInteraction):
        toggle = self.toggle_mode('hide_scrolls')
        embed = EmbedFactory().create(
                                title='Toggle scrolls',
                                description=f"Hide scrolls has been set to `{toggle}`. If you'd like to reverse this change at any time, simpy use `toggle scrolls` again."
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'{inter.author.name} (ID: {inter.author.id})')
        return await inter.response.send_message(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Toggle(bot))