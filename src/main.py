#! /usr/bin/env python3

'''
This module contains the main entry point for the bot.
For more information about each cog and its usage, refer to the docstrings
in the respective module.

Usage:
    poetry run python src/main.py --env development
    poetry run python src/main.py --env production
'''

import argparse
import sys
import disnake
from loguru import logger

from settings import load_settings
from templates.bot import Bot
from utils.helpers import configuration
from utils.internal_api import InternalStatsAPIServer
from utils.log_api_sink import start_log_api_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--env',
        default='development',
        choices=('development', 'production'),
        help='Runtime environment: development or production'
    )
    return parser.parse_args()


def configure_logging() -> None:
    logger.remove()
    logger.add(sys.stderr, level='INFO', backtrace=False, diagnose=False)


def main() -> None:
    args = parse_args()
    configure_logging()
    settings = load_settings(args.env)
    
    log_pipeline = start_log_api_pipeline(
        host=settings.internal_api_host,
        port=settings.internal_api_port,
        token=settings.internal_api_token,
        logs_db_path=settings.internal_logs_db_path,
    )

    config = configuration()
    bot = Bot(
        config=config,
        db_path=settings.db_path,
        activity=disnake.Game(
            name=f"{config['configuration']['activity']}"
        )
    )
    setattr(bot, 'log_pipeline', log_pipeline)

    bot.load_extensions(exts=[
        'cogs.administrator.ping',
        'cogs.player_utilities.setrsn',
        'cogs.player_utilities.stats',
        'cogs.search_tools.alchemy',
        'cogs.search_tools.bestiary',
        'cogs.search_tools.minigames',
        'cogs.search_tools.price',
        'cogs.search_tools.quests',
        'cogs.search_tools.wikipedia'
    ])

    internal_api = InternalStatsAPIServer(
        bot=bot,
        token=settings.internal_api_token,
        host=settings.internal_api_host,
        port=settings.internal_api_port,
        logs_db_path=settings.internal_logs_db_path,
        log_pipeline=log_pipeline
    )
    internal_api.start()

    bot.run(settings.bot_token)


if __name__ == '__main__':
    main()
