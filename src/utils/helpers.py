#! /usr/bin/env python3

'''
This module contains various common helper utilities to help RuneBot
function properly.

Functions:
    - `convert_date_to_duration()`:
            Converts unix timestamps to "human friendly" durations.
    - `configuration()`:
            Reads the configuration file (config.json) and returns its contents as a dictionary.
    - `extract_colour()`:
            Extracts the most frequent colour from an image with a given URL.
    - `normalise_price()`:
            Reformats (normalises) price integers into RuneScape currency.
    - `slugify()`:
            Replaces spaces with underscores in a search query for parsing purposes (URL formatting).

Each function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import sys
import os
import io
import json

from typing import Optional, Tuple
from urllib.request import Request, urlopen
from loguru import logger
from humanfriendly import format_timespan
import disnake
from colorthief import ColorThief as ColourThief

from .database import get_colour_mode


def convert_date_to_duration(date_1, date_2) -> str:
    '''
    Helper function which converts unix timestamps to "human friendly"
    durations. (https://github.com/xolox/python-humanfriendly)

    :param date_1: (Datetime) -
        Represents a datetime object. The first datetime object to compare.
    :param date_2: (Datetime) -
        Represents a datetime object. The second datetime object to compare.

    :return: (String) -
        A string indicating the duration between the two
        datetime objects in a "human-friendly" format.
    '''

    diff = date_1 - date_2
    seconds = diff.total_seconds()
    timespan = format_timespan(seconds).split(',')[0].split(' and ')[0]
    return f'{timespan} ago'


def configuration() -> dict:
    '''
    Helper function which reads the configuration file (config.json)
    and returns its contents as a dictionary.

    :return: (Dictionary) -
        A dictionary representing the contents of the configuration file.
    '''

    if os.path.isfile('config.json'):
        with open('config.json', encoding='utf-8') as json_file:
            data = json.load(json_file)
            return data
    else:
        sys.exit('Configuration file not found. Please add it and try again.')


async def extract_colour(
    self,
    guild_id: int,
    guild_owner_id: int,
    image_url: str,
    headers: str) -> Optional[Tuple[int, int, int]]:
    '''
    Helper function which extracts the most frequent colour from an image with
    a given URL, using color-thief-py.
    (https://github.com/fengsp/color-thief-py)

    :param self: -
        Represents this object.
    :param guild_id: (Integer) -
        Represents the guild id.
    :param guild_owner_id: (Integer) -
        Represents the id of the guild owner.
    :param image_url: (String) -
        Represents the URL/to/image.
    :param headers: (String) -
        Represents HTTP request headers for the web request.

    :return: (Tuple) -
        A tuple representing the dominant RGB color value of the image,
        or None if an error occurs during color extraction.
    '''

    if image_url:
        colour_mode = await get_colour_mode(self, guild_id, guild_owner_id)
        if colour_mode:
            try:
                request_image = Request(image_url, headers=headers)
                open_image = urlopen(request_image)
                image_data = io.BytesIO(open_image.read())
                colour_thief = ColourThief(image_data)
                dominant_colour = colour_thief.get_color(quality=1)
                return (dominant_colour)
            except Exception:
                logger.error(
                    'Empty pixels when quantize. Ignoring colour extraction.'
                )
    return ((
        disnake.Colour.og_blurple().r,
        disnake.Colour.og_blurple().g,
        disnake.Colour.og_blurple().b
    ))


def normalise_price(price: int) -> Optional[str]:
    '''
    Helper function which reformats (normalises) price integers into
    RuneScape currency (eg. 550000 to 550K gp)

    :param price: (Integer) -
        Represents a price integer.

    :return: (String or None) -
        The normalized price value in a formatted string,
        or None if price is negative.
    '''

    if price < 1000:
        normalised_price = f'{price:,.0f} gp'
    elif price < 1000000:
        normalised_price = f'{price / 1000:,.1f} K gp'
    elif price < 1000000000:
        normalised_price = f'{price / 1000000:,.1f} M gp'
    else:
        return f'{price / 1000000000:,.2f} B gp'

    return normalised_price


def slugify(search_query: str) -> str:
    '''
    Helper function which replaces spaces (' ' characters) with underscores
    in a search query for parsing purposes (URL formatting.)

    :param search_query: (String) -
        Represents a search value.
    
    :return: (String) -
        The new "slugified" search query with underscores.
    '''

    search_query = search_query.replace(' ', '_')
    return search_query
