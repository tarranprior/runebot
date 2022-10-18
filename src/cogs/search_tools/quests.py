from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *

import exceptions


class Quests(commands.Cog, name='quests'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Quest function. Takes the given search query and returns quest data (if exists.)
    Includes quest summary, properties, requirements, recommendations etc.

    :param query: (String) - Represents a search query.
    '''
    def fetch_quest_data(self, query: str) -> None:
        query = search_query(query)
        page_content = parse_page(BASE_URL, query, HEADERS)
        info = parse_infobox(page_content)
        title = parse_title(page_content)

        try:
            info['Quest series']
            info['Official difficulty']
        except KeyError:
            raise exceptions.NoQuestData

        quest_details = parse_quest_details(page_content)

        embed, view = EmbedFactory().create(
            title=title,
            description=quest_details['Description'],
            colour=disnake.Colour.og_blurple(),
            thumbnail_url=QUEST_ICO,
            button_label='Quick Guide',
            button_url=f"{BASE_URL}{title.replace(' ', '_')}/Quick_guide"
        )

        quest_properties = [
            'Quest series', 'Official difficulty', 'Members'
        ]

        for prop in quest_properties:
            embed.add_field(name=prop, value=info.get(prop), inline=True)

        embed.add_field(name='Start point', value=quest_details['Start point'], inline=False)
        embed.add_field(name='Requirements', value=f"Click [here]({BASE_URL}{title.replace(' ', '_')}#Details) for a full list of requirements.", inline=True)
        embed.add_field(name='Rewards', value=f"Click [here]({BASE_URL}{title.replace(' ', '_')}#Rewards) for a full list of rewards.", inline=True)

        return(embed, view)

    @commands.command(name='quest', description='Fetch quest information from the official Old School RuneScape wikipedia.')
    async def quest(self, ctx: Context, *, query: str) -> None:
        embed, view = self.fetch_quest_data(query.lower())
        await ctx.send(embed=embed, view=view)

    @commands.slash_command(name='quest', description='Fetch quest information from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for a quest.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def quest_slash(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = self.fetch_quest_data(query.lower())
        await inter.followup.send(embed=embed, view=view)

def setup(bot) -> None:
    bot.add_cog(Quests(bot))