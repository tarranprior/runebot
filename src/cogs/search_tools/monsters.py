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
        page_content = parse_page(BASE_URL, query, HEADERS)
        info = parse_infobox(page_content)
        title = parse_title(page_content)
        description = parse_description(page_content).pop()

        try:
            combat_level = info['Combat level']
            size = info['Size']
            examine_text = info['Examine']
            max_hit = info['Max hit']
            aggressive = info['Aggressive']
            poisonous = info['Poisonous']
            attack_style = info['Attack style']
            poison = info['Poison']
            venom = info['Venom']
            cannons = info['Cannons']
            thralls = info['Thralls']
        except KeyError:
            raise exceptions.NoMonsterData

        embed, view = EmbedFactory().create(
            title=title,
            description=description,
            thumbnail_url=f"https://oldschool.runescape.wiki{info['Image']}",
            button_label='Visit Page',
            button_url=f'{BASE_URL}{query}'
        )

        embed.add_field(name='Examine', value=examine_text, inline=False)

        embed.add_field(name='Combat level', value=combat_level, inline=True)
        embed.add_field(name='Max hit', value=')\n'.join(max_hit.split(')')), inline=True)
        embed.add_field(name='Aggressive', value=aggressive, inline=True)
        
        embed.add_field(name='Poison', value=poison, inline=True)
        embed.add_field(name='Venom', value=venom, inline=True)
        embed.add_field(name='Cannons', value=cannons, inline=True)
        embed.add_field(name='Thralls', value=thralls, inline=True)

        embed.add_field(name='Attack style', value=attack_style, inline=True)
        embed.add_field(name='Poisonous', value=poisonous, inline=True)

        try:
            respawn_time = info['Respawn time']
            embed.add_field(name='Respawn time', value=respawn_time, inline=True)
        except KeyError:
            pass
        try:
            monster_id = info['Monster ID']
            embed.add_field(name='Monster ID(s)', value=f"```\n{', '.join(monster_id.split(','))}```", inline=False)
        except KeyError:
            pass

        return(embed, view)

    @commands.command(name='monster', description='Fetch monster information from the official Old School RuneScape wikipedia.')
    async def monster(self, ctx: Context, *, query: str) -> None:
        embed, view = self.fetch_monster_data(query.lower())
        await ctx.send(embed=embed, view=view)
    
    @commands.slash_command(name='monster', description='Fetch monster information from the official Old School RuneScape wikipedia.', options=[
            Option(
                name="query",
                description="Search for a monster.",
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def monster_slash(self, inter: ApplicationCommandInteraction, *, query) -> None:
        await inter.response.defer()
        embed, view = self.fetch_monster_data(query.lower())
        await inter.follow.send(embed=embed, view=view)

def setup(bot) -> None:
    bot.add_cog(Monsters(bot))