#! /usr/bin/env python3

'''
This module defines a collection of exceptions that can be raised
in the context of RuneBot.

Each exception has an associated custom message that can be used to
provide additional information to the user.

For more information about each function and its usage, refer to the
docstrings.
'''


class Nonexistence(Exception):
    '''
    Thrown when a user's search query doesn't return any results
    (or doesn't exist!)

    :param message: (String) -
        A custom message to display when the exception is raised. Defaults to
        a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The term you have searched for does not exist in Old School RuneScape. '
        'It may have never existed, or was added to RuneScape after the August '
        '2007 Archive of RuneScape, which Old School RuneScape was based on, '
        'and has not been replicated.\n\nIf you are searching for a future update, '
        'please look for it at [upcoming updates]'
        '(https://oldschool.runescape.wiki/w/Upcoming_updates) or create an '
        'article about it, supplying definite sources and citations.'
    )) -> None:
        '''
        Initialises a new instance of the Nonexistence class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoAlchemyData(Exception):
    '''
    Thrown when a user's search query doesn't return any alchemy data.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The term you have searched for does not have any **alchemy data**. '
        'Try selecting one of the options from the list of suggestions.'
        '\n\n**Usage**: `/alchemy <ITEM_NAME>`'
    )) -> None:
        '''
        Initialises a new instance of the NoAlchemyData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoHiscoreData(Exception):
    '''
    Thrown when a player doesn't exist on the Hiscores,
    or if the Hiscores are unavailable.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The player you have searched for doesn\'t appear to exist '
        'on the **Hiscores**, or the **API** is currently unavailable. '
        'Please try another username or try again later.\n\n'
        '**Usage**: `/stats <USERNAME> [ACCOUNT_TYPE (optional)]`'
    )) -> None:
        '''
        Initialises a new instance of the NoHiscoreData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoMinigameData(Exception):
    '''
    Thrown when a user's search query doesn't return any minigame data.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The term you have searched for does not appear to be a **minigame**. '
        'Try selecting one of the options from the list of suggestions, '
        'or visit [this page](https://oldschool.runescape.wiki/w/Minigames) '
        'for a full list of minigames.\n\n**Usage**: `/minigame <MINIGAME_NAME>`'
    )) -> None:
        '''
        Initialises a new instance of the NoMinigameData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoMonsterData(Exception):
    '''
    Thrown when a user's search query doesn't return any monster data.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The term you have searched for does not appear to be a **monster**. '
        'Try selecting one of the options from the list of suggestions, '
        'or visit [this page](https://oldschool.runescape.wiki/w/Bestiary) '
        'for a full list of monsters.\n\n**Usage**: `/bestiary <MONSTER_NAME>`'
    )) -> None:
        '''
        Initialises a new instance of the NoMonsterData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoPriceData(Exception):
    '''
    Thrown when a user's search query doesn't return any price data.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The term you have searched for does not have any **price data**. '
        'Try selecting one of the options from the list of suggestions.\n\n'
        '**Usage**: `/price <ITEM_NAME>`'
    )) -> None:
        '''
        Initialises a new instance of the NoPriceData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoQuestData(Exception):
    '''
    Thrown when a user's search query doesn't return any quest data.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The term you have searched for does not appear to be a **quest**. '
        'Try selecting one of the options from the list of suggestions, '
        'or visit [this page](https://oldschool.runescape.wiki/w/Quests/List) '
        'for a full list of quests.\n\n**Usage**: `/quests <QUEST_NAME>`'
    )) -> None:
        '''
        Initialises a new instance of the NoQuestData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoAdministratorPermissions(Exception):
    '''
    Thrown when a user without administritive permissions
    tries to invoke a administrator command.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'This command can only be used by **administrators**. For more '
        'informationon commands, use `/help`.'
    )) -> None:
        '''
        Initialises a new instance of the NoAdministratorPermissions class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class StubArticle(Exception):
    '''
    Thrown when an article has insufficient or unparsable information.

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'This means there is **insufficient information** on this article to '
        'display. However, this does not mean the stub is not a legitimate '
        'article; it just needs to be expanded or may not be supported by '
        'RuneBot at this time.'
    )) -> None:
        '''
        Initialises a new instance of the StubArticle class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class UsernameInvalid(Exception):
    '''
    Thrown when a username is invalid (too many characters, contains symbols
    etc.)

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The username provided appears to be **invalid** or **doesn\'t exist**. '
        'Please try a different username.\n\n'
        '**Usage**: `/stats <USERNAME> [ACCOUNT_TYPE (optional)]`'
    )) -> None:
        '''
        Initialises a new instance of the UsernameInvalid class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)


class NoGameModeData(Exception):
    '''
    Thrown when the provided username does not appear to exist under the
    given game mode (Ex: Selecting UIM when searching for a HCIM account.)

    :param message: (String) -
        A custom message to display when the exception is raised.
        Defaults to a pre-defined message.

    :return: (None)
    '''

    def __init__(self, message: str = (
        'The username provided doesn\'t appear to exist under this '
        '**Account Type**. Please select a different `account_type`, or try '
        'another username.\n\n**Usage**: `/stats <USERNAME> [ACCOUNT_TYPE (optional)]`'
    )) -> None:
        '''
        Initialises a new instance of the NoGameModeData class.

        :param message: (Optional[String]) -
            A custom message to display when the exception is raised.
            Defaults to a pre-defined message.

        :return: (None)
        '''

        self.message = message
        super().__init__(self.message)
