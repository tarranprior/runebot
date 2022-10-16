from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *


class Alch(commands.Cog, name='alch'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Fetch alch data. Takes the given search query and returns low alch and high alch prices, thumbnail etc.
    :param query: (String) - Represents a search query.
    '''
    def fetch_alch_data(self, query: str) -> None:
        query = search_query(query)
        page_content = parse_page(BASE_URL, query, HEADERS)
        title = parse_title(page_content)
        info = parse_infobox(page_content)
        thumbnail_url = parse_thumbnail(page_content)

        try:
            value = info['Value']
            low_alch = info['Low alch']
            high_alch = info['High alch']
            item_id = info['Item ID']
        except KeyError:
            raise exceptions.NoAlchData
        
        embed = EmbedFactory().create(
            title=f'{title} (ID: {item_id})',
            thumbnail_url=thumbnail_url
        )
        embed.add_field(name='Value', value=value, inline=True)
        embed.add_field(name='High alch', value=high_alch, inline=True)
        embed.add_field(name='Low alch', value=low_alch, inline=True)
        return(embed)

    @commands.command(name='alch', description='Fetch alchemy price data from the official Old School RuneScape wikipedia.')
    async def alch(self, ctx: Context, *, query: str) -> None:
        embed = self.fetch_alch_data(query.lower())
        await ctx.send(embed=embed)
    
    @commands.slash_command(name='alch', description='Fetch alchemy price data from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for an article.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def alch_slash(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed = self.fetch_alch_data(query.lower())
        await inter.followup.send(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Alch(bot))