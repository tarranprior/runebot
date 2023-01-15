from utils.helpers import configuration


# URLs
BASE_URL = configuration()['urls']['osrswiki_url']
WIKIAPI_URL = configuration()['urls']['priceapi_wikipedia']
PRICEAPI_URL = configuration()['urls']['priceapi_official']
GRAPHAPI_URL = configuration()['urls']['graphapi_official']

# HEADERS
HEADERS = configuration()['headers']

# SPECIAL QUERIES
FEELING_LUCKY = 'Special:Random/main'

# COMMON THUMBNAILS
BUCKET_ICO = configuration()['icons']['bucket_ico']
LEVER_ICO = configuration()['icons']['lever_ico']
QUEST_ICO = configuration()['icons']['quest_ico']
MINIGAME_ICO = configuration()['icons']['minigame_ico']
STUB_ICO = configuration()['icons']['stub_ico']
