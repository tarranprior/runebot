'''
Nonexistence.
Thrown when a user's search query doesn't return any results (or doesn't exist!)
:param self:
:param query: (String) - Represents a search query.
'''


class Nonexistence(Exception):
    def __init__(self, query: str):
        self.message = f'The term you have searched for does not exist in Old School RuneScape. It may have never existed, or was added to RuneScape after the August 2007 Archive of RuneScape, which Old School RuneScape was based on, and has not been replicated.\n\nIf you are searching for a future update, please look for it at [upcoming updates](https://oldschool.runescape.wiki/w/Upcoming_updates) or create an article about it, supplying definite sources and citations.'
        super().__init__(self.message)


'''
No alchemy data.
Thrown when a user's search query doesn't return any alchemy data.
:param self:
:param query: (String) - Represents a search query.
'''


class NoAlchemyData(Exception):
    def __init__(self, query: str):
        self.message = f'The term you have searched for does not have any alch data. Try selecting one of the options from the list of suggestions.'
        super().__init__(self.message)


'''
No minigame data.
Thrown when a user's search query doesn't return any minigame data.
:param self:
:param query: (String) - Represents a search query.
'''


class NoMinigameData(Exception):
    def __init__(self, query: str):
        self.message = f'The term you have searched for does not appear to be a minigame. Try selecting one of the options from the list of suggestions.'
        super().__init__(self.message)


'''
No monster data.
Thrown when a user's search query doesn't return any monster data.
:param self:
:param query: (String) - Represents a search query.
'''


class NoMonsterData(Exception):
    def __init__(self, query: str):
        self.message = f'The term you have searched for does not appear to be a monster. Try selecting one of the options from the list of suggestions.'
        super().__init__(self.message)


'''
No price data.
Thrown when a user's search query doesn't return any price data.
:param self:
:param query: (String) - Represents a search query.
'''


class NoPriceData(Exception):
    def __init__(self, query: str):
        self.message = f'The term you have searched for does not have any price data. Try selecting one of the options from the list of suggestions.'
        super().__init__(self.message)


'''
No quest data.
Thrown when a user's search query doesn't return any quest data.
:param self:
:param query: (String) - Represents a search query.
'''


class NoQuestData(Exception):
    def __init__(self, query: str):
        self.message = f'The term you have searched for does not appear to be a quest. Try selecting one of the options from the list of suggestions.'
        super().__init__(self.message)


'''
No administrator permissions.
Thrown when a user without administritive permissions tries to invoke a administrator command.
:param self:
:param message: (String) - Represents an error message.
'''


class NoAdministratorPermissions(Exception):
    def __init__(
            self,
            message: str = 'This command can only be used by administrators. For more information on commands, use `/help`.'):
        self.message = message
        super().__init__(self.message)


'''
Stub article.
Thrown when an article has insufficient or unparsable information.
:param self:
:param message: (String) - Represents an error message.
'''


class StubArticle(Exception):
    def __init__(self, message: str = 'This means there is insufficient information on this article to display. However, this does not mean the stub is not a legitimate article; it just needs to be expanded or may not be supported by RuneBot at this time.'):
        self.message = message
        super().__init__(self.message)
