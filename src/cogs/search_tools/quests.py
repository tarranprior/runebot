import exceptions
from config import *
from templates.bot import Bot
from utils import *

import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Quests(commands.Cog, name='quests'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    '''
    General function which takes the given search query and returns corresponding quest data.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    async def parse_quest_data(self, inter: ApplicationCommandInteraction, query: str) -> None:

        # Checks if the query is equal to the "I'm feeling lucky" special query
        # and returns a random quest if True.
        if query == 'I\'m feeling lucky ':
            page_content = parse_page(BASE_URL, replace_spaces(random.choice(await get_suggestions(self, ['Quests']))), HEADERS)

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

        try:
            info['Quest series']
            info['Official difficulty']
        except KeyError:
            raise exceptions.NoQuestData(query)

        quest_details = parse_quest_details(page_content)

        embed, view = EmbedFactory().create(
            title=title,
            description=quest_details['Description'],
            colour=disnake.Colour.og_blurple(),
            thumbnail_url=QUEST_ICO,
            button_label='Quick Guide',
            button_url=f'{BASE_URL}{title.replace(" ", "_")}/Quick_guide'
        )

        quest_properties = [
            'Quest series', 'Official difficulty', 'Members'
        ]

        for prop in quest_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)

        embed.add_field(
            name='Start point',
            value=quest_details['Start point'],
            inline=False)
        embed.add_field(
            name='Requirements',
            value=f'Click [here]({BASE_URL}{title.replace(" ", "_")}#Details) for a full list of requirements.',
            inline=True)
        embed.add_field(
            name='Rewards',
            value=f'Click [here]({BASE_URL}{title.replace(" ", "_")}#Rewards) for a full list of rewards.',
            inline=True)
        return (embed, view)


    '''
    Creates the quest slash command for user interaction.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    @commands.slash_command(
        name='quests',
        description='Fetch quest information from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='query',
                description='Search for a quest.',
                type=OptionType.string,
                required=True)])
    async def quests(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = await self.parse_quest_data(inter, query)
        await inter.followup.send(embed=embed, view=view)


    '''
    Creates a basic selection of autocomplete suggestions (from runebot database) once the user begins typing.
    Returns a max. list of 25 item suggestions.
    :param self:
    :param query: (String) - Represents a search query.
    '''


    @quests.autocomplete('query')
    async def query_autocomplete(self, query: str):
        autocomplete_suggestions = await get_suggestions(self, ['Quests'])
        if len(query) > 0:
            return (
                [f'{a} ' for a in autocomplete_suggestions if query.lower() in a.lower()][:25])
        return (['I\'m feeling lucky '])


def setup(bot) -> None:
    bot.add_cog(Quests(bot))
