from config import *
from templates.bot import Bot
from utils import *

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Wikipedia(commands.Cog, name='wikipedia'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    General function which takes a search query and returns data from the official OldSchool RuneScape wikipedia.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''

    async def parse_wikipedia_data(self, inter: ApplicationCommandInteraction, query: str) -> None:

        # Checks if the query is equal to the "I'm feeling lucky" special query
        # and returns a random article if True.
        if query == 'I\'m feeling lucky ':
            page_content = parse_page(BASE_URL, FEELING_LUCKY, HEADERS)

        # Autocomplete suggestions all have a space (character) at the end of the query.
        # This determines whether the query is an autocomplete suggestion, and
        # parses the query accordingly.
        elif not query.endswith(' '):
            new_query = replace_spaces(query).lower()
            page_content = parse_page(BASE_URL, new_query, HEADERS)
        else:
            new_query = replace_spaces(query[:-1])
            page_content = parse_page(BASE_URL, new_query, HEADERS)

        attributes = parse_all(page_content, query)
        title = attributes['title']
        description = attributes['description']
        infobox = attributes['infobox']
        options = attributes['options']
        thumbnail_url = attributes['thumbnail_url']

        colour = disnake.Colour.from_rgb(*await extract_colour(self, inter.guild_id, inter.guild.owner_id, thumbnail_url, HEADERS))

        if description:
            embed, view = EmbedFactory().create(title=title, description=description.pop(), colour=colour, infobox=infobox,
                                                thumbnail_url=thumbnail_url, button_url=f'{BASE_URL}{attributes["title"].replace(" ", "_")}')
            if len(embed.description) < 84:
                embed.set_footer(
                    text='To view more information about this page, click the button below.')
            return (embed, view)
        embed, view = EmbedFactory().create(title=title,
                                            description=f'{title} may refer to several articles. Use the dropdown below to select an option.', options=options)
        return (embed, view)

    '''
    Creates a wikipedia slash command which uses the `parse_wikipedia_data` function for user interaction.
    :param self:
    :param inter_1: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''

    @commands.slash_command(
        name='wikipedia',
        description='Search for an article from the official OldSchool RuneScape wikipedia.',
        options=[
            Option(
                name='query',
                description='Search for an article. Start typing for suggestions or hit `I\'m feeling lucky` for a random page!',
                type=OptionType.string,
                required=True)],
    )
    async def wikipedia(self, inter_1: disnake.ApplicationCommandInteraction, *, query: str) -> None:
        await inter_1.response.defer()
        embed_1, view_1 = await self.parse_wikipedia_data(inter_1, query)
        await inter_1.followup.send(embed=embed_1, view=view_1)

        async def select_option_1(inter_2) -> None:
            await inter_2.response.defer()
            embed_2, view_2 = await self.parse_wikipedia_data(inter_2, f'{view_1.children[0].values[0]} ')
            await inter_2.followup.send(embed=embed_2, view=view_2)

            async def select_option_2(inter_3) -> None:
                await inter_3.response.defer()
                embed_3, view_3 = await self.parse_wikipedia_data(inter_3, f'{view_2.children[0].values[0]} ')
                await inter_3.followup.send(embed=embed_3, view=view_3)

            view_2.children[0].callback = select_option_2

        view_1.children[0].callback = select_option_1

    '''
    Creates a basic selection of autocomplete suggestions (from runebot database) once the user begins typing.
    Returns a max. list of 25 suggestions.
    Displays the "I'm feeling lucky" special query in the initial suggestion before typing begins.
    :param self:
    :param query: (String) - Represents a search query.
    '''

    @wikipedia.autocomplete('query')
    async def query_autocomplete(self, query: str):
        autocomplete_suggestions = await get_wikipedia_suggestions(self)
        if len(query) > 0:
            return (
                [f'{a} ' for a in autocomplete_suggestions if query.lower() in a.lower()][:25])
        return (['I\'m feeling lucky '])


def setup(bot) -> None:
    bot.add_cog(Wikipedia(bot))
