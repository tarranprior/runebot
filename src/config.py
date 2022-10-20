from utils.general import load_configuration


# URLs
BASE_URL = load_configuration()['urls']['wiki_url']
PRICEAPI_URL = load_configuration()['urls']['priceapi_url']
GRAPHAPI_URL = load_configuration()['urls']['graphapi_url']

# HEADERS
HEADERS = load_configuration()['headers']

# MISC
FEELING_LUCKY = 'Special:Random/main'
MAX_PURGE = 100

# COMMON THUMBNAILS
BUCKET_ICO = 'https://oldschool.runescape.wiki/images/thumb/Weird_gloop_detail.png/75px-Weird_gloop_detail.png?94769'
LEVER_ICO = 'https://oldschool.runescape.wiki/images/Lever.png?71ea6'
QUEST_ICO = 'https://oldschool.runescape.wiki/images/thumb/Quests.png/130px-Quests.png?f5120'
MINIGAME_ICO = 'https://oldschool.runescape.wiki/images/thumb/Minigames.png/120px-Minigames.png?d639f'
STUB_ICO = 'https://oldschool.runescape.wiki/images/thumb/Woodcutting_stump.png/200px-Woodcutting_stump.png?669ab'