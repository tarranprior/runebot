#! /usr/bin/env python3

'''
This module contains functions and logic for parsing data from HTML
content, the hiscores API, Exchange data etc. in the context of Runebot.

For more information about each function and its usage, refer to the
docstrings.

Key Functions:
    - `parse_all()`:
            A parser function which parses all attributes from an Old School
            RuneScape wikipedia page and returns a dictionary.
    - `parse_page()`:
            A parser function which parses all page content from an Old School
            RuneScape wikipedia page.
    - `parse_description()`:
            A parser function which parses a description from an Old School
            RuneScape wikipedia page.
    - `parse_infobox()`:
            A parser function which parses an infobox from an Old School
            RuneScape wikipedia page into a dictionary.
    - `parse_options()`:
            A parser function which parses a list of options for queries
            that may refer to several articles.
    - `parse_price_data()`:
            A parser function which parses price data using the official API.
    - `parse_title()`:
            A parser function which parses a title from an Old School RuneScape
            wikipedia page.
    - `generate_graph()`:
            A function which generates a graph with given API price data.
    - `parse_hiscores()`:
            A parser function which parses values from the official OSRS
            Hiscores API.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from urllib.request import Request, urlopen
from urllib.error import HTTPError
import uuid
from typing import List, Optional
import requests

from bs4 import BeautifulSoup
import matplotlib
import matplotlib.pyplot as plotter
matplotlib.use('Agg')

import exceptions
from utils.helpers import normalise_price, slugify


def parse_all(page_content: BeautifulSoup) -> dict:
    '''
    Parser function which parses all attributes (title,
    description, thumbnail etc.) from an Old School RuneScape
    wikipedia page and returns a dictionary.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.

    :return: (dict) -
        A dictionary containing the parsed title, description, infobox,
        options, and thumbnail URL.
    '''

    page_title = parse_title(page_content)
    page_description = parse_description(page_content)
    page_thumbnail = parse_thumbnail(page_content)

    if len(page_description) == 1:
        infobox = parse_infobox(page_content)
        return {'title': page_title,
                 'description': page_description,
                 'infobox': infobox,
                 'options': False,
                 'thumbnail_url': page_thumbnail}

    options = page_description
    return {'title': page_title,
             'description': False,
             'infobox': False,
             'options': options,
             'thumbnail_url': page_thumbnail}


def parse_page(url: str, search_query: str, headers: dict) -> BeautifulSoup:
    '''
    Parser function whichs parses all page content from an
    Old School RuneScape wikipedia page.

    :param url: (String) -
        Represents the base URL.
    :param search_query: (String) -
        Represents the search query given by the user. (Ex: 'firecape'.)
    :param headers: (Dictionary) -
        Represents a series of request headers.

    :return: (BeautifulSoup) -
        A BeautifulSoup object containing the parsed search results.
    '''

    new_query = slugify(search_query.rstrip(
        '\u200a'
    )) if search_query.endswith(
        '\u200a'
    ) else slugify(search_query).lower()
    queries = [new_query, slugify(search_query).rstrip('\u200a')]

    for query in queries:
        try:
            request = Request(f'{url}{query}', headers=headers)
            page = urlopen(request)
            page_content = BeautifulSoup(page, 'html.parser')
            break
        except HTTPError:
            continue
    else:
        raise exceptions.Nonexistence()

    return page_content


def parse_description(page_content) -> List[str]:
    '''
    Parser function which parses a description from an
    Old School RuneScape wikipedia page.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.

    :return: (List[String]) -
        A list containing the parsed description(s) for the page.
    '''

    page_div = page_content.find('div', class_='mw-parser-output')

    if str('This page doesn\'t exist on the wiki.') in page_div.getText():
        raise exceptions.Nonexistence

    for paragraph in page_content.find_all('p'):
        description = paragraph.getText().replace(
            '[1]', ''
        ).replace(
            '[2]', ''
        ).replace(
            '[3]', ''
        )
        if len(description) >= 34:
            break  # To only return qualifying descriptions for articles.

    if (str('May refer to').lower() in page_div.getText() or
       str('Could refer to').lower() in page_div.getText() or
       str('It can refer to:').lower() in page_div.getText() or
       str('Can mean any of the following:').lower() in page_div.getText() or
       str('Can refer to one of the following:').lower() in page_div.getText()):
        options = parse_options(page_div)
        return options

    if str('/Quick guide') in page_div.getText():
        page_hyperlink = page_content.find(
            'link', rel='canonical').attrs['href']
        description = parse_quick_guide(page_div, page_hyperlink)

    if str('/Level_up_table') in page_content.find(
        'link', rel='canonical'
    ).attrs['href']:
        description = parse_levelup_table(page_div)

    if len(description) < 34 or description is None:
        raise exceptions.StubArticle
        # No description(s) over 36 characters nullifies article and returns
        # StubArticle error.

    return [description]


def parse_infobox(page_content: BeautifulSoup) -> dict:
    '''
    Parser function which parses an infobox from an
    Old School RuneScape wikipedia page into a dictionary.
    An infobox includes various properties about an asset -
    such as release date, value (price), tradability etc.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.

    :return: (Dictionary) -
        A dictionary containing the parsed infobox properties
        and their values.
    '''

    infobox = {}
    infobox_content = page_content.find_all('table', class_='infobox')

    if infobox_content:
        for tab in infobox_content:
            for row in tab.find_all('tr'):
                try:
                    property_name = row.find(
                        'th').getText().rstrip('\n').strip()
                    property_value = row.find('td').getText().replace(
                        '(info)',
                        '').replace(
                        '(Update)',
                        '').replace(
                        '[1]',
                        '').replace(
                        '[2]',
                        '').replace(
                        '[3]',
                        '').rstrip('\n').strip()
                    if property_name in ('Icon', 'Minimap icon'):
                        property_value = row.find('img')['src']
                        continue
                    infobox.update({property_name: property_value})
                except AttributeError:
                    try:
                        property_name = 'Image'
                        property_value = row.find(
                            'td',
                            class_='infobox-image infobox-full-width-content'
                        ).find('img')['src']
                        infobox.update({property_name: property_value})
                    except AttributeError:
                        pass
                    except TypeError:
                        pass
    return infobox


def parse_minigame_icon(page_content, search_query: str) -> Optional[str]:
    '''
    Parser function which parses a minigame icon from
    'https://oldschool.runescape.wiki/w/Minigames'.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.
    :param search_query: (String) -
        Represents the search query given by the user. (Ex: 'firecape'.)

    :return: (Optional[String]) -
        The URL of the minigame icon, or None if no matching icon was found.
    '''

    for table in page_content.find_all('table', class_='wikitable'):
        for icon in table.find_all('img'):
            if search_query.lower() in slugify(icon['alt']).lower():
                icon_url = icon['src']
                return f'https://oldschool.runescape.wiki{icon_url}'


def parse_options(page_div: BeautifulSoup) -> List[str]:
    '''
    Parser function which parses a list of options for queries
    that may refer to several articles.

    :param page_div: (BeautifulSoup object) -
        Represents a div as a nested data structure.

    :return: (List[String]) -
        A list of the parsed options for the query.
    '''

    options = []
    for item in page_div.find_all('ul'):
        for link in item.find_all('a'):
            try:
                # Prevents external RuneScape 3 options (404s).
                if not str('rsw') in link.attrs['title']:
                    options.append(link.attrs['title'])
            except KeyError:
                pass
    if len(options) == 0:
        for item in page_div.find('table').find_all('td'):
            for link in item.find_all('a'):
                options.append(link.attrs['title'])
    sorted_options = list(dict.fromkeys(options))[:25]
    return sorted_options


def parse_levelup_table(page_div: BeautifulSoup) -> str:
    '''
    Parser function which parses a level up table from a table page
    (still in development.)

    :param page_div: (BeautifulSoup object) -
        Represents a div as a nested data structure.

    :return: (String) -
        A string containing information about the level up table page.
    '''

    levelup_details = [
        ('This is a level up table page. \
          To view more information about this page, click the button below.')
    ]
    _ = page_div
    # Do more stuff later...

    return ''.join(levelup_details)


def parse_price_data(url: str, headers: dict) -> dict:
    '''
    Parser function which parses price data using the official API.

    :param url: (String) -
        Represents the full URL with an item_id.
    :param headers: (Dictionary) -
        Represents a series of request headers.

    :return: (Dictionary) -
        A dictionary containing the parsed price data.
    '''

    try:
        request = requests.get(url, headers=headers, timeout=60)
        data = request.json()
    except BaseException as exc:
        raise exceptions.NoPriceData from exc
    return data


def parse_quest_details(page_content: BeautifulSoup) -> dict:
    '''
    Parser function which parses quest details from an
    Old School RuneScape quest page. This will always pass
    a page with quest details, so won't fail.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.

    :return: (Dictionary) -
        A dictionary containing the parsed quest details.
    '''

    detail_table = page_content.find(
        'table', class_='questdetails').find_all('tr')
    quest_details = {}
    for row in detail_table:
        property_name = row.find('th').getText()
        property_value = row.find('td').getText()
        quest_details.update({property_name: property_value})
        continue
    return quest_details


def parse_quick_guide(page_content: BeautifulSoup, page_hyperlink: str) -> str:
    '''
    Parser function which parses quick guide details from a
    guide page

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.
    :param page_hyperlink: (String) -
        Represents the URL of the page.

    :return: (String) -
        A string containing the parsed quick guide for the page.
    '''

    quickguide_details = [
        'This is a quick guide page. Use the links below to display \
         more information about each section:\n\n']
    count = 1
    for header in page_content.find_all('span', class_='mw-headline'):
        quickguide_details.append(
            (
                f'Part {count}: '
                f'[{header.getText()}]({page_hyperlink}'
                f'#{header.getText().replace(" ", "_")})\n'
            )
        )
        count += 1
    return ''.join(quickguide_details)


def parse_thumbnail(page_content) -> Optional[str]:
    '''
    Parser function which parses a thumbnail URL from an
    Old School RuneScape wikipedia page.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.

    :return: (Optional[str]) -
        The URL of the thumbnail image,
        or None if no thumbnail was found.
    '''

    try:

    #    img_src = page_content.find(
    #        'div', class_='floatleft').find(
    #        'a', class_='image').find('img').attrs['src']
    #   thumbnail_url = f'https://oldschool.runescape.wiki/{img_src}'

        img_src = page_content.find(
            'figure', class_='mw-halign-left').find('img').attrs['src']
        thumbnail_url = f'https://oldschool.runescape.wiki/{img_src}'

    except AttributeError:
        thumbnail_url = None
    return thumbnail_url


def parse_title(page_content: BeautifulSoup) -> str:
    '''
    Parser function which parses a title from an
    Old School RuneScape wikipedia page.

    :param page_content: (BeautifulSoup object) -
        Represents the document as a nested data structure.

    :return: (String) -
        The title of the page.
    '''

    page_title = page_content.find('h1', class_='firstHeading').string
    return page_title


async def generate_graph(data: dict) -> str:
    '''
    Generates a graph with given api price data.

    :param data: (Dictionary) -
        Represents a dictionary of price data.

    :return: (String) -
        The filename of the generated graph.
    '''

    prices = data['daily'].values()
    average = data['average'].values()
    filename = str(uuid.uuid4())

    plotter.rcParams['ytick.color'] = 'lightslategrey'
    plotter.rcParams['figure.figsize'] = 8, 3
    plotter.box(on=None)
    plotter.yticks(
        [
            max(prices),
            sum(prices) / len(prices),
            min(prices)
        ],
        [
            normalise_price(max(prices)),
            normalise_price(sum(prices) / len(prices)),
            normalise_price(min(prices))
        ]
    )
    plotter.xticks([])
    plotter.axhline(y=sum(prices) / len(prices), dashes=[1, 3])
    plotter.plot(average, color='#5865F2')
    plotter.plot(prices, color='lightslategrey')
    plotter.title('Past 180 Days', loc='right', color='lightslategrey')
    plotter.savefig(f'assets/{filename}', transparent=True)
    plotter.close()
    return f'{filename}.png'


def parse_hiscores(
    url: str,
    headers: dict,
    hiscores_order: list,
    usernames: list
) -> dict:
    '''
    Parser function which parses values from the official
    OSRS Hiscores API

    :param url: (String) -
        Represents the full URL with an item_id.
    :param headers: (Dictionary) -
        Represents a series of request headers.
    :param hiscores_order: (List) -
        Represents a list of the hiscores in order (from 'config.py').
    :param usernames: (List) -
        Represents a list of usernames.

    :return: (Dictionary) -
        A dictionary containing the parsed hiscores data
        for the given usernames.
    '''

    responses = []
    for user in usernames:
        request = requests.get(f'{url}{user}', headers=headers, timeout=60)
        player_info = request.text[:-1]
        responses.append(player_info.split('\n'))
    for resp in responses:
        hiscore_data =(
            {hiscores_order[i]: resp[i] for i in range(len(hiscores_order))}
        )
    return hiscore_data
