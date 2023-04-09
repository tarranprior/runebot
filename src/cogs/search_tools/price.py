from config import *
from templates.bot import Bot
from utils import *

import datetime
import random

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Price(commands.Cog, name='price'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    '''
    General function which takes the given search query and returns exchange and value prices.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    async def parse_price_data(self, inter: ApplicationCommandInteraction, query: str) -> None:

        # Checks if the query is equal to the "I'm feeling lucky" special query
        # and returns a random item if True.
        if query == 'I\'m feeling lucky ':
            tradeable_items = await get_suggestions(self, ['Tradeable items'])
            page_content = parse_page(BASE_URL, replace_spaces(random.choice([i for i in tradeable_items if not any(w in i for w in BLACKLIST_ITEMS)])), HEADERS)

        # Autocomplete suggestions all have a space (character) at the end of the query.
        # This determines whether the query is an autocomplete suggestion, and
        # parses the query accordingly.
        elif not query.endswith(' '):
            query = replace_spaces(query).lower()
            page_content = parse_page(BASE_URL, query, HEADERS)
        else:
            query = replace_spaces(query[:-1])
            page_content = parse_page(BASE_URL, query, HEADERS)

        info = parse_infobox(page_content)
        title = parse_title(page_content)

        try:
            info['Value']
            info['Exchange']
            info['Buy limit']
        except KeyError:
            raise exceptions.NoPriceData

        api_data = parse_price_data(
            f"{PRICEAPI_URL}{info['Item ID']}", HEADERS, query)
        graphapi_data = parse_price_data(
            f"{GRAPHAPI_URL}{info['Item ID']}.json", HEADERS, query)
        filename = await generate_graph(graphapi_data)

        thumbnail_url = api_data['item']['icon_large']
        colour = disnake.Colour.from_rgb(*await extract_colour(self, inter.guild_id, inter.guild.owner_id, thumbnail_url, HEADERS))

        embed, view = EmbedFactory().create(
            title=f"{title} (ID: {info['Item ID']})",
            description=api_data['item']['description'],
            thumbnail_url=thumbnail_url,
            colour=colour,
            button_label='Real-Time Prices',
            button_url=f'https://prices.runescape.wiki/osrs/item/{info["Item ID"]}'
        )

        # Creates a button which redirects to the corresponding GE Tracker
        # (https://ge-tracker.com) page.
        ge_tracker = create_link_button(
            'GE Tracker', f'https://ge-tracker.com/item/{info["Item ID"]}')
        view.add_item(ge_tracker)
        # Creates a button which redirects to the corresponding OSRS Exchange
        # page.
        osrs_exchange = create_link_button(
            'OSRS Exchange',
            f'https://secure.runescape.com/m=itemdb_oldschool/Watermelon/viewitem?obj={info["Item ID"]}')
        view.add_item(osrs_exchange)

        price_properties = ['Value', 'Exchange', 'Buy limit']
        for prop in price_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)

        try:

            # Calculating the profit margin.
            price_data = parse_price_data(
                f'{WIKIAPI_URL}{info["Item ID"]}', HEADERS, query)
            high_price = price_data['data'][info['Item ID']]['high']
            low_price = price_data['data'][info['Item ID']]['low']
            # Insert a + or - depending on positive or negative profit.
            def operator(i): return (
                '+' if int(i.replace(',', '')) >= 0 else '') + str(i)
            profit_margin = operator(f'{low_price +- high_price:,}')
            try:
                # Represents buy limit * profit margin.
                potential_profit = operator(
                    f'{int(info.get("Buy limit").replace(",", "")) * (int(low_price) +- int(high_price)):,}')
            except ValueError:
                # Sets the potential profit to profit margin if buy limit is
                # currently unknown.
                potential_profit = operator(
                    f'{int(profit_margin.replace("-", "").replace("+", "").replace(",", ""))}')

            # Gets the last trade date/time.
            high_time = datetime.datetime.fromtimestamp(
                price_data['data'][info['Item ID']]['highTime'])
            low_time = datetime.datetime.fromtimestamp(
                price_data['data'][info['Item ID']]['lowTime'])
            present_time = datetime.datetime.now().replace(microsecond=0)
            high_date_diff = convert_date_to_duration(present_time, high_time)
            low_date_diff = convert_date_to_duration(present_time, low_time)

        except KeyError:
            raise exceptions.NoPriceData

        embed.add_field(
            name='Buy price',
            value=f'{high_price:,} coins\n`{high_date_diff}`',
            inline=True)
        embed.add_field(
            name='Sell price',
            value=f'{low_price:,} coins\n`{low_date_diff}`',
            inline=True)
        embed.add_field(
            name='Margin',
            value=f'{profit_margin}\n(`{potential_profit}`)',
            inline=True)

        embed.add_field(
            name='Today',
            value=f'{api_data["item"]["today"]["price"]} coins ({api_data["item"]["today"]["trend"].title()})'.replace(
                '- ',
                '-'),
            inline=False)
        embed.add_field(
            name='30 Days',
            value=f'{api_data["item"]["day30"]["change"]}',
            inline=True)
        embed.add_field(
            name='90 Days',
            value=f'{api_data["item"]["day90"]["change"]}',
            inline=True)
        embed.add_field(
            name='180 Days',
            value=f'{api_data["item"]["day180"]["change"]}',
            inline=True)
        embed.set_footer(
            text='Exchange data from OSRS Exchange. For more analytics, use the buttons below.')
        return (embed, view, filename)


    '''
    Creates the price slash command for user interaction.
    :param self:
    :param inter_1: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param query: (String) - Represents a search query.
    '''


    @commands.slash_command(
        name='price',
        description='Fetch guide price data from the official Old School RuneScape wikipedia.',
        options=[
            Option(
                name='query',
                description='Search for an item.',
                type=OptionType.string,
                required=True)])
    async def price(self, inter: ApplicationCommandInteraction, *, query: str) -> None:
        await inter.response.defer()
        embed, view, filename = await self.parse_price_data(inter, query)
        file = disnake.File(f'assets/{filename}', filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        await inter.followup.send(embed=embed, view=view, file=file)
        file.close()
        os.remove(f'assets/{filename}')


    '''
    Creates a basic selection of autocomplete suggestions (from runebot database) once the user begins typing.
    Returns a max. list of 25 item suggestions.
    :param self:
    :param query: (String) - Represents a search query.
    '''


    @price.autocomplete('query')
    async def query_autocomplete(self, query: str):
        tradeable_items = await get_suggestions(self, ['Tradeable items'])
        autocomplete_suggestions = [i for i in tradeable_items if not any(w in i for w in BLACKLIST_ITEMS)]
        if len(query) > 0:
            return (
                [f'{a} ' for a in autocomplete_suggestions if query.lower() in a.lower()][:25])
        return (['I\'m feeling lucky '])


def setup(bot) -> None:
    bot.add_cog(Price(bot))
