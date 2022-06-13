from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *

import exceptions

class Price(commands.Cog, name='price'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Price data function. Takes the given search query and returns exchange and value prices.
    Returns custom interface/view components (Real-Time Prices button.)
    
    :param query: (String) - Represents a search query.
    '''
    def price_data(query: str):
        query = search_query(query)
        page_content = parse_page(BASE_URL, query, HEADERS)
        info = parse_infobox(page_content)
        title = parse_title(page_content)

        try:
            value_price = info['Value']
            exchange_price = info['Exchange']
            buy_limit = info['Buy limit']
            item_id = info['Item ID']

        except KeyError:
            raise exceptions.NoPriceData

        api_data = parse_price_data(f'{PRICEAPI_URL}{item_id}', HEADERS)
        graphapi_data = parse_price_data(f'{GRAPHAPI_URL}{item_id}.json', HEADERS)
        generate_graph(graphapi_data)

        embed, view = EmbedFactory().create(
            title=f'{title} (ID: {item_id})',
            description=api_data['item']['description'],
            thumbnail_url=api_data['item']['icon_large'],
            button_label='Real-Time Prices',
            button_url=f'https://prices.runescape.wiki/osrs/item/{item_id}'
        )
        embed.add_field(name='Current Value', value=value_price, inline=True)
        embed.add_field(name='Exchange Price', value=exchange_price, inline=True)
        embed.add_field(name='Buy Limit', value=buy_limit, inline=True)

        embed.add_field(name='Today', value=f"{api_data['item']['today']['price']} coins ({api_data['item']['today']['trend'].title()})", inline=False)

        embed.add_field(name='30 Days', value=f"{api_data['item']['day30']['change']}", inline=True)
        embed.add_field(name='90 Days', value=f"{api_data['item']['day90']['change']}", inline=True)
        embed.add_field(name='180 Days', value=f"{api_data['item']['day180']['change']}", inline=True)

        file = disnake.File('assets/apigraph.png', filename='apigraph.png')
        embed.set_image(url='attachment://apigraph.png')
        return(embed, view, file)

    @commands.command(name='price', description='Fetch guide price data from the official Old School RuneScape wikipedia.')
    async def price(self, ctx: Context, *, query: str):
        embed, view, file = Price.price_data(query)
        await ctx.send(embed=embed, view=view, file=file)

    @commands.slash_command(name='price', description='Fetch guide price data from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for an item.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def price_slash(self, inter: ApplicationCommandInteraction, *, query):
        inter.response.defer
        embed, view, file = Price.price_data(query)
        await inter.response.send_message(embed=embed, view=view, file=file)
        file.close()

def setup(bot) -> None:
    bot.add_cog(Price(bot))