#! /usr/bin/env python3

'''
This module contains configuration data for the RuneBot
application.

Most configuration data is read from the `config.json` file,
which should be stored in the root of the project directory.
'''

from utils.helpers import configuration


# CURRENT VERSION
VER = 'v1.0.5'

# GENERAL
MAX_CHARS = 12 # Represents maximum character limit for usernames.

# URL / HEADERS
HEADERS = configuration()['headers']
URLS = configuration()['urls']

# URLs (API)
BASE_URL = URLS['osrswiki']
HISCORES_URL = URLS['hiscores']
WIKIAPI_URL = URLS['priceapi_wikipedia']
PRICEAPI_URL = URLS['priceapi_official']
GRAPHAPI_URL = URLS['graphapi']

# ACCOUNT TYPES
ACCOUNT_TYPES = [
    'Normal',
    'Ironman',
    'Hardcore Ironman',
    'Ultimate Ironman',
    'Skiller',
    '1 Defence',
    'Fresh Start Worlds'
]

# HISCORE URLs
NORMAL_HISCORES = HISCORES_URL + URLS['normal']['h']
IRONMAN_HISCORES = HISCORES_URL + URLS['ironman']['h']
HARDCORE_IRONMAN_HISCORES = HISCORES_URL + URLS['hardcore_ironman']['h']
ULTIMATE_HISCORES = HISCORES_URL + URLS['ultimate']['h']
SKILLER_HISCORES = HISCORES_URL + URLS['skiller']['h']
SKILLER_DEFENCE_HISCORES = HISCORES_URL + URLS['skiller_defence']['h']
FRESH_START_HISCORES = HISCORES_URL + URLS['fresh_start']['h']

HISCORE_URLS = {
    'Ironman': IRONMAN_HISCORES,
    'Hardcore Ironman': HARDCORE_IRONMAN_HISCORES,
    'Ultimate Ironman': ULTIMATE_HISCORES,
    'Skiller': SKILLER_HISCORES,
    '1 Defence': SKILLER_DEFENCE_HISCORES,
    'Fresh Start Worlds': FRESH_START_HISCORES,
    'Normal': NORMAL_HISCORES
}

# HISCORE API URLs
NORMAL_API = HISCORES_URL + URLS['normal']['a']
IRONMAN_API = HISCORES_URL + URLS['ironman']['a']
HARDCORE_IRONMAN_API = HISCORES_URL + URLS['hardcore_ironman']['a']
ULTIMATE_API = HISCORES_URL + URLS['ultimate']['a']
SKILLER_API = HISCORES_URL + URLS['skiller']['a']
SKILLER_DEFENCE_API = HISCORES_URL + URLS['skiller_defence']['a']
FRESH_START_API = HISCORES_URL + URLS['fresh_start']['a']

HISCORE_API_URLS = {
    'Ironman': IRONMAN_API,
    'Hardcore Ironman': HARDCORE_IRONMAN_API,
    'Ultimate Ironman': ULTIMATE_API,
    'Skiller': SKILLER_API,
    '1 Defence': SKILLER_DEFENCE_API,
    'Fresh Start Worlds': FRESH_START_API,
    'Normal': NORMAL_API
}

HISCORES_ORDER = [
    'Overall',
    'Attack',
    'Defence',
    'Strength',
    'Hitpoints',
    'Ranged',
    'Prayer',
    'Magic',
    'Cooking',
    'Woodcutting',
    'Fletching',
    'Fishing',
    'Firemaking',
    'Crafting',
    'Smithing',
    'Mining',
    'Herblore',
    'Agility',
    'Thieving',
    'Slayer',
    'Farming',
    'Runecraft',
    'Hunter',
    'Construction',
    '----',
    '----',
    'Bounty Hunter - Hunter',
    'Bounty Hunter - Rogue',
    'Bounty Hunter (Legacy) - Hunter',
    'Bounty Hunter (Legacy) - Rogue',
    'Clue Scrolls (All)',
    'Clue Scrolls (Beginner)',
    'Clue Scrolls (Easy)',
    'Clue Scrolls (Medium)',
    'Clue Scrolls (Hard)',
    'Clue Scrolls (Elite)',
    'Clue Scrolls (Master)',
    'LMS - Rank',
    'PvP Arena - Rank',
    'Soul Wars Zeal',
    'Rifts Closed',
    'Colosseum Glory',
    'Collections Logged',
    'Abyssal Sire',
    'Alchemical Hydra',
    'Amoxliatl',
    'Araxxor',
    'Artio',
    'Barrows Chests',
    'Bryophyta',
    'Callisto',
    'Calvar\'ion',
    'Cerberus',
    'Chambers of Xeric',
    'Chambers of Xeric: Challenge Mode',
    'Chaos Elemental',
    'Chaos Fanatic',
    'Commander Zilyana',
    'Corporeal Beast',
    'Crazy Archaeologist',
    'Dagannoth Prime',
    'Dagannoth Rex',
    'Dagannoth Supreme',
    'Deranged Archaeologist',
    'Duke Sucellus',
    'General Graardor',
    'Giant Mole',
    'Grotesque Guardians',
    'Hespori',
    'Kalphite Queen',
    'King Black Dragon',
    'Kraken',
    'Kree\'Arra',
    'K\'ril Tsutsaroth',
    'Lunar Chests',
    'Mimic',
    'Nex',
    'Nightmare',
    'Phosani\'s Nightmare',
    'Obor',
    'Phantom Muspah',
    'Sarachnis',
    'Scorpia',
    'Scurrius',
    'Skotizo',
    'Sol Heredit',
    'Spindel',
    'Tempoross',
    'The Gauntlet',
    'The Corrupted Gauntlet',
    'The Hueycoatl',
    'The Leviathan',
    'The Royal Titans',
    'The Whisperer',
    'Theatre of Blood',
    'Theatre of Blood: Hard Mode',
    'Thermonuclear Smoke Devil',
    'Tombs of Amascut',
    'Tombs of Amascut: Expert Mode',
    'TzKal-Zuk',
    'TzTok-Jad',
    'Vardorvis',
    'Venenatis',
    'Vet\'ion',
    'Vorkath',
    'Wintertodt',
    'Zalcano',
    'Zulrah'
]

STAT_ORDER = [
    'Attack',
    'Hitpoints',
    'Mining',
    'Strength',
    'Agility',
    'Smithing',
    'Defence',
    'Herblore',
    'Fishing',
    'Ranged',
    'Thieving',
    'Cooking',
    'Prayer',
    'Crafting',
    'Firemaking',
    'Magic',
    'Fletching',
    'Woodcutting',
    'Runecraft',
    'Slayer',
    'Farming',
    'Construction',
    'Hunter',
    'Overall'
]

STAT_COLUMNS = [
    [
        (col.lower(), col) for col in [
            'Attack',
            'Strength',
            'Defence',
            'Ranged',
            'Prayer',
            'Magic',
            'Runecraft',
            'Construction'
        ]
    ],
    [
        (col.lower(), col) for col in [
            'Hitpoints',
            'Agility',
            'Herblore',
            'Thieving',
            'Crafting',
            'Fletching',
            'Slayer',
            'Hunter'
        ]
    ],
    [
        (col.lower(), col) for col in [
            'Mining',
            'Smithing',
            'Fishing',
            'Cooking',
            'Firemaking',
            'Woodcutting',
            'Farming',
            'Overall'
        ]
    ]
]

BOSS_COLUMNS = [
    [
        ('abyssalsire', 'Abyssal Sire'),
        ('araxxor', 'Araxxor'),
        ('bryophyta', 'Bryophyta'),
        ('cerberus', 'Cerberus'),
        ('chaoselemental', 'Chaos Elemental'),
        ('corporealbeast', 'Corporeal Beast'),
        ('dagannothrex', 'Dagannoth Rex'),
        ('dukesucellus', 'Duke Sucellus'),
        ('grotesqueguardians', 'Grotesque Guardians'),
        ('kbd', 'King Black Dragon'),
        ('kriltsutsaroth', "K'ril Tsutsaroth"),
        ('nex', 'Nex'),
        ('obor', 'Obor'),
        ('scorpia', 'Scorpia'),
        ('solheredit', 'Sol Heredit'),
        ('thegauntlet', 'The Gauntlet'),
        ('theleviathan', 'The Leviathan'),
        ('tobhardmode', 'Theatre of Blood: Hard Mode'),
        ('tombsofamascutexpertmode', 'Tombs of Amascut: Expert Mode'),
        ('vardorvis', 'Vardorvis'),
        ('vetion', "Vet'ion"),
        ('zalcano', 'Zalcano')
    ],
    [
        ('alchemicalhydra', 'Alchemical Hydra'),
        ('artio', 'Artio'),
        ('callisto', 'Callisto'),
        ('cox', 'Chambers of Xeric'),
        ('chaosfanatic', 'Chaos Fanatic'),
        ('crazyarchaeologist', 'Crazy Archaeologist'),
        ('dagannothsupreme', 'Dagannoth Supreme'),
        ('generalgraardor', 'General Graardor'),
        ('hespori', 'Hespori'),
        ('kraken', 'Kraken'),
        ('lunarchests', 'Lunar Chests'),
        ('nightmare', 'Nightmare'),
        ('phantommuspah', 'Phantom Muspah'),
        ('scurrius', 'Scurrius'),
        ('spindel', 'Spindel'),
        ('thecorruptedgauntlet', 'The Corrupted Gauntlet'),
        ('theroyaltitans', 'The Royal Titans'),
        ('thermonuclearsmokedevil', 'Thermonuclear Smoke Devil'),
        ('tzkalzuk', 'TzKal-Zuk'),
        ('venenatis', 'Venenatis'),
        ('vorkath', 'Vorkath'),
        ('zulrah', 'Zulrah')
    ],
    [
        ('amoxliatl', 'Amoxliatl'),
        ('barrowschests', 'Barrows Chests'),
        ('calvarion', "Calvar'ion"),
        ('coxchallengemode', 'Chambers of Xeric: Challenge Mode'),
        ('commanderzilyana', 'Commander Zilyana'),
        ('dagannothprime', 'Dagannoth Prime'),
        ('derangedarchaeologist', 'Deranged Archaeologist'),
        ('giantmole', 'Giant Mole'),
        ('kalphitequeen', 'Kalphite Queen'),
        ('kreearra', "Kree'Arra"),
        ('mimic', 'Mimic'),
        ('phosanisnightmare', "Phosani's Nightmare"),
        ('sarachnis', 'Sarachnis'),
        ('skotizo', 'Skotizo'),
        ('tempoross', 'Tempoross'),
        ('thehueycoatl', 'The Hueycoatl'),
        ('thewhisperer', 'The Whisperer'),
        ('tob', 'Theatre of Blood'),
        ('tombsofamascut', 'Tombs of Amascut'),
        ('tztokjad', 'TzTok-Jad'),
        ('wintertodt', 'Wintertodt')
    ]
]

BOUNTY_COLUMNS = [
    [
        ('bh_legacyhunter', 'Bounty Hunter (Legacy) - Hunter'),
        ('bh_hunter', 'Bounty Hunter - Hunter')
    ],
    [
        ('bh_legacyrogue', 'Bounty Hunter (Legacy) - Rogue'),
        ('bh_rogue', 'Bounty Hunter - Rogue')
    ]
]

CLUE_COLUMNS = [
    [
        ('cluescrolls_beginner', 'Clue Scrolls (Beginner)'),
        ('cluescrolls_hard', 'Clue Scrolls (Hard)')
    ],
    [
        ('cluescrolls_easy', 'Clue Scrolls (Easy)'),
        ('cluescrolls_elite', 'Clue Scrolls (Elite)')
    ],
    [
        ('cluescrolls_medium', 'Clue Scrolls (Medium)'),
        ('cluescrolls_master', 'Clue Scrolls (Master)')
    ]
]

COMBAT_SKILLS = [
    'Attack',
    'Defence',
    'Hitpoints',
    'Magic',
    'Prayer',
    'Ranged',
    'Strength'
]

CLUE_SCROLL_ORDER = HISCORES_ORDER[28:34]
BOSS_ORDER = HISCORES_ORDER[39:89]

# URLs (Misc)
SUPPORT_SERVER = configuration()['configuration']['support_server']

# SPECIAL QUERIES
FEELING_LUCKY = 'Special:Random/main'

# EMOTES (EMOJIS)
ACCOUNT_EMOTES = configuration()['account_emotes']
BOSS_EMOTES = configuration()['boss_emotes']
BOUNTY_EMOTES = configuration()['bounty_emotes']
CLUE_EMOTES = configuration()['clue_emotes']
SKILL_EMOTES = configuration()['skill_emotes']

# THUMBNAILS
FILLER = configuration()['thumbs']['filler']
BUCKET = configuration()['thumbs']['bucket']
LEVER = configuration()['thumbs']['lever']
MINIGAME = configuration()['thumbs']['minigame']
QUEST = configuration()['thumbs']['quest']
STUB = configuration()['thumbs']['stub']

# GRAYSCALE THUMBNAILS
FILLER_GRAYSCALE = configuration()['grayscale_thumbs']['filler']
BUCKET_GRAYSCALE = configuration()['grayscale_thumbs']['bucket']

# THUMBNAIL DICT
THUMBNAILS = {
    'filler': FILLER,
    'bucket': BUCKET,
    'lever': LEVER,
    'minigame': MINIGAME,
    'quest': QUEST,
    'stub': STUB
}

# GRAYSCALE THUMBNAIL DICT
GRAYSCALE_THUMBNAILS = {
    'filler': FILLER_GRAYSCALE,
    'bucket': BUCKET_GRAYSCALE
}

# BLACKLISTS
BLACKLIST_CHARS = [
    ',',
    '!',
    ':',
    ';',
    '[',
    ']',
    '{',
    '}',
    '?',
    '#',
    '@',
    '\\',
    '/',
    '¬',
    '`',
    '~',
]

BLACKLIST_ITEMS = [
    '(+)',
    '(-)',
    '(burnt)',
    'Anchovy paste',
    'Burning',
    'Burnt',
    'Cabbage (Draynor Manor)',
    'Ensouled',
    'Guthix balance (unf)',
    'Sigil of',
    'The great divide',
]

BLACKLIST_QUESTS = [
    'Cutscene',
    'Quest items/',
    'Quest Difficulties',
    'Quest experience rewards',
    'Quests',
    'Quests/',
    'Quick guide',
]
