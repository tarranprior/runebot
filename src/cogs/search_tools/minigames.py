import exceptions
from config import *
from templates.bot import Bot
from utils import *

import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Minigames(commands.Cog, name='minigames'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    '''
    General function which takes the given search query and returns corresponding minigame data.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    async def parse_minigame_data(self, inter: ApplicationCommandInteraction, query: str) -> None:

        # Checks if the query is equal to the "I'm feeling lucky" special query
        # and returns a random quest if True.
        if query == 'I\'m feeling lucky ':
            new_query = replace_spaces(random.choice(await get_suggestions(self, ['Minigames'])))
            page_content = parse_page(BASE_URL, new_query, HEADERS)

        # Autocomplete suggestions all have a space (character) at the end of the query.
        # This determines whether the query is an autocomplete suggestion, and
        # parses the query accordingly.
        elif not query.endswith(' '):
            new_query = replace_spaces(query).lower()
            page_content = parse_page(BASE_URL, new_query, HEADERS)
        else:
            new_query = replace_spaces(query[:-1])
            page_content = parse_page(BASE_URL, new_query, HEADERS)

        title = parse_title(page_content)
        description = parse_description(page_content, query).pop()
        info = parse_infobox(page_content)
        minigames = parse_page(BASE_URL, 'Minigames', HEADERS)

        thumbnail_url = parse_minigame_icon(minigames, new_query)
        if not thumbnail_url:
            thumbnail_url = MINIGAME_ICO
            colour = 0xC24E46
        else:
            colour = disnake.Colour.from_rgb(*await extract_colour(self, inter.guild_id, inter.guild.owner_id, thumbnail_url, HEADERS))

        try:
            info['Type']
        except KeyError:
            raise exceptions.NoMinigameData(query)

        embed, view = EmbedFactory().create(
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            colour=colour,
            button_label='Visit Page',
            button_url=f'{BASE_URL}{new_query}'
        )

        minigame_properties = [
            'Released',
            'Type',
            'Members',
            'Location',
            'Participants',
            'Reward currency',
            'Tutorial']

        for prop in minigame_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)
        embed.add_field(name='Skills', value=info.get('Skills'), inline=False)
        embed.add_field(
            name='Requirements',
            value=info.get('Requirements'),
            inline=False)
        return (embed, view)


    '''
    Creates the minigame slash command for user interaction.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    @commands.slash_command(
        name='minigames',
        description='Fetch minigame information from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='query',
                description='Search for a minigame.',
                type=OptionType.string,
                required=True)])
    async def minigames(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = await self.parse_minigame_data(inter, query)
        await inter.followup.send(embed=embed, view=view)


    '''
    Creates a basic selection of autocomplete suggestions (from runebot database) once the user begins typing.
    Returns a max. list of 25 item suggestions.
    :param self:
    :param query: (String) - Represents a search query.
    '''


    @minigames.autocomplete('query')
    async def query_autocomplete(self, query: str):
        autocomplete_suggestions = await get_suggestions(self, ['Minigames'])
        if len(query) > 0:
            return (
                [f'{a} ' for a in autocomplete_suggestions if query.lower() in a.lower()][:25])
        return (['I\'m feeling lucky '])


def setup(bot) -> None:
    bot.add_cog(Minigames(bot))
