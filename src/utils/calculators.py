#! /usr/bin/env python3

'''
This module contains logic behind combat level and experience
calculation in the context of Runebot.

Functions:
    - `calculate_combat_level()`:
            Calculates the combat level of a player.
    - `calculate_combat_exp()`:
            Calculates the total combat experience of a player.

Each function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from typing import Union
from math import trunc


async def calculate_combat_level(combat_levels: dict) -> int:
    '''
    Calculator function which calculates the combat level of a player.

    :param combat_levels: (Dictionary) -
        Represents a dictionary containing the player's combat levels.

    :return: (Integer) -
        The calculated combat level.
    '''

    attack_level = combat_levels.get('Attack')
    strength_level = combat_levels.get('Strength')
    defence_level = combat_levels.get('Defence')
    hitpoints_level = combat_levels.get('Hitpoints')
    prayer_level = combat_levels.get('Prayer')
    ranged_level = combat_levels.get('Ranged')
    magic_level = combat_levels.get('Magic')

    base_level = 0.25 * ((defence_level + hitpoints_level) + trunc(prayer_level * 0.5))
    melee_level = (attack_level + strength_level) * 0.325
    range_level = ((trunc((ranged_level) / 2) + ranged_level) * 0.325)
    magic_level = ((trunc((magic_level) / 2) + magic_level) * 0.325)

    final_level = base_level + max(melee_level, range_level, magic_level)
    combat_level = trunc(final_level)

    return combat_level


async def calculate_combat_exp(
    combat_skills: list,
    hiscore_data: dict
) -> Union[int, str]:
    '''
    Calculator function which calculates the total combat experience of a player.

    :param combat_skills: (List) -
        Represents the combat levels of a player.
    :param hiscore_data: (Dictionary) -
        Represents hiscore data of a player.

    :return: Union[Integer, String] -
        The total combat experience of the player.
    '''

    combat_experience = 0
    for skill in combat_skills:
        combat_experience += int(hiscore_data.get(skill).split(',')[2])
    if combat_experience == int(-7):
        combat_experience = 'N/A'
    else:
        combat_experience = f'{int(combat_experience):,}'

    return combat_experience
