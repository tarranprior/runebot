#! /usr/bin/env python3

'''
This module contains a basic factory for embed creation and functions
for message interaction components (Buttons, Dropdowns etc.)

Classes:
    - `EmbedFactory`:
            A class which represents the EmbedFactory function.

Functions:
    - `create()`:
            Creates an embed for display purposes.
    - `create_button()`:
            Creates a regular button for interaction responses.
    - `create_link_button()`:
            Creates a hyperlink button for interaction responses.
    - `create_dropdown()`:
            Creates a dropdown menu for interaction responses.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from typing import Tuple, Union

import disnake
from disnake.ui import Button, Select, View


class EmbedFactory:
    '''
    A class which represents the EmbedFactory function.
    '''

    def __init__(
        self,
        **kwargs
    ) -> None:
        '''
        Initialises a new `EmbedFactory` object with optional parameters.

        :param self: -
            Represents this object.

        :param title: (Optional[String]) -
            Represents a title for the embed.
        :param description: (Optional[String]) -
            Represents a description for the embed.
        :param colour: (Optional[disnake.Colour]) -
            Represents a colour for the embed. Defaults to `disnake.Colour.og_blurple()`.
        :param infobox: (Optional[Dictionary]) -
            Represents the infobox (properties) to display in the embed.
        :param options: (Optional[List]) -
                Represents a list of options for the Select Menu.
        :param thumbnail_url: (Optional[String]) -
            Represents a URL for the embed's thumbnail.
        :param button_label: (Optional[String]) -
            Represents a label for the embed's button.
        :param button_url: (Optional[String]) -
            Represents a hyperlink (URL) for the embed's button.
        :param button_emoji: (Optional[Union[disnake.Emoji, disnake.PartialEmoji, String]]) -
            Represents an emoji for the embed's button.

        :return: (None)
    '''

        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.colour = kwargs.get('colour', disnake.Colour.og_blurple())
        self.infobox = kwargs.get('infobox')
        self.options = kwargs.get('options', [])
        self.thumbnail_url = kwargs.get('thumbnail_url')
        self.button_label = kwargs.get('button_label')
        self.button_url = kwargs.get('button_url')


    def create(
        self,
        title: str = None,
        description: str = None,
        colour: disnake.Colour = None,
        infobox: dict = None,
        options: list = None,
        thumbnail_url: str = None,
        button_label: str = None,
        button_url: str = None,
        button_emoji: disnake.PartialEmoji = None
    ) -> Union[Tuple[disnake.Embed, View], disnake.Embed]:
        '''
        Creates an embed for display purposes.
        Each paramater is optional and defaults to None.

        :param self: -
            Represents this object.
        :param title: Optional([String]) -
            Represents a title for the embed.
        :param description: Optional([String]) -
            Represents a description for the embed.
        :param colour: Optional([disnake.Colour]) -
            Represents a colour for the embed.
        :param infobox: Optional([Dictionary]) -
            Represents the infobox (properties) to display in the embed.
        :param options: Optional([List]) -
            Represents a list of options for the Select Menu.
        :param thumbnail_url: Optional([String]) -
            Represents a URL for the embed's thumbnail.
        :param button_label: Optional([String]) -
            Represents a label for the embed's button.
        :param button_url: (Optional[String]) -
            Represents a hyperlink (URL) for the embed's button.
        :param button_emoji: (Optional[Union[disnake.Emoji, disnake.PartialEmoji, String]]) -
            Represents an emoji for the embed's button.

        :return: (Union[Tuple[disnake.Embed, View], disnake.Embed]) -
            A tuple containing the Embed and View objects, or just the Embed object.
        '''

        embed = disnake.Embed()
        view = View(timeout=None)

        embed.title = self.title if not title else title
        embed.description = self.description if not description else description
        embed.colour = self.colour if not colour else colour

        if options:
            dropdown = create_dropdown(options)
            view.add_item(dropdown)

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        if infobox:
            infobox.pop('Image', 'Icon')
            for i in list(infobox.items())[:3]:
                embed.add_field(name=i[0], value=i[1], inline=True)

        if button_url:
            if button_label:
                button = create_link_button(
                    button_label, button_url, button_emoji)
                view.add_item(button)
                return embed, view
            button = create_link_button(
                'Visit Page',
                button_url,
                button_emoji
            )
            view.add_item(button)
            return embed, view
        return embed


def create_button(label=None, emoji=None) -> Button:
    '''
    Creates a regular button for interaction responses.

    :param label: (Optional[String]) -
        Represents a label for the button.
    :param emoji: (Optional[Union[disnake.Emoji, disnake.PartialEmoji, String]]) -
        Represents an emoji for the button.

    :return: (Button) -
        Newly created Button object.
    '''

    button = Button(
        label=label,
        style=disnake.ButtonStyle.grey,
        emoji=emoji
    )
    return button


def create_link_button(label, url, emoji=None) -> Button:
    '''
    Creates a hyperlink button for interaction responses.

    :param label: (String) -
        Represents a label for the button.
    :param url: (String) -
        Represents a hyperlink (URL) for the button.
    :param emoji: (Optional[Union[disnake.Emoji, disnake.PartialEmoji, String]]) -
        Represents an emoji for the button.

    :return: (Button) -
        Newly created Button object.
    '''

    button = Button(
        label=label,
        style=disnake.ButtonStyle.link,
        url=url,
        emoji=emoji
    )
    return button


def create_dropdown(options) -> Select:
    '''
    Creates a dropdown menu for interaction responses.

    :param options: (List[String]) -
        Represents a list of options (labels) for the dropdown.

    :return: (Select) -
        Newly created Select object.
    '''

    dropdown = Select(placeholder='Select an option.', options=[])
    for option in options:
        dropdown.add_option(label=option)
    return dropdown
