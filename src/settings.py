#! /usr/bin/env python3

'''
Runtime settings and secrets loader for Runebot.

Runtime mode is selected by CLI and passed into load_settings():
    - "development" (default): values come from environment variables / .env.
    - "production": values come from AWS Secrets Manager secrets.

Environment variables consumed by this module:
    RUNEBOT_AWS_REGION                  - AWS region for Secrets Manager
                                          (default: "eu-north-1")
    RUNEBOT_AWS_BOT_TOKEN_SECRET_NAME   - AWS secret name for bot token
                                          (default: "bot_token")
    RUNEBOT_AWS_DB_PATH_SECRET_NAME     - AWS secret name for database path
                                          (default: "db_path")

    Development only (env / .env):
    BOT_TOKEN                   - Discord bot token
    RUNEBOT_INTERNAL_API_TOKEN  - Bearer token for the internal stats API
                                  (default: "")
    RUNEBOT_INTERNAL_API_HOST   - Host for the internal stats API
                                  (default: "127.0.0.1")
    RUNEBOT_INTERNAL_API_PORT   - Port for the internal stats API
                                  (default: 8080)
    DB_PATH                     - SQLite database path
                                  (default: "runebot.db")

Production only (AWS Secrets Manager):
    bot_token secret            - SecretString is the Discord bot token
    db_path secret              - SecretString is the SQLite database path

Exported names:
    RuntimeSettings
    load_settings(runtime_env="development")

Usage examples:
    poetry run python src/main.py --env development
    poetry run python src/main.py --env production
'''

from dataclasses import dataclass
from os import environ as env
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from loguru import logger


@dataclass
class RuntimeSettings:
    bot_token: str
    internal_api_token: str
    internal_api_host: str
    internal_api_port: int
    db_path: str


def _fetch_aws_secret(secret_name: str) -> str:
    '''
    Fetches a single secret value from AWS Secrets Manager and returns
    its SecretString as a plain string.
    '''

    region_name: str = env.get('RUNEBOT_AWS_REGION', 'eu-north-1')

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = response['SecretString']
    except ClientError as e:
        raise e

    return secret


def _coerce_port(value: str, fallback: int = 8080) -> int:
    try:
        port = int(value)
        if port < 1 or port > 65535:
            raise ValueError
        return port
    except ValueError:
        logger.warning(
            'Invalid RUNEBOT_INTERNAL_API_PORT value. Falling back to {}.'.format(fallback)
        )
        return fallback


def load_settings(runtime_env: str = 'development') -> RuntimeSettings:
    normalized_env = runtime_env.strip().lower()

    if normalized_env not in ('development', 'production'):
        raise ValueError(
            'Invalid runtime environment: {}. Use "development" or "production".'.format(runtime_env)
        )

    if normalized_env == 'development':
        load_dotenv()

        bot_token = env.get('BOT_TOKEN')
        internal_api_token = env.get('RUNEBOT_INTERNAL_API_TOKEN', '')
        internal_api_host = env.get('RUNEBOT_INTERNAL_API_HOST', '127.0.0.1')
        internal_api_port = _coerce_port(env.get('RUNEBOT_INTERNAL_API_PORT', '8080'))
        db_path = env.get('DB_PATH', 'runebot.db')

    else:
        bot_token_secret_name = env.get('RUNEBOT_AWS_BOT_TOKEN_SECRET_NAME', 'bot_token')
        db_path_secret_name = env.get('RUNEBOT_AWS_DB_PATH_SECRET_NAME', 'db_path')

        bot_token_secret = _fetch_aws_secret(bot_token_secret_name)
        bot_token_data = json.loads(bot_token_secret)
        bot_token = bot_token_data.get('BOT_TOKEN')

        db_path = _fetch_aws_secret(db_path_secret_name)

        internal_api_token = ''
        internal_api_host = '127.0.0.1'
        internal_api_port = 8080

    if not bot_token:
        raise ValueError(
            'BOT_TOKEN is required for runtime environment: {}.'.format(normalized_env)
        )

    if not db_path:
        raise ValueError(
            'DB_PATH is required for runtime environment: {}.'.format(normalized_env)
        )

    return RuntimeSettings(
        bot_token=bot_token,
        internal_api_token=internal_api_token,
        internal_api_host=internal_api_host,
        internal_api_port=internal_api_port,
        db_path=db_path
    )