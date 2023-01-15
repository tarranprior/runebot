from .database import get_colour_mode

import disnake
import io
import json
import os
import sys

from colorthief import ColorThief as ColourThief
from humanfriendly import format_timespan
from loguru import logger
from urllib.request import Request, urlopen


'''
Helper function which converts unix timestamps to "human friendly" durations.
(https://github.com/xolox/python-humanfriendly)
:param date_1: (Datetime) - Represents a datetime object.
:param date_2: (Datetime) - Represents a datetime object.
'''


def convert_date_to_duration(date_1, date_2):
    diff = date_1 - date_2
    seconds = diff.total_seconds()
    timespan = format_timespan(seconds).split(',')[0].split(' and ')[0]
    return (f'{timespan} ago')


'''
Helper function which returns configuration data from './config.json'
'''


def configuration():
    if os.path.isfile('config.json'):
        with open('config.json') as json_file:
            data = json.load(json_file)
            return (data)
    else:
        sys.exit(f'Configuration file not found. Please add it and try again.')


'''
Helper function which extracts the most frequent colour from an image with a given URL, using color-thief-py.
(https://github.com/fengsp/color-thief-py)
:param guild_id: (Integer) - Represents the guild id.
:param image_url: (String) - Represents the URL/to/image.
:param headers: (String) - Represents HTTP request headers for the web request.
'''


async def extract_colour(self, guild_id: int, guild_owner_id: int, image_url: str, headers: str) -> None:
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
                    'Empty pixels when quantize. Ignoring colour extraction.')
    return ((disnake.Colour.og_blurple().r,
             disnake.Colour.og_blurple().g,
             disnake.Colour.og_blurple().b))


'''
Helper function which reformats (normalises) price integers into RuneScape currency (eg. 550000 to 550K gp)
:param price: (Integer) - Represents a price integer.
'''


def normalise_price(price: int) -> None:
    if price < 1000:
        return (f'{price:,.0f} gp')
    elif price < 1000000:
        return (f'{price / 1000:,.1f} K gp')
    elif price < 1000000000:
        return (f'{price / 1000000:,.1f} M gp')
    else:
        return (f'{price / 1000000000:,.2f} B gp')


'''
Helper function which replaces spaces (characters) with underscores in a search query for parsing purposes.
:param query: (String) - Represents a search value.
'''


def replace_spaces(query: str) -> None:
    search_query = query.replace(' ', '_')
    return (search_query)
