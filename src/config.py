from utils.helpers import configuration


# URLs
BASE_URL = configuration()['urls']['osrswiki_url']
WIKIAPI_URL = configuration()['urls']['priceapi_wikipedia']
PRICEAPI_URL = configuration()['urls']['priceapi_official']
GRAPHAPI_URL = configuration()['urls']['graphapi_official']

# HISCORE URLs
HISCORES_API_REGULAR = configuration()['urls']['hiscores_api_regular']
HISCORES_API_IRONMAN = configuration()['urls']['hiscores_api_ironman']
HISCORES_API_HARDCORE_IRONMAN = configuration()['urls']['hiscores_api_hardcore_ironman']
HISCORES_API_ULTIMATE = configuration()['urls']['hiscores_api_ultimate']
HISCORES_API_SKILLER = configuration()['urls']['hiscores_api_skiller']
HISCORES_API_SKILLER_DEFENCE = configuration()['urls']['hiscores_api_skiller_defence']
HISCORES_API_FRESH_START = configuration()['urls']['hiscores_api_fresh_start']

# HEADERS
HEADERS = configuration()['headers']

# SPECIAL QUERIES
FEELING_LUCKY = 'Special:Random/main'

# EMOTES / EMOJIS
SKILL_EMOTES = configuration()['skill_emotes']

# THUMBNAILS
BUCKET_ICO = configuration()['icons']['bucket_ico']
LEVER_ICO = configuration()['icons']['lever_ico']
MINIGAME_ICO = configuration()['icons']['minigame_ico']
QUEST_ICO = configuration()['icons']['quest_ico']
STUB_ICO = configuration()['icons']['stub_ico']

# HISCORES
HISCORES_ORDER = [
    'Overall', 'Attack', 'Defence', 'Strength', 'Hitpoints', 'Ranged', 'Prayer',
    'Magic', 'Cooking', 'Woodcutting', 'Fletching', 'Fishing', 'Firemaking',
    'Crafting', 'Smithing', 'Mining', 'Herblore', 'Agility', 'Thieving', 'Slayer',
    'Farming', 'Runecraft', 'Hunter', 'Construction',
    'TBC', 'Bounty Hunter (Hunter)', 'Bounty Hunter (Rogue)',
    'Clue Scrolls (All)', 'Clue Scrolls (Beginner)', 'Clue Scrolls (Easy)',
    'Clue Scrolls (Medium)', 'Clue Scrolls (Hard)', 'Clue Scrolls (Elite)',
    'Clue Scrolls (Master)',
    'LMS - Rank', 'PvP Arena - Rank',
    'Soul Wars Zeal', 'Rifts Closed',
    'Abyssal Sire', 'Alchemical Hydra', 'Barrows Chests', 'Bryophyta', 'Callisto',
    'Cerberus', 'Chambers of Xeric', 'Chambers of Xeric: Challenge Mode', 'Chaos Elemental',
    'Chaos Fanatic', 'Commander Zilyana', 'Corporeal Beast', 'Dagannoth Prime',
    'Daggonoth Rex', 'Daggonoth Supreme', 'Crazy Archaeologist', 'Deranged Archaeologist',
    'General Graardor', 'Giant Mole', 'Grotesque Guardians', 'Hespori', 'Kalphite Queen', 
    'King Black Dragon', 'Kraken', 'Kree\'Arra', 'K\'ril Tsutsaroth', 'Mimic', 'Nex', 'Nightmare',
    'Phosani\'s Nightmare', 'Obor', 'Phantom Muspah', 'Sarachnis', 'Scorpia', 'Skotizo',
    'Tempoross', 'The Gauntlet', 'The Corrupted Gauntlet', 'Theatre of Blood',
    'Theatre of Blood: Hard Mode', 'Thermonuclear Smoke Devil', 'Tombs of Amascut',
    'Tombs of Amascut: Expert Mode', 'TzKal-Zuk', 'TzTok-Jad', 'Venenatis', 'Vet\'ion', 'Vorkath',
    'Wintertodt', 'Zalcano', 'Zulrah'
]

STAT_ORDER = [
    'Attack', 'Hitpoints', 'Mining', 'Strength', 'Agility', 'Smithing', 'Defence', 'Herblore', 'Fishing',
    'Ranged', 'Thieving', 'Cooking', 'Prayer', 'Crafting', 'Firemaking', 'Magic', 'Fletching', 'Woodcutting',
    'Runecraft', 'Slayer', 'Farming', 'Construction', 'Hunter', 'Overall'
]

COMBAT_SKILLS = [
    'Attack', 'Defence', 'Hitpoints', 'Magic', 'Prayer', 'Ranged', 'Strength'
]

CLUE_SCROLL_ORDER = HISCORES_ORDER[28:34]
BOSS_ORDER = HISCORES_ORDER[39:89]
