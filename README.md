<h1 align="center">Rotten Soup</h1>

<a href="https://github.com/tarranprior/discord-rotten-soup/releases"><p align="center">![Version](https://img.shields.io/badge/Latest%20Version-v1.0.0-7289da?style=for-the-badge)</a>
<a href="https://www.python.org/downloads/">![Python](https://img.shields.io/badge/made%20with-python%203.8-7289da?style=for-the-badge&logo=python&logoColor=ffdd54)</a>
<a href="https://github.com/tarranprior/discord-rotten-soup/blob/main/LICENSE">![License](https://img.shields.io/badge/license-CC%20BY%20NC%20SA%203.0-7289da?style=for-the-badge)</p></a>
</p>
<p align="center"><a href="#introduction">Introduction</a> • <a href="#key-features">Features</a> • <a href="#prerequisites">Prerequisites</a> • <a href="#tools">Tools</a> • <a href="#disclaimer">Disclaimer</a> • <a href="#installation">Installation</a> • <a href="#usage">Usage</a> • <a href="#support">Support</a> • <a href="#license">License</a> • <a href="#references">References</a></p>

## Introduction
Rotten Soup is a Discord tool which scrapes and displays information about Old School RuneScape. Built with Python and Beautiful Soup 4.

## Key Features
- Search for items and equipment, activities, bosses and more directly on discord.
- Display names, descriptions, images, properties etc. beautifully with embeds.
- Get the most up to date information - directly from the official wiki.
- Full slash command integration.
- User interface components (buttons, dropdowns etc.) for usability.

## Prerequisites
- Python 3.8 +
- The [pip](https://pypi.org/project/pip/) package management tool.

## Tools
- [Disnake API Wrapper](https://github.com/DisnakeDev/disnake)
- [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Color-thief-py](https://github.com/fengsp/color-thief-py)

## Disclaimer
The Old School RuneScape Wiki, also known as the OSRS Wiki and previously known as the 2007Scape Wiki, is the official wiki for the MMORPG game Old School RuneScape developed and published by Jagex Ltd.

RuneScape and RuneScape Old School are the trademarks of Jagex Limited and are used with the permission of Jagex.

## Installation
Preferably, you should use Poetry to run this bot for local development:

1. Clone the repository. `git clone https://github.com/tarranprior/discord-rotten-soup.git`
2. Navigate to the project folder. `cd discord-rotten-soup`
3. Install the dependencies:

    ```s
    poetry install
    ```

    Alternatively, you can install the dependencies using pip:
    
    ```s
    pip install -r requirements.txt
    ```

## Setup
1. Create an application at [Discord Developer Portal](https://discord.com/developers/applications). Build a bot, and copy the token.
2. Invite the bot to your server/guild.
3. Update the values in [configuration](#configuration).
4. Run the bot:

    ```s
    poetry run python src/main.py
    ```

## Configuration
1. Update the values in `.env.EXAMPLE` and rename to `.env`.

   ```s
   BOT_TOKEN = 'YOUR_BOT_TOKEN'
   BOT_OWNER = 'YOUR_USER_ID'
   ```
2. *Optional*: Update the activity (bot status) and/or prefix in `config.json`.

   ```json
   {
       "activity": "Old School RuneScape",
       "prefix": "!"
   }
   ```

## Usage

🍲 Rotten Soup
- `alch` - Fetches alch price data (low alch/high alch) from the official Old School RuneScape wikipedia.
- `examine` - Fetch the examine text from the official Old School RuneScape wikipedia.
- `price` - Fetch guide price data from the official Old School RuneScape wikipedia.
- `wiki` - Look up an entry from the official Old School RuneScape wikipedia.

## Screenshots
<img src="https://i.imgur.com/6TVvpeB.png" />
<img src="https://i.imgur.com/mg2kI6x.png" />
<img src="https://i.imgur.com/FUby7Y3.png" />

## Support
If you have any questions about this template, please submit an issue [here](https://github.com/linuxiso/rotten-soup/issues).<br/>

## License
This project is licensed under the CC BY-NC-SA 3.0 License - see the [LICENSE](https://github.com/linuxiso/rotten-soup/blob/main/LICENSE) file for details.

## References
- Beautiful Soup Docs https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Disnake Docs https://docs.disnake.dev/en/latest/index.html
- Discord Developer Applications https://discord.com/developers/applications
- Old School RuneScape Wiki https://oldschool.runescape.wiki/