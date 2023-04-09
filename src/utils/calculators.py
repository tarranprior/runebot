from math import trunc


'''
Calculator function which calculates the combat level of a player.
:param self:
:param combat_levels: (Dictionary) - Represents the combat levels (Strength, Hitpoints, Magic etc.) of a player.
'''


async def calculate_combat_level(self, combat_levels: dict) -> None:
    base_level = 0.25 * ((combat_levels.get('Defence') + combat_levels.get('Hitpoints')) + trunc(combat_levels.get('Prayer') * 0.5))
    melee_level = ((combat_levels.get('Attack') + combat_levels.get('Strength')) * 0.325)
    range_level = (((trunc((combat_levels.get('Ranged')) / 2) + combat_levels.get('Ranged')) * 0.325))
    magic_level = (((trunc((combat_levels.get('Magic')) / 2) + combat_levels.get('Magic')) * 0.325))
    final_level = base_level + max(melee_level, range_level, magic_level)
    combat_level = trunc(final_level)
    return (combat_level)


'''
Calculator function which calculates the total combat experience of a player.
:param self:
:param combat_levels: (Dictionary) - Represents the combat levels (Strength, Hitpoints, Magic etc.) of a player.
'''


async def calculate_combat_exp(self, combat_skills: list, hiscore_data: dict) -> None:
    combat_experience = 0
    for skill in combat_skills:
        combat_experience += int(hiscore_data.get(skill).split(',')[2])
    return (combat_experience)