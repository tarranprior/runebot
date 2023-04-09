import exceptions
from config import *
from templates.bot import Bot
from utils import *

import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Bestiary(commands.Cog, name='bestiary'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    '''
    General function which takes the given search query and returns corresponding monster data.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    async def parse_monster_data(self, inter: ApplicationCommandInteraction, query: str) -> None:

        # Checks if the query is equal to the "I'm feeling lucky" special query
        # and returns a random quest if True.
        if query == 'I\'m feeling lucky ':
            new_query = replace_spaces(random.choice(await get_suggestions(self, ['Monsters'])))
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

        info = parse_infobox(page_content)
        title = parse_title(page_content)
        description = parse_description(page_content, new_query).pop()

        try:
            info['Combat level']
        except KeyError:
            raise exceptions.NoMonsterData(query)

        embed, view = EmbedFactory().create(
            title=title,
            description=description,
            thumbnail_url=f'https://oldschool.runescape.wiki{info["Image"]}',
            button_label='Visit Page',
            button_url=f'{BASE_URL}{new_query}'
        )

        try:
            colour = disnake.Colour.from_rgb(*await extract_colour(self, inter.guild_id, inter.guild.owner_id, f'https://oldschool.runescape.wiki{info["Image"]}', HEADERS))
            embed.colour = colour
        except KeyError:
            pass

        monster_properties = [
            'Aggressive',
            'Poison',
            'Venom',
            'Cannons',
            'Thralls',
            'Attack style',
            'Poisonous',
            'Respawn time']

        embed.add_field(
            name='Examine',
            value=info.get('Examine'),
            inline=False)
        embed.add_field(
            name='Combat level',
            value=info.get('Combat level'),
            inline=True)
        embed.add_field(
            name='Max hit',
            value=')\n'.join(
                info.get('Max hit').split(')')),
            inline=True)

        for prop in monster_properties:
            prop_value = info.get(prop)
            if prop_value is not None:
                embed.add_field(name=prop, value=prop_value, inline=True)
            else:
                embed.add_field(name=prop, value='N/A', inline=True)

        embed.add_field(
            name='Monster ID(s)',
            value=f'```\n{", ".join(info.get("Monster ID").split(","))}```',
            inline=False)
        return (embed, view)


    '''
    Creates the bestiary slash command for user interaction.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    @commands.slash_command(
        name='bestiary',
        description='Fetch monster information from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='query',
                description='Search for a monster.',
                type=OptionType.string,
                required=True)])
    async def bestiary(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = await self.parse_monster_data(inter, query)
        await inter.followup.send(embed=embed, view=view)


    '''
    Creates a basic selection of autocomplete suggestions (from runebot database) once the user begins typing.
    Returns a max. list of 25 item suggestions.
    :param self:
    :param query: (String) - Represents a search query.
    '''


    @bestiary.autocomplete('query')
    async def query_autocomplete(self, query: str):
        autocomplete_suggestions = await get_suggestions(self, ['Monsters'])
        if len(query) > 0:
            return (
                [f'{a} ' for a in autocomplete_suggestions if query.lower() in a.lower()][:25])
        return (['I\'m feeling lucky '])


def setup(bot) -> None:
    bot.add_cog(Bestiary(bot))
