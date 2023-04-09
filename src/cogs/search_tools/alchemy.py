from templates.bot import Bot
from config import *
from utils import *

import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Alchemy(commands.Cog, name='alchemy'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    '''
    General function which takes a search query and returns alchemy data from the official OldSchool RuneScape wikipedia.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''

    async def parse_alchemy_data(self, inter: ApplicationCommandInteraction, query: str) -> None:
        # Checks if the query is equal to the "I'm feeling lucky" special query
        # and returns a random article if True.
        if query == 'I\'m feeling lucky ':
            page_content = parse_page(BASE_URL, replace_spaces(random.choice(await get_suggestions(self, ['Tradeable items']))), HEADERS)

        # Autocomplete suggestions all have a space (character) at the end of the query.
        # This determines whether the query is an autocomplete suggestion, and
        # parses the query accordingly.
        elif not query.endswith(' '):
            query = replace_spaces(query).lower()
            page_content = parse_page(BASE_URL, query, HEADERS)
        else:
            query = replace_spaces(query[:-1])
            page_content = parse_page(BASE_URL, query, HEADERS)

        title = parse_title(page_content)
        info = parse_infobox(page_content)
        thumbnail_url = parse_thumbnail(page_content)
        colour = disnake.Colour.from_rgb(*await extract_colour(self, inter.guild_id, inter.guild.owner_id, thumbnail_url, HEADERS))

        try:
            info['Low alch']
            info['High alch']
        except KeyError:
            raise exceptions.NoAlchemyData

        embed = EmbedFactory().create(
            title=f'{title} (ID: {info.get("Item ID")})',
            description=info.get('Examine'),
            thumbnail_url=thumbnail_url,
            colour=colour)
        alch_properties = [
            'Value',
            'Exchange',
            'Buy limit',
            'High alch',
            'Low alch']

        for prop in alch_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)

        try:
            # Calculating the profit margin.
            price_data = parse_price_data(
                f'{WIKIAPI_URL}{info["Item ID"]}', HEADERS, query)
            high_price = price_data['data'][info['Item ID']]['high']
            # Fetches latest price of Nature Runes
            nature_data = parse_price_data(f'{WIKIAPI_URL}561', HEADERS, query)
            nature_price = nature_data['data']['561']['high']
            def operator(i): return (
                '+' if int(i.replace(',', '')) >= 0 else '') + str(i)
            profit_margin = operator(
                f'{int(info.get("High alch").replace(" coins", "").replace(" coin", "").replace(",", "")) +- high_price +- nature_price:,}')
            embed.add_field(
                name='Margin',
                value=str(profit_margin),
                inline=True)
        except KeyError:
            embed.add_field(name='Margin', value='None', inline=True)

        return (embed)


    '''
    Creates an alchemy slash command which uses the `parse_alchemy_data` function for user interaction.
    :param self:
    :param inter_1: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''
    @commands.slash_command(
        name='alchemy',
        description='Fetch alchemy data from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='query',
                description='Search for an item.',
                type=OptionType.string,
                required=True)])
    async def alchemy(self, inter: ApplicationCommandInteraction, *, query: str) -> None:
        await inter.response.defer()
        embed = await self.parse_alchemy_data(inter, query)
        await inter.followup.send(embed=embed)


    '''
    Creates a basic selection of autocomplete suggestions (from runebot database) once the user begins typing.
    Returns a max. list of 25 suggestions.
    Displays the "I'm feeling lucky" special query in the initial suggestion before typing begins.
    :param self:
    :param query: (String) - Represents a search query.
    '''
    @alchemy.autocomplete('query')
    async def query_autocomplete(self, query: str):
        autocomplete_suggestions = await get_suggestions(self, ['Tradeable items'])
        if len(query) > 0:
            return (
                [f'{a} ' for a in autocomplete_suggestions if query.lower() in a.lower()][:25])
        return (['I\'m feeling lucky '])


def setup(bot) -> None:
    bot.add_cog(Alchemy(bot))
