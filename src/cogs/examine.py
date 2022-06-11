from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from utils import *

class Examine(commands.Cog, name='examine'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

        global WIKI_URL
        WIKI_URL = self.bot.config['configuration']['wiki_url']
        global HEADERS
        HEADERS = self.bot.config['headers']

    '''
    Examine text function. Takes the given search query and fetches the examine text (if available.)
    :param query: (String) - Represents a search query.
    '''
    def examine_text(query: str):
        query = search_query(query)
        page_content = parse_page(WIKI_URL, query, HEADERS)
        
        title = parse_title(page_content)
        info = parse_infobox(page_content)
        thumbnail_url = parse_thumbnail(page_content)

        try:
            item_id = info['Item ID']
            examine_text = info['Examine']
        except KeyError:
            raise exceptions.NoExamineText

        embed = EmbedFactory().create(title=f'{title} (ID: {item_id})', description=f'**Examine**: {examine_text}', thumbnail_url=thumbnail_url)
        return(embed)

    @commands.command(name='examine', description='Fetch the examine text from the official Old School RuneScape wikipedia.')
    async def examine(self, ctx: Context, *, query: str):
        embed = Examine.examine_text(query)
        await ctx.send(embed=embed)

    @commands.slash_command(name='examine', description='Fetch the examine text from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="Query",
                description="Search for an item.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def examine_slash(self, inter: ApplicationCommandInteraction, *, query):
        embed = Examine.examine_text(query)
        await inter.response.send_message(embed=embed)

def setup(bot) -> None:
    bot.add_cog(Examine(bot))