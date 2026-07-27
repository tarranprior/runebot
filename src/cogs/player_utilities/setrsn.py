#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `setrsn`
command, allowing users to save a RuneScape username for their
Discord account.

Classes:
    - `Setrsn`:
            A class for handling the `setrsn` command.

Key Functions:
    - `set_username(...)`, `setrsn(...)`:
            Functions for setting a RuneScape username, as well as
            creating a slash command and autocomplete query for the `setrsn`
            command.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `setrsn` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, Option, OptionType

import time
import uuid

import exceptions
from templates.bot import Bot
from config import *
from utils import *
from utils.logging import (
    BoundCommandLogger,
    build_log_message,
    build_command_log_bind,
    elapsed_ms,
)


class Setrsn(commands.Cog, name='setrsn'):
    '''
    A class which represents the Setrsn cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises the Setrsn cog.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        return: (None)
        '''
        self.bot = bot
        self._setrsn_log = BoundCommandLogger(self._setrsn_bind)


    @staticmethod
    def _invocation_source(inter: ApplicationCommandInteraction) -> str:
        return 'slash_command'


    def _setrsn_bind(
        self,
        inter: ApplicationCommandInteraction,
        *,
        action: str,
        stage: str,
        operation: str = 'set',
        invocation_mode: str | None = None,
        username: str | None = None,
        resolved_username: str | None = None,
        account_type: str | None = None,
        resolved_account_type: str | None = None,
        resolution_source: str | None = None,
        trace_id: str | None = None,
        log_params: list | None = None,
        **extra,
    ) -> dict:
        return build_command_log_bind(
            command='setrsn',
            inter=inter,
            action=action,
            stage=stage,
            operation=operation,
            invocation_source=self._invocation_source(inter),
            trace_id=trace_id,
            log_params=log_params,
            invocation_mode=invocation_mode,
            username=username,
            resolved_username=resolved_username,
            account_type=account_type,
            resolved_account_type=resolved_account_type,
            resolution_source=resolution_source,
            **extra,
        )


    async def set_username(
        self,
        inter: ApplicationCommandInteraction,
        username: str,
        account_type: str = None,
        trace_id: str | None = None,
        started_at: float | None = None,
    ) -> Tuple[disnake.Embed, disnake.ui.View]:
        '''
        Function which takes a provided username and stores it
        with a respective user_id for easy retrieval.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param username: (String) -
            Represents a player's username.
        :param account_type: (String[Optional]) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (Tuple[disnake.Embed, disnake.ui.View])
            An embed and view containing a success message.
        '''

        if len(username) > MAX_CHARS or any(char in username for char in BLACKLIST_CHARS):
            self._setrsn_log.warning(
                inter,
                build_log_message(
                    command='setrsn',
                    stage='failure',
                    operation='set',
                ),
                action='fail',
                stage='failure',
                operation='set',
                invocation_mode='explicit',
                username=username,
                resolved_username=username,
                account_type=account_type or 'Normal',
                resolved_account_type=account_type or 'Normal',
                resolution_source='provided_username',
                log_params=[
                    {'kind': 'username', 'label': 'username', 'value': username},
                    {'kind': 'account_type', 'label': 'account_type', 'value': account_type or 'Normal'},
                ],
                handled=True,
                expected_failure=True,
                user_visible=True,
                trace_id=trace_id,
                exception_type='UsernameInvalid',
                exception_message=str(exceptions.UsernameInvalid()),
                **(
                    {'duration_ms': elapsed_ms(started_at)}
                    if started_at is not None
                    else {}
                ),
            )
            raise exceptions.UsernameInvalid

        if not account_type:
            account_type = 'Normal'

        resolved_username = username
        resolved_account_type = account_type

        self._setrsn_log.info(
            inter,
            build_log_message(
                command='setrsn',
                stage='resolve',
                operation='set',
                subject='username',
                resolved=resolved_username,
            ),
            action='resolve',
            stage='resolve',
            operation='set',
            trace_id=trace_id,
            invocation_mode='explicit',
            username=username,
            resolved_username=resolved_username,
            account_type=account_type,
            resolved_account_type=resolved_account_type,
            resolution_source='provided_username',
            log_params=[
                {'kind': 'username', 'label': 'username', 'value': username},
                {'kind': 'account_type', 'label': 'account_type', 'value': account_type},
            ],
        )

        await add_username(self, inter.author.id, resolved_username, resolved_account_type)

        embed, view = EmbedFactory().create(
            title=f'Account has been set.',
            description=f'Your default account has now been set to **{username}**.\n\n'
            f'You can set a new default at any time by using {SLASH_MENTIONS["setrsn"]}, '
            f'or use the {disnake.PartialEmoji(name="account", id=1482896847239381065)} Account Manager under {SLASH_MENTIONS["stats"]} to manage all of your accounts.',
            button_label='Hiscores',
            button_url=f'{HISCORE_URLS.get(account_type)}{slugify(username)}'
        )
        embed.timestamp = inter.created_at
        embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

        return embed, view


    @commands.slash_command(
        name='setrsn',
        description='Set a RuneScape username for your Discord account.',
        options=[
            Option(
                name='username',
                description='Enter your username.',
                type=OptionType.string,
                required=True
            ),
            Option(
                name='account_type',
                description='Select a default Account Type (optional.)',
                type=OptionType.string,
                required=False
            )
        ]
    )
    async def setrsn(
        self,
        inter: ApplicationCommandInteraction,
        username: str,
        account_type: str = None
    ) -> None:
        '''
        Creates a slash command for the `set_username` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param username: (String) -
            Represents a player's username.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (None)
        '''

        trace_id = uuid.uuid4().hex
        started_at = time.perf_counter()

        self._setrsn_log.info(
            inter,
            build_log_message(
                command='setrsn',
                stage='start',
                operation='set',
                subject='username',
            ),
            action='start',
            stage='start',
            operation='set',
            trace_id=trace_id,
            username=username,
            account_type=account_type or 'Normal',
            invocation_mode='explicit',
            log_params=[
                {'kind': 'username', 'label': 'username', 'value': username},
                {'kind': 'account_type', 'label': 'account_type', 'value': account_type or 'Normal'},
            ],
        )

        try:
            embed, view = await self.set_username(
                inter,
                username,
                account_type,
                trace_id=trace_id,
                started_at=started_at,
            )
            await inter.send(embed=embed, view=view, ephemeral=True)

            self._setrsn_log.success(
                inter,
                build_log_message(
                    command='setrsn',
                    stage='complete',
                    operation='set',
                ),
                action='complete',
                stage='complete',
                operation='set',
                trace_id=trace_id,
                invocation_mode='explicit',
                username=username,
                resolved_username=username,
                account_type=account_type or 'Normal',
                resolved_account_type=account_type or 'Normal',
                resolution_source='provided_username',
                duration_ms=elapsed_ms(started_at),
                log_params=[
                    {'kind': 'username', 'label': 'username', 'value': username},
                    {'kind': 'account_type', 'label': 'account_type', 'value': account_type or 'Normal'},
                ],
            )
        except exceptions.UsernameInvalid:
            raise

        except exceptions.MaximumAccountsReached as exc:
            self._setrsn_log.warning(
                inter,
                build_log_message(
                    command='setrsn',
                    stage='failure',
                    operation='set',
                ),
                action='fail',
                stage='failure',
                operation='set',
                trace_id=trace_id,
                username=username,
                account_type=account_type or 'Normal',
                resolved_account_type=account_type or 'Normal',
                resolution_source='provided_username',
                invocation_mode='explicit',
                log_params=[
                    {'kind': 'username', 'label': 'username', 'value': username},
                    {
                        'kind': 'account_type',
                        'label': 'account_type',
                        'value': account_type or 'Normal',
                    },
                ],
                handled=True,
                expected_failure=True,
                user_visible=True,
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                duration_ms=elapsed_ms(started_at),
            )

            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=str(exc),
                colour=0xB72615,
                button_label='Support Server',
                button_url=SUPPORT_SERVER
            )
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')
            await inter.send(embed=embed, view=view, ephemeral=True)
            return

        except Exception as exc:
            self._setrsn_log.error(
                inter,
                build_log_message(
                    command='setrsn',
                    stage='runtime_failure',
                    operation='set',
                ),
                exc=exc,
                action='fail',
                stage='runtime_failure',
                operation='set',
                trace_id=trace_id,
                username=username,
                invocation_mode='explicit',
                log_params=[
                    {'kind': 'username', 'label': 'username', 'value': username}
                ],
                handled=False,
                expected_failure=False,
                user_visible=False,
                duration_ms=elapsed_ms(started_at),
            )
            raise


    @setrsn.autocomplete('account_type')
    async def account_type_autocomplete(self, account_type: str) -> List[str]:
        '''
        Creates a selection of autocomplete suggestions once the user begins
        typing.

        :param self: -
            Represents this object.
        :param account_type: (String) -
            Represents an account type (Ex: Ironman, 1 Defence etc.)

        :return: (List[String]) -
            A list of autocomplete suggestions.
        '''

        _ = account_type

        return ACCOUNT_TYPES


def setup(bot: Bot) -> None:
    '''
    Defines the bot setup function for the `setrsn` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Setrsn(bot))
