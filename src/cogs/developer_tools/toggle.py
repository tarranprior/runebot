from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from utils import *

class Toggle(commands.Cog, name='toggle'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot    

    '''
    📏 DEVELOPER-ONLY. Toggles colour mode on/off. An alternative to `configure colours`.
    :param None:
    '''
    def toggle_colour_mode(self) -> None:
        if check_colour_mode() == True:
            update_configuration(key='colour_mode', value='False')
            new_toggle = False
            return(new_toggle)
        update_configuration(key='colour_mode', value='True')
        new_toggle = True
        return(new_toggle)

    @commands.command(name='toggle', description='📏 Developer-only. Toggles colour mode for embeds.')
    async def toggle(self, ctx: Context):
        toggle = self.toggle_colour_mode()
        embed = EmbedFactory().create(title='Toggle colour mode', description=f'Colour mode set to `{toggle}`.')
        embed.timestamp = ctx.message.created_at
        embed.set_footer(text=f'{ctx.message.author.name} (ID: {ctx.message.author.id})')
        return await ctx.send(embed=embed)

    @commands.slash_command(name='toggle', description='📏 Developer-only. Toggles colour mode for embeds.')
    @commands.is_owner()
    async def toggle_slash(self, inter: ApplicationCommandInteraction):
        toggle = self.toggle_colour_mode()
        embed = EmbedFactory().create(title='Toggle colour mode', description=f'Colour mode set to `{toggle}`.')
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'{inter.author.name} (ID: {inter.author.id})')
        return await inter.response.send_message(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Toggle(bot))