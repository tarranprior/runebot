from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from utils import *

import exceptions

class Price(commands.Cog, name='price'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        global WIKI_URL
        WIKI_URL = self.bot.config['configuration']['wiki_url']
        global HEADERS
        HEADERS = self.bot.config['headers']

    '''
    Price data function. Takes the given search query and returns exchange and value prices.
    Returns custom interface/view components (Real-Time Prices button.)
    
    :param query: (String) - Represents a search query.
    '''
    def price_data(query: str):
        query = search_query(query)
        page_content = parse_page(WIKI_URL, query, HEADERS)
        info = parse_infobox(page_content)
        title = parse_title(page_content)

        try:
            value_price = info['Value']
            exchange_price = info['Exchange']
            buy_limit = info['Buy limit']
            item_id = info['Item ID']
        except KeyError:
            raise exceptions.NoPriceData

        embed, view = EmbedFactory().create(
            title=f'{title} (ID: {item_id})',
            description=f'**Value**: {value_price} • **Exchange Price**: {exchange_price} • **Buy Limit**: {buy_limit}',
            button_label='Real-Time Prices',
            button_url=f'https://prices.runescape.wiki/osrs/item/{item_id}'
        )

        return(embed, view)

    @commands.command(name='price', description='Fetch guide price data from the official Old School RuneScape wikipedia.')
    async def price(self, ctx: Context, *, query: str):
        embed, view = Price.price_data(query)
        await ctx.send(embed=embed, view=view)

    @commands.slash_command(name='price', description='Fetch guide price data from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="Query",
                description="Search for an article.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def price_slash(self, inter: ApplicationCommandInteraction, *, query):
        embed, view = Price.price_data(query)
        await inter.response.send_message(embed=embed, view=view)

def setup(bot) -> None:
    bot.add_cog(Price(bot))