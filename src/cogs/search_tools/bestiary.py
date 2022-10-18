from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import ApplicationCommandInteraction, Option, OptionType

from templates.bot import Bot
from config import *
from utils import *

import exceptions


class Monsters(commands.Cog, name='monsters'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Monster function. Takes the given search query and returns monster data (if exists.)
    :param query: (String) - Represents a search query.
    '''
    def fetch_monster_data(self, query: str) -> None:
        query = search_query(query)

        if query == str('random') or query == str("i'm_feeling_lucky"):
            page_content = parse_page(BASE_URL, parse_random_bestiary(BASE_URL, HEADERS), HEADERS)
        else:
            page_content = parse_page(BASE_URL, query, HEADERS)

        info = parse_infobox(page_content)
        title = parse_title(page_content)
        description = parse_description(page_content).pop()

        try:
            info['Combat level']
        except KeyError:
            raise exceptions.NoMonsterData

        embed, view = EmbedFactory().create(
                    title=title,
                    description=description,
                    thumbnail_url=f"https://oldschool.runescape.wiki{info['Image']}",
                    button_label='Visit Page',
                    button_url=f'{BASE_URL}{query}'
        )

        monster_properties = [
            'Aggressive', 'Poison', 'Venom', 'Cannons', 'Thralls', 'Attack style', 'Poisonous', 'Respawn time'
        ]

        embed.add_field(name='Examine', value=info.get('Examine'), inline=False)
        embed.add_field(name='Combat level', value=info.get('Combat level'), inline=True)
        embed.add_field(name='Max hit', value=')\n'.join(info.get('Max hit').split(')')), inline=True)
        
        for prop in monster_properties:
            prop_value = info.get(prop)
            if prop_value != None:
                embed.add_field(name=prop, value=prop_value, inline=True)
            else:
                embed.add_field(name=prop, value='N/A', inline=True)

        embed.add_field(name='Monster ID(s)', value=f"```\n{', '.join(info.get('Monster ID').split(','))}```", inline=False)
        return(embed, view)

    @commands.command(name='bestiary', description='Fetch monster information from the official Old School RuneScape wikipedia.')
    async def monster(self, ctx: Context, *, query: str) -> None:
        embed, view = self.fetch_monster_data(query.lower())
        await ctx.send(embed=embed, view=view)

    @commands.slash_command(name='bestiary', description='Fetch monster information from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for a monster.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def bestiary_slash(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = self.fetch_monster_data(query.lower())
        await inter.followup.send(embed=embed, view=view)

def setup(bot) -> None:
    bot.add_cog(Monsters(bot))