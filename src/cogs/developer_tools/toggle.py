from disnake.ext import commands
from disnake.ext.commands import Context
from disnake.ui import View, Button
from disnake import ApplicationCommandInteraction

from templates.bot import Bot
from config import *
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
                                    title=f'Toggle colour mode set to {toggle}',
                                    description=f"Colour mode has been set to **{toggle}**. If you'd like to reverse this change, simpy use the buttons below or use `toggle colours` again.",
                                    thumbnail_url=LEVER_ICO
            )
            if toggle == True:
                embed.colour = embed.colour.blurple()
            else:
                embed.colour = embed.colour.red()
            embed.timestamp = ctx.message.created_at
            view=View()
            toggle_on = Button(label='Toggle on', emoji='⚙️', style=disnake.ButtonStyle.grey)
            toggle_off = Button(label='Toggle off', emoji='⚙️', style=disnake.ButtonStyle.grey)
            view.add_item(toggle_on)
            view.add_item(toggle_off)
            await ctx.send(embed=embed, view=view)
        else:
            embed = EmbedFactory().create(
                                    title='Usage',
                                    description=f'```\ntoggle <colours>```'
            )
            await ctx.send(embed=embed)

        async def toggle_option_on(interaction_1):
            await interaction_1.response.defer()
            if check_mode('colour_mode') == True:
                embed = EmbedFactory().create(
                                title=f'Toggle colour mode already set to True!',
                                description=f"Colour mode is already set to **True**!",
                                thumbnail_url=LEVER_ICO
                )
                embed.colour = embed.colour.blurple()
                embed.timestamp = interaction_1.created_at
                return await interaction_1.followup.send(embed=embed)
            update_configuration(key='colour_mode', value='True')
            embed = EmbedFactory().create(
                                title=f'Toggle colour mode set to True.',
                                description=f"Colour mode set to **True**.",
                                thumbnail_url=LEVER_ICO
            )
            embed.colour = embed.colour.blurple()
            embed.timestamp = interaction_1.created_at
            return await interaction_1.followup.send(embed=embed)

        async def toggle_option_off(interaction_2):
            await interaction_2.response.defer()
            if check_mode('colour_mode') == False:
                embed = EmbedFactory().create(
                                title=f'Toggle colour mode already set to False!',
                                description=f"Colour mode is already set to **False**!",
                                thumbnail_url=LEVER_ICO
                )
                embed.colour = embed.colour.red()
                embed.timestamp = interaction_2.created_at
                return await interaction_2.followup.send(embed=embed)
            update_configuration(key='colour_mode', value='False')
            embed = EmbedFactory().create(
                                title=f'Toggle colour mode set to False.',
                                description=f"Colour mode set to **False**.",
                                thumbnail_url=LEVER_ICO
            )
            embed.colour = embed.colour.red()
            embed.timestamp = interaction_2.created_at
            return await interaction_2.followup.send(embed=embed)

        view.children[0].callback = toggle_option_on
        view.children[1].callback = toggle_option_off

    @commands.slash_command(name='toggle', description='📏 Developer-only. Toggles configuration modes on/off.')
    @commands.is_owner()
    async def toggle_slash(self, inter: ApplicationCommandInteraction):
        return

    @toggle_slash.sub_command(name='colours', description='📏 Developer-only. Toggles `colour_mode` on/off.')
    async def toggle_colours(self, inter: ApplicationCommandInteraction):
        await inter.response.defer()
        toggle = self.toggle_mode('colour_mode')
        embed = EmbedFactory().create(
                                title=f'Toggle colour mode set to {toggle}',
                                description=f"Colour mode has been set to **{toggle}**. If you'd like to reverse this change, simpy use the buttons below or use `toggle colours` again.",
                                thumbnail_url=LEVER_ICO
        )
        if toggle == True:
            embed.colour = embed.colour.blurple()
        else:
            embed.colour = embed.colour.red()
        embed.timestamp = inter.created_at
        view=View()
        toggle_on = Button(label='Toggle on', emoji='⚙️', style=disnake.ButtonStyle.grey)
        toggle_off = Button(label='Toggle off', emoji='⚙️', style=disnake.ButtonStyle.grey)
        view.add_item(toggle_on)
        view.add_item(toggle_off)
        await inter.followup.send(embed=embed, view=view)

        async def toggle_option_on(interaction_1):
            await interaction_1.response.defer()
            if check_mode('colour_mode') == True:
                embed = EmbedFactory().create(
                                title=f'Toggle colour mode already set to True!',
                                description=f"Colour mode is already set to **True**!",
                                thumbnail_url=LEVER_ICO
                )
                embed.colour = embed.colour.blurple()
                embed.timestamp = inter.created_at
                return await inter.followup.send(embed=embed)
            update_configuration(key='colour_mode', value='True')
            embed = EmbedFactory().create(
                                title=f'Toggle colour mode set to True.',
                                description=f"Colour mode set to **True**.",
                                thumbnail_url=LEVER_ICO
            )
            embed.colour = embed.colour.blurple()
            embed.timestamp = inter.created_at
            return await inter.followup.send(embed=embed)

        async def toggle_option_off(interaction_2):
            await interaction_2.response.defer()
            if check_mode('colour_mode') == False:
                embed = EmbedFactory().create(
                                title=f'Toggle colour mode already set to False!',
                                description=f"Colour mode is already set to **False**!",
                                thumbnail_url=LEVER_ICO
                )
                embed.colour = embed.colour.red()
                embed.timestamp = inter.created_at
                return await inter.followup.send(embed=embed)
            update_configuration(key='colour_mode', value='False')
            embed = EmbedFactory().create(
                                title=f'Toggle colour mode set to False.',
                                description=f"Colour mode set to **False**.",
                                thumbnail_url=LEVER_ICO
            )
            embed.colour = embed.colour.red()
            embed.timestamp = inter.created_at
            return await inter.followup.send(embed=embed)

        view.children[0].callback = toggle_option_on
        view.children[1].callback = toggle_option_off

def setup(bot) -> None:
    bot.add_cog(Toggle(bot))