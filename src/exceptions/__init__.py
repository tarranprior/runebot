'''
Nonexistence.
Thrown when a user's search query doesn't return any results (or doesn't exist!)
'''


class Nonexistence(Exception):
    def __init__(self, message: str = f'The term you have searched for does not exist in Old School RuneScape. It may have never existed, or was added to RuneScape after the August 2007 Archive of RuneScape, which Old School RuneScape was based on, and has not been replicated.\n\nIf you are searching for a future update, please look for it at [upcoming updates](https://oldschool.runescape.wiki/w/Upcoming_updates) or create an article about it, supplying definite sources and citations.'):
        self.message = message
        super().__init__(self.message)


'''
No Alchemy Data.
Thrown when a user's search query doesn't return any alchemy data.
'''


class NoAlchemyData(Exception):
    def __init__(self, message: str = f'The term you have searched for does not have any **alchemy data**. Try selecting one of the options from the list of suggestions.\n\n**Usage**: `/alchemy <ITEM_NAME>`'):
        self.message = message
        super().__init__(self.message)


'''
No Hiscore Data.
Thrown when a player doesn't exist on the Hiscores, or if the Hiscores are unavailable.
'''


class NoHiscoreData(Exception):
    def __init__(self, message: str = f'The player you have searched for doesn\'t appear to exist on the **Hiscores**, or the **Hiscores** are currently unavailable.\n\n**Usage**: `/stats <USERNAME> [GAME_MODE (optional)]`'):
        self.message = message
        super().__init__(self.message)


'''
No Minigame Data.
Thrown when a user's search query doesn't return any minigame data.
'''


class NoMinigameData(Exception):
    def __init__(self, message: str = f'The term you have searched for does not appear to be a **minigame**. Try selecting one of the options from the list of suggestions, or visit [this page](https://oldschool.runescape.wiki/w/Minigames) for a full list of minigames.\n\n**Usage**: `/minigame <MINIGAME_NAME>`'):
        self.message = message
        super().__init__(self.message)


'''
No Monster Data.
Thrown when a user's search query doesn't return any monster data.
'''


class NoMonsterData(Exception):
    def __init__(self, message: str = f'The term you have searched for does not appear to be a **monster**. Try selecting one of the options from the list of suggestions, or visit [this page](https://oldschool.runescape.wiki/w/Bestiary) for a full list of monsters.\n\n**Usage**: `/bestiary <MONSTER_NAME>`'):
        self.message = message
        super().__init__(self.message)


'''
No Price Data.
Thrown when a user's search query doesn't return any price data.
'''


class NoPriceData(Exception):
    def __init__(self, message: str = f'The term you have searched for does not have any **price data**. Try selecting one of the options from the list of suggestions.\n\n**Usage**: `/price <ITEM_NAME>`'):
        self.message = message
        super().__init__(self.message)


'''
No Quest Data.
Thrown when a user's search query doesn't return any quest data.
'''


class NoQuestData(Exception):
    def __init__(self, message: str = f'The term you have searched for does not appear to be a **quest**. Try selecting one of the options from the list of suggestions, or visit [this page](https://oldschool.runescape.wiki/w/Quests/List) for a full list of quests.\n\n**Usage**: `/quests <QUEST_NAME>`'):
        self.message = message
        super().__init__(self.message)


'''
No Administrator Permissions.
Thrown when a user without administritive permissions tries to invoke a administrator command.
'''


class NoAdministratorPermissions(Exception):
    def __init__(self, message: str = 'This command can only be used by **administrators**. For more information on commands, use `/help`.'):
        self.message = message
        super().__init__(self.message)


'''
Stub Article.
Thrown when an article has insufficient or unparsable information.
'''


class StubArticle(Exception):
    def __init__(self, message: str = 'This means there is **insufficient information** on this article to display. However, this does not mean the stub is not a legitimate article; it just needs to be expanded or may not be supported by RuneBot at this time.'):
        self.message = message
        super().__init__(self.message)


'''
Username Invalid
Thrown when a username is invalid (too many characters, contains symbols etc.)
'''


class UsernameInvalid(Exception):
    def __init__(self, message: str = 'The username provided appears to be **invalid** or **doesn\'t exist**. Please try a different username.\n\n**Usage**: `/stats <USERNAME> [GAME_MODE (optional)]`'):
        self.message = message
        super().__init__(self.message)


'''
No Game Mode Data
Thrown when a username doesn't exist on a particular game mode (Ex: Searching for an Ironman on UIM Mode.)
'''

class NoGameModeData(Exception):
    def __init__(self, message: str = 'The username provided doesn\'t appear to exist under this **gamemode**. Please select a different `game_mode`, or try another username.\n\n**Usage**: `/stats <USERNAME> [GAME_MODE (optional)]`'):
        self.message = message
        super().__init__(self.message)