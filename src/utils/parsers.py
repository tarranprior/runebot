import requests
import matplotlib.pyplot as plotter
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen

import exceptions
from config import *
from utils.general import *


'''
Parses all attributes (title, description, thumbnail etc.) from an Old School RuneScape wikipedia page
and returns a dictionary.

:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
'''
def parse_all(page_content):
    page_title = parse_title(page_content)
    page_description = parse_description(page_content)
    page_thumbnail = parse_thumbnail(page_content)
    
    if len(page_description) == 1:
        infobox = parse_infobox(page_content)
        return({'title': page_title, 'description': page_description, 'infobox': infobox, 'options': False, 'thumbnail_url': page_thumbnail})
    
    options = page_description
    return({'title': page_title, 'description': False, 'infobox': False, 'options': options, 'thumbnail_url': page_thumbnail})

'''
Parses all page content from an Old School RuneScape wikipedia page.

:param url: (String) - Represents the base URL.
:param query: (String) - Represents the search query. Ex: Firecape.
:param headers: (Dictionary) - Represents a series of request headers.
'''
def parse_page(url: str, query: str, headers: dict) -> None:
    try:
        request = Request(f'{url}{query}', headers=headers)
        page = urlopen(request)
        page_content = BeautifulSoup(page, 'html.parser')
    except HTTPError:
        raise exceptions.Nonexistence
    return(page_content)

'''
Parses a description from an Old School RuneScape wikipedia page.

:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
:param query: (String) - Represents the query given by the user. (Ex: 'firecape'.)
'''
def parse_description(page_content) -> None:
    page_div = page_content.find('div', class_='mw-parser-output')
    
    if str('May refer to').lower() in page_div.getText():
        options = parse_options(page_div)
        return(options)
    
    for paragraph in page_content.find_all('p'):
        description = paragraph.getText().replace('[1]', '')
        if not len(description) < 56:
            break

    if len(description) < 56 or description == None:
        raise exceptions.Nonexistence
    
    return([description])

'''
Parses an infobox from an Old School RuneScape wikipedia page into a dictionary.
An infobox includes various properties about an asset - such as release date, value (price), tradability etc.

:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
'''
def parse_infobox(page_content) -> None:
    infobox = {}
    infobox_content = page_content.find('table', class_='infobox')

    if infobox_content:
        for row in infobox_content.find_all('tr'):
            try:
                property_name = row.find('th').getText().rstrip('\n').strip()
                property_value = row.find('td').getText().replace('(info)', '').replace('(Update)', '').replace('[1]', '').rstrip('\n').strip()
                if property_name == 'Icon':
                    property_value = row.find('img')['src']
                    continue
                infobox.update({property_name: property_value})
            except AttributeError:
                try:
                    property_name = 'Image'
                    property_value = row.find('td', class_="infobox-image infobox-full-width-content").find('img')['src']
                    infobox.update({property_name: property_value})
                except AttributeError:
                    pass
                pass

    return(infobox)

'''
Parses a minigame icon from 'https://oldschool.runescape.wiki/w/Minigames'.
:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
'''
def parse_minigame_icon(page_content, query: str) -> None:
    for table in page_content.find_all('table', class_='wikitable'):
        for icon in table.find_all('img'):
            if query in search_query(icon['alt']):
                icon_url = icon['src']
                return(f'https://oldschool.runescape.wiki{icon_url}')

'''
Parses a list of options for queries that may refer to several articles.
:param page_div: (BeautifulSoup object) Represents a div as a nested data structure.
'''
def parse_options(page_div) -> None:
    options = []

    for item in page_div.find_all('ul'):
        for link in item.find_all('a'):
            options.append(link.attrs['title'])
    sorted_options = list(dict.fromkeys(options))[:25]

    return(sorted_options)

'''
Parses price data using the official API.
:param url: (String) - Represents the full URL with an item_id.
:param headers: (Dictionary) - Represents a series of request headers.
'''
def parse_price_data(url, headers) -> None:
    try:
        request = requests.get(url, headers=headers)
        data = request.json()
    except:
        raise exceptions.NoPriceData
    return(data)

'''
Parses quest details from an Old School RuneScape quest page.
This will always pass a page with quest details, so won't fail.

:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
'''
def parse_quest_details(page_content) -> None:
    detail_table = page_content.find('table', class_='questdetails').find_all('tr')
    quest_details = {}
    for row in detail_table:
        property_name = row.find('th').getText()
        property_value = row.find('td').getText()
        quest_details.update({property_name: property_value})
        continue
    return(quest_details)

'''
Parses a thumbnail URL from an Old School RuneScape wikipedia page.
:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
'''
def parse_thumbnail(page_content) -> None:
    try:
        img_src = page_content.find('div', class_='floatleft').find('a', class_='image').find('img').attrs['src']
        thumbnail_url = f'https://oldschool.runescape.wiki/{img_src}'
    except:
        thumbnail_url = None
    return(thumbnail_url)

'''
Parses a title from an Old School RuneScape wikipedia page.
:param page_content: (BeautifulSoup object) - Represents the document as a nested data structure.
'''
def parse_title(page_content) -> None:
    page_title = page_content.find('h1', class_='firstHeading').string
    return(page_title)

'''
Generates a graph with given api price data.
:param data: (Dictionary) - Represents a dictionary of price data.
'''
def generate_graph(data) -> None:

    prices = data['daily'].values()
    average = data['average'].values()

    plotter.rcParams['ytick.color'] = 'lightslategrey'
    plotter.rcParams['figure.figsize'] = 8, 3
    plotter.box(on=None)
    plotter.yticks(
        [
            max(prices),
            sum(prices)/len(prices),
            min(prices)
        ],
        [
            normalise_price(max(prices)),
            normalise_price(sum(prices)/len(prices)),
            normalise_price(min(prices))
        ]
    )
    plotter.xticks([])
    plotter.axhline(y=sum(prices)/len(prices), dashes=[1, 3])
    plotter.plot(average, color='#5865F2')
    plotter.plot(prices, color='lightslategrey')
    plotter.title('Past 180 Days', loc='right', color='lightslategrey')
    plotter.savefig('assets/apigraph.png', transparent=True)
    plotter.close()