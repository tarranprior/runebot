from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from utils import *

class Alch(commands.Cog, name='alch'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        global WIKI_URL
        WIKI_URL = self.bot.config['configuration']['wiki_url']
        global HEADERS
        HEADERS = self.bot.config['headers']

    '''
    Alch data function. Takes the given search query and returns low alch and high alch price data.
    :param query: (String) - Represents a search query.
    '''
    def alch_data(query: str):
        query = search_query(query)
        page_content = parse_page(WIKI_URL, query, HEADERS)

        title = parse_title(page_content)
        info = parse_infobox(page_content)

        try:
            value = info['Value']
            low_alch = info['Low alch']
            high_alch = info['High alch']
            item_id = info['Item ID']
        except KeyError:
            raise exceptions.NoAlchData

        embed = EmbedFactory().create(
            title=f'{title} ({item_id})',
            description=f'**Value**: {value} • **Low Alch**: {low_alch} • **High Alch**: {high_alch}'
        )

        return(embed)

    @commands.command(name='alch', description='Fetches alch price data from the official Old School RuneScape wikipedia.')
    async def alch(self, ctx: Context, *, query: str):
        embed = Alch.alch_data(query)
        await ctx.send(embed=embed)
    
    @commands.slash_command(name='alch', description='Fetches alch price data from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="Query",
                description="Search for an article.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def alch_slash(self, inter: ApplicationCommandInteraction, *, query):
        embed = Alch.alch_data(query)
        await inter.response.send_message(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Alch(bot))