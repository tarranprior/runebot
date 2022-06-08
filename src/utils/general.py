import io, os, sys
import json
from urllib.request import Request, urlopen

from colorthief import ColorThief as ColourThief

import disnake

'''
Function to check whether colour mode is set to True/False.
'''
def check_colour_mode() -> None:
    colour_mode = load_configuration()['configuration']['colour_mode']
    if colour_mode == 'True':
        return(True)
    return(False)

'''
Extracts the most frequent colour from an image with a given URL, using color-thief-py.
(https://github.com/fengsp/color-thief-py)

:param image_url: (String) - Represents the URL/to/image.
:param headers: (String) - Represents HTTP request headers for the web request.
'''
def extract_colour(image_url, headers) -> None:
    colour_mode = check_colour_mode()
    if colour_mode == True:
        request_image = Request(image_url, headers=headers)
        open_image = urlopen(request_image)
        image_data = io.BytesIO(open_image.read())
        colour_thief = ColourThief(image_data)
        dominant_colour = colour_thief.get_color(quality=1)
        return(dominant_colour)
    return((disnake.Colour.og_blurple().r, disnake.Colour.og_blurple().g, disnake.Colour.og_blurple().b))

'''
Function to return configuration data from './config.json'
'''
def load_configuration():
    if os.path.isfile("config.json"):
        with open("config.json") as json_file:
            data = json.load(json_file)
            return data
    else:
        sys.exit(f"Configuration file not found. Please add it and try again.")

'''
Function to reformat a query.
:param query: (String) - Represents a search value.
'''
def search_query(query: str) -> None:
    search_query = query.lower().replace(' ', '_')
    return(search_query)