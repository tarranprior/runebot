'''
Nonexistence
Thrown when a user's search query doesn't return any results (or doesn't exist!)
'''
class Nonexistence(Exception):
    def __init__(self, message: str = 'The term you have searched for does not exist in Old School RuneScape. It may have never existed, or was added to RuneScape after the August 2007 Archive of RuneScape, which Old School RuneScape was based on, and has not been replicated.\n\nIf you are searching for a future update, please look for it at [upcoming updates](https://oldschool.runescape.wiki/w/Upcoming_updates) or create an article about it, supplying definite sources and citations.'):
        self.message = message
        super().__init__(self.message)

class NoExamineText(Exception):
    def __init__(self, message: str = 'The term you have searched for does not appear to have any examine text, nor an examine option.'):
        self.message = message
        super().__init__(self.message)

class NoAlchData(Exception):
    def __init__(self, message: str = 'The term you have searched for does not have any alch data.'):
        self.message = message
        super().__init__(self.message)

class NoMonsterData(Exception):
    def __init__(self, message: str = 'The term you have searched for does not appear to be a monster.'):
        self.message = message
        super().__init__(self.message)

class NoPriceData(Exception):
    def __init__(self, message: str = 'The term you have searched for does not have any price data.'):
        self.message = message
        super().__init__(self.message)

class NoQuestData(Exception):
    def __init__(self, message: str = 'The term you have searched for does not appear to be a quest.'):
        self.message = message
        super().__init__(self.message)