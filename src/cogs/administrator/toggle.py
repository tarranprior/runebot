from config import *
from templates.bot import Bot
from utils import *

import asyncio

from disnake.ext import commands
from disnake.ui import View, Button
from disnake import ApplicationCommandInteraction


class Toggle(commands.Cog, name='toggle'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Colours function for toggling colour_mode on/off for the current guild.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param toggle: (Bool) - Represents a boolean value (toggle) for the colour mode field.
    '''

    async def toggle_colour_mode(self, inter: ApplicationCommandInteraction, toggle: bool) -> None:
        if not inter.user.id == inter.guild.owner_id:
            raise exceptions.NoAdministratorPermissions

        if await get_colour_mode(self, inter.guild_id, inter.guild.owner_id) == toggle:
            embed = EmbedFactory().create(
                title=f'Toggle colour mode already set to {toggle}!',
                description=f"Colour mode is already set to `{toggle}`!",
                thumbnail_url=LEVER_ICO)
            if toggle:
                embed.colour = embed.colour.blurple()
            else:
                embed.colour = embed.colour.red()
            embed.timestamp = inter.created_at
            toggle_message = await inter.followup.send(embed=embed)
            await asyncio.sleep(3)
            return await toggle_message.delete()

        await update_colour_mode(self, inter.guild_id, toggle)
        embed = EmbedFactory().create(
            title=f'Toggle colour mode set to {toggle}.',
            description=f"Colour mode set to `{toggle}`. If you'd like to reverse this change, simpy use `/colours` again.",
            thumbnail_url=LEVER_ICO)
        if toggle:
            embed.colour = embed.colour.blurple()
        else:
            embed.colour = embed.colour.red()
        embed.timestamp = inter.created_at
        await inter.followup.send(embed=embed)

    '''
    Creates default toggle slash command for user interaction.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    '''

    @commands.slash_command(name='toggle',
                            description='Toggle configuration values on/off for this specific guild.')
    async def toggle(self, inter: ApplicationCommandInteraction) -> None:
        return

    '''
    Creates the colours slash subcommand for user interaction.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    '''

    @toggle.sub_command(name='colours',
                        description='Toggles colour mode on/off for this specific guild.')
    async def toggle_colours(self, inter: ApplicationCommandInteraction) -> None:
        await inter.response.defer()
        if inter.user.id != inter.guild.owner_id:
            raise exceptions.NoAdministratorPermissions
        current_toggle = await get_colour_mode(self, inter.guild_id, inter.guild.owner_id)

        if current_toggle:
            await update_colour_mode(self, inter.guild_id, False)
            embed = EmbedFactory().create(
                title=f'Toggle colour mode set to False',
                description=f'Colour mode has been set to `False`. If you\'d like to reverse this change, simpy use the buttons below or use `/colours` again.',
                thumbnail_url=LEVER_ICO)
            embed.colour = embed.colour.red()
        else:
            await update_colour_mode(self, inter.guild_id, True)
            embed = EmbedFactory().create(
                title=f'Toggle colour mode set to True',
                description=f'Colour mode has been set to `True`. If you\'d like to reverse this change, simpy use the buttons below or use `/colours` again.',
                thumbnail_url=LEVER_ICO)
            embed.colour = embed.colour.blurple()

        embed.timestamp = inter.created_at
        view = View(timeout=None)
        toggle_on = Button(
            label='Toggle on',
            emoji='⚙️',
            style=disnake.ButtonStyle.grey)
        toggle_off = Button(
            label='Toggle off',
            emoji='⚙️',
            style=disnake.ButtonStyle.grey)
        view.add_item(toggle_on)
        view.add_item(toggle_off)
        await inter.followup.send(embed=embed, view=view)

        async def toggle_option_on(inter: ApplicationCommandInteraction):
            await inter.response.defer()
            await self.toggle_colour_mode(inter, True)
            toggle_on.disabled = True
            toggle_off.disabled = True
            await inter.edit_original_message(view=view)

        async def toggle_option_off(inter: ApplicationCommandInteraction):
            await inter.response.defer()
            await self.toggle_colour_mode(inter, False)
            toggle_on.disabled = True
            toggle_off.disabled = True
            await inter.edit_original_message(view=view)

        view.children[0].callback = toggle_option_on
        view.children[1].callback = toggle_option_off


def setup(bot) -> None:
    bot.add_cog(Toggle(bot))
