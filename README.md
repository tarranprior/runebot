
<p align="center"><img src="https://github.com/tarranprior/runebot/blob/main/assets/banner.png" /></p>
<h1 align="center">Runebot</h1>

<a href="https://github.com/tarranprior/runebot/releases"><p align="center">![Version](https://img.shields.io/badge/Latest%20Version-v1.0.5-7289da?style=for-the-badge)</a>
<a href="https://www.python.org/downloads/">![Python](https://img.shields.io/badge/made%20with-python%203.8-7289da?style=for-the-badge&logo=python&logoColor=ffdd54)</a>
<a href="https://github.com/tarranprior/runebot/blob/main/LICENSE">![License](https://img.shields.io/badge/license-CC%20BY%20NC%20SA%203.0-7289da?style=for-the-badge)</p></a>
</p>
<p align="center"><a href="#introduction">Introduction</a> • <a href="#key-features">Features</a> • <a href="#prerequisites">Prerequisites</a> • <a href="#tools">Tools</a> • <a href="#disclaimer">Disclaimer</a> • <a href="#installation">Installation</a> • <a href="#usage">Usage</a> • <a href="#support">Support</a> • <a href="#license">License</a>

## Introduction
Runebot is a feature-rich Discord tool which scrapes, pulls and displays information about Old School RuneScape. Built with Python, SQLite and Beautiful Soup 4.

You can try a live instance of this project by [clicking here](https://discord.com/oauth2/authorize?client_id=978953033989914654&permissions=2147764224&scope=bot%20applications.commands) and inviting Runebot to your server.

## Key Features
- Search for items and equipment, activities, bosses and more directly on discord.
- Get the most up to date information - directly from the official api and wiki.
- Full support of slash commands and the latest developer tools.
- Autocomplete suggestions for all applicable interactions.
- Display the latest price analytics and trends with data visualisation.
- Integration of UI/UX components (buttons, dropdowns etc.)

## Prerequisites
- Python 3.8 +
- [Poetry](https://python-poetry.org/docs) (or the [pip](https://pypi.org/project/pip/) package management tool.)

## Tools
- [Disnake API Wrapper](https://github.com/DisnakeDev/disnake)
- [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Color-thief-py](https://github.com/fengsp/color-thief-py)
- [Matplotlib - Data Visualisation](https://matplotlib.org/)
- [aiosqlite](https://pypi.org/project/aiosqlite/)
- [Humanfriendly](https://github.com/xolox/python-humanfriendly)

## Disclaimer
The Old School RuneScape Wiki, also known as the OSRS Wiki and previously known as the 2007Scape Wiki, is the official wiki for the MMORPG game Old School RuneScape developed and published by Jagex Ltd.

RuneScape and RuneScape Old School are the trademarks of Jagex Limited and are used with the permission of Jagex.

## Installation
Preferably, you should use Poetry to run this bot for local development:

1. Clone the repository. `git clone https://github.com/tarranprior/runebot.git`
2. Navigate to the project folder. `cd runebot`
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
2. *Optional*: Update the activity in `config.json`.

   ```json
   {
       "activity": "/wikipedia | RuneBot",
   }
   ```

## Usage

## Support
If you have any questions about this project, please submit an issue [here](https://github.com/tarranprior/runebot/issues).<br/>

## License
This project is licensed under the CC BY-NC-SA 3.0 License - see the [LICENSE](https://github.com/tarranprior/runebot/blob/main/LICENSE) file for details.
