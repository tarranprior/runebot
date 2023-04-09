from templates.bot import Bot
from config import *
from utils import *

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType


class Stats(commands.Cog, name='stats'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot


    '''
    General function which takes a username and returns hiscore values from the official API in a structured format.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param game_mode: (String) - Represents a specified game mode (Ex: Ironman, 1 Defence etc.)
    :param username: (String) - Represents a player's username.
    '''


    async def parse_hiscores(self, inter: ApplicationCommandInteraction, game_mode: str, username: str) -> None:
        if len(username) > 12:
            raise exceptions.UsernameInvalid

        if type(game_mode) == type(None):
            game_mode = 'Regular Mode'
            try:
                hiscore_data = parse_hiscores(GAME_MODE_URLS.get(game_mode), HEADERS, HISCORES_ORDER, [username])
            except IndexError:
                raise exceptions.NoHiscoreData

        else:
            try:
                hiscore_data = parse_hiscores(GAME_MODE_URLS.get(game_mode), HEADERS, HISCORES_ORDER, [username])
            except IndexError:
                # Check whether the username exists on the regualr Hiscores before throwing Game Mode error.
                try:
                    hiscore_data = parse_hiscores(HISCORES_API_REGULAR, HEADERS, HISCORES_ORDER, [username])
                except IndexError:
                    raise exceptions.NoHiscoreData
                raise exceptions.NoGameModeData

        combat_levels = {}
        for skill in COMBAT_SKILLS:
            combat_levels.update({skill: int(hiscore_data.get(skill).split(',')[1])})

        if int(hiscore_data.get('Hitpoints').split(',')[1]) < 10:
            hiscore_data.update({'Hitpoints': f'{hiscore_data.get("Hitpoints").split(",")[0]},{int(10)},{hiscore_data.get("Hitpoints").split(",")[2]}'})
            combat_levels.update({'Hitpoints': int(10)})

        combat_level = await calculate_combat_level(self, combat_levels)
        combat_experience = await calculate_combat_exp(self, COMBAT_SKILLS, hiscore_data)

        if combat_experience == int(-7):
            combat_experience = 'N/A'
        else:
            combat_experience = f'{int(combat_experience):,}'

        overall_rank = f'{int(hiscore_data.get("Overall").split(",")[0]):,}'
        if overall_rank == '-1':
            overall_rank = 'N/A'

        overall_exp = f'{int(hiscore_data.get("Overall").split(",")[2]):,}'
        if overall_exp == '0':
            overall_exp = 'N/A'

        skills_column_one = f'''
            {SKILL_EMOTES.get('attack')} {hiscore_data.get('Attack').split(',')[1]}
            {SKILL_EMOTES.get('strength')} {hiscore_data.get('Strength').split(',')[1]}
            {SKILL_EMOTES.get('defence')} {hiscore_data.get('Defence').split(',')[1]}
            {SKILL_EMOTES.get('ranged')} {hiscore_data.get('Ranged').split(',')[1]}
            {SKILL_EMOTES.get('prayer')} {hiscore_data.get('Prayer').split(',')[1]}
            {SKILL_EMOTES.get('magic')} {hiscore_data.get('Magic').split(',')[1]}
            {SKILL_EMOTES.get('runecraft')} {hiscore_data.get('Runecraft').split(',')[1]}
            {SKILL_EMOTES.get('construction')} {hiscore_data.get('Construction').split(',')[1]}\n\u200b\n
        '''
        skills_column_two = f'''
            {SKILL_EMOTES.get('hitpoints')} {hiscore_data.get('Hitpoints').split(',')[1]}
            {SKILL_EMOTES.get('agility')} {hiscore_data.get('Agility').split(',')[1]}
            {SKILL_EMOTES.get('herblore')} {hiscore_data.get('Herblore').split(',')[1]}
            {SKILL_EMOTES.get('thieving')} {hiscore_data.get('Thieving').split(',')[1]}
            {SKILL_EMOTES.get('crafting')} {hiscore_data.get('Crafting').split(',')[1]}
            {SKILL_EMOTES.get('fletching')} {hiscore_data.get('Fletching').split(',')[1]}
            {SKILL_EMOTES.get('slayer')} {hiscore_data.get('Slayer').split(',')[1]}
            {SKILL_EMOTES.get('hunter')} {hiscore_data.get('Hunter').split(',')[1]}\n\u200b\n
        '''
        skills_column_three = f'''
            {SKILL_EMOTES.get('mining')} {hiscore_data.get('Mining').split(',')[1]}
            {SKILL_EMOTES.get('smithing')} {hiscore_data.get('Smithing').split(',')[1]}
            {SKILL_EMOTES.get('fishing')} {hiscore_data.get('Fishing').split(',')[1]}
            {SKILL_EMOTES.get('cooking')} {hiscore_data.get('Cooking').split(',')[1]}
            {SKILL_EMOTES.get('firemaking')} {hiscore_data.get('Firemaking').split(',')[1]}
            {SKILL_EMOTES.get('woodcutting')} {hiscore_data.get('Woodcutting').split(',')[1]}
            {SKILL_EMOTES.get('farming')} {hiscore_data.get('Farming').split(',')[1]}
            {SKILL_EMOTES.get('overall')} {hiscore_data.get('Overall').split(',')[1]}\n\u200b\n
        '''

        embed = EmbedFactory().create(
            description=f'Personal Hiscores for **{username}**\n({game_mode})\n\u200b\n'
        )

        embed.add_field(name='\u200a', value=skills_column_one, inline=True)
        embed.add_field(name='\u200a', value=skills_column_two, inline=True)
        embed.add_field(name='\u200a', value=skills_column_three, inline=True)

        embed.add_field(
            name=f'{SKILL_EMOTES.get("overall")} Overall',
            value=f'''
                **Rank**: {overall_rank}
                **XP**: {overall_exp}
            '''
        )

        embed.add_field(
            name=f'{SKILL_EMOTES.get("combat")} Combat',
            value=f'''
                **Level**: {combat_level}
                **XP**: {combat_experience}
            '''    
        )

        embed.set_footer(text='Experience data from the official Hiscores API.')
        return (embed)


    '''
    Creates a stats slash command which uses the `parse_hiscores` function for user interaction.
    :param self:
    :param inter: (ApplicationCommandInteraction) - Represents an interaction with an application command.
    :param game_mode: (String) - Represents a specified game mode (Ex: Ironman, 1 Defence etc.)
    :param username: (String) - Represents a player's username.
    '''


    @commands.slash_command(
        name='stats',
        description='Fetch player stats from the official Hiscores.',
        options=[
            Option(
                name='username',
                description='Search for a Player.',
                type=OptionType.string,
                required=True),
            Option(
                name='game_mode',
                description='Select a Game Mode.',
                type=OptionType.string,
                required=False)
            ])

    async def stats(self, inter: ApplicationCommandInteraction, game_mode = None, *, username: str) -> None:
        embed = await self.parse_hiscores(inter, game_mode, username)
        await inter.response.send_message(embed=embed)


    '''
    Creates a selection of autocomplete suggestions for the 'game-mode' option.
    :param self:
    :param game_mode: (String) - Represents a specified game mode (Ex: Ironman, 1 Defence etc.)
    '''


    @stats.autocomplete('game_mode')
    async def game_mode_autocomplete(self, game_mode: str):
        return (['Ironman', 'Hardcore Ironman', 'Ultimate Ironman', 'Skiller', '1 Defence', 'Fresh Start Worlds'])


def setup(bot) -> None:
    bot.add_cog(Stats(bot))
