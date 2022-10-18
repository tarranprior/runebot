from ast import parse
from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *

import exceptions


class Minigames(commands.Cog, name='minigames'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Minigame function. Takes the given search query and returns minigame data (if exists.)
    :param query: (String) - Represents a search query.
    '''
    def fetch_minigame_data(self, query: str) -> None:
        query = search_query(query)
        page_content = parse_page(BASE_URL, query, HEADERS)
        title = parse_title(page_content)
        description = parse_description(page_content).pop()
        info = parse_infobox(page_content)
        
        minigames = parse_page(BASE_URL, 'Minigames', HEADERS)
        
        thumbnail_url = parse_minigame_icon(minigames, query)
        if not thumbnail_url:
            thumbnail_url = MINIGAME_ICO

        try:
            info['Type']
        except KeyError:
            raise exceptions.NoMinigameData

        embed, view = EmbedFactory().create(
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            button_label='Visit Page',
            button_url=f'{BASE_URL}{query}'
        )

        minigame_properties = [
            'Released', 'Type', 'Members', 'Location', 'Participants', 'Reward currency', 'Tutorial'
        ]

        for prop in minigame_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)
        embed.add_field(name='Skills', value=info.get('Skills'), inline=False)
        embed.add_field(name='Requirements', value=info.get('Requirements'), inline=False)

        return(embed, view)

    @commands.command(name='minigame', description='Fetch minigame information from the official Old School RuneScape wikipedia.')
    async def minigame(self, ctx: Context, *, query: str) -> None:
        embed, view = self.fetch_minigame_data(query.lower())
        await ctx.send(embed=embed, view=view)
    
    @commands.slash_command(name='minigame', description='Fetch minigame information from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for a minigame.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def minigame_slash(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = self.fetch_minigame_data(query.lower())
        await inter.followup.send(embed=embed, view=view)

def setup(bot) -> None:
    bot.add_cog(Minigames(bot))