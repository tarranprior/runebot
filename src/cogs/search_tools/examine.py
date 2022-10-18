from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *


class Examine(commands.Cog, name='examine'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Examine text function. Takes the given search query and fetches the examine text (if available.)
    :param query: (String) - Represents a search query.
    '''
    def fetch_examine_text(self, query: str) -> None:
        query = search_query(query)
        page_content = parse_page(BASE_URL, query, HEADERS)
        title = parse_title(page_content)
        info = parse_infobox(page_content)
        thumbnail_url = parse_thumbnail(page_content)

        try:
            info['Examine']
        except KeyError:
            raise exceptions.NoExamineText
 
        if info.get('Item ID'):
            embed = EmbedFactory().create(title=f"{title} (ID: {info.get('Item ID')})", description=f"**Examine**: {info.get('Examine')}", thumbnail_url=thumbnail_url)
            return(embed)
        embed = EmbedFactory().create(title=title, description=f"**Examine**: {info.get('Examine')}", thumbnail_url=thumbnail_url)
        return(embed)

    @commands.command(name='examine', description='Fetch the examine text from the official Old School RuneScape wikipedia.')
    async def examine(self, ctx: Context, *, query: str) -> None:
        embed = self.fetch_examine_text(query.lower())
        await ctx.send(embed=embed)

    @commands.slash_command(name='examine', description='Fetch the examine text from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for an item.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def examine_slash(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed = self.fetch_examine_text(query.lower())
        await inter.followup.send(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Examine(bot))