#! /usr/bin/env python3

'''
This module contains the functionality and logic for the `wikipedia`
command, allowing users to search for general article information from
the official Old School RuneScape wikipedia.

Classes:
    - `Wikipedia`:
            A class for handling the `wikipedia` command.
    - `Dropdown`:
            A class for creating dropdown options that can be added
            to a `DropdownView` instance.
    - `DropdownView`:
            A view class for creating dropdowns in the response.

Key Functions:
    - `search_wikipedia(...)`, `wikipedia(...)`, and
      `search_query_autocomplete(...)`:
            Functions for searching for and retrieving Wikipedia articles,
            as well as creating a slash command and autocomplete query for
            the `wikipedia` command.
    - `callback(self, inter: disnake.MessageInteraction)`:
            A callback function for dropdown selection.
    - `setup(bot: Bot)`:
            A function for defining the bot setup for the `wikipedia` command.

Each class and function has an associated docstring, providing details
about its functionality, parameters, and return values.

For more information about each function and its usage, refer to the
docstrings.
'''

import disnake
import uuid

from disnake.ext import commands
from disnake import ApplicationCommandInteraction, MessageInteraction, Option, OptionType
from loguru import logger
from utils.logging import build_log_message

import exceptions
from config import *
from templates.bot import Bot
from utils import *


class Wikipedia(commands.Cog, name='wikipedia'):
    '''
    A class which represents the Wikipedia cog.
    '''

    def __init__(self, bot: Bot) -> None:
        '''
        Initialises a new instance of the Wikipedia class.

        :param self: -
            Represents this object.
        :param bot: (Bot) -
            An instance of the Bot class.

        :return: (None)
        '''

        self.bot = bot


    @staticmethod
    def _invocation_source(
        inter: ApplicationCommandInteraction | disnake.MessageInteraction
    ) -> str:
        return (
            'component_callback'
            if isinstance(inter, disnake.MessageInteraction)
            else 'slash_command'
        )


    def _wiki_bind(
        self,
        inter: ApplicationCommandInteraction | disnake.MessageInteraction,
        *,
        action: str,
        stage: str,
        operation: str = 'search',
        invocation_mode: str | None = None,
        search_query: str | None = None,
        resolved_search_term: str | None = None,
        resolved_page_title: str | None = None,
        resolution_source: str | None = None,
        trace_id: str | None = None,
        log_params: list | None = None,
        **extra,
    ) -> dict:
        payload = {
            'command': 'wikipedia',
            'trace_id': trace_id,
            'invocation_source': self._invocation_source(inter),
            'action': action,
            'stage': stage,
            'operation': operation,
            'invocation_mode': invocation_mode,
            'search_query': search_query,
            'resolved_search_term': resolved_search_term,
            'resolved_page_title': resolved_page_title,
            'resolution_source': resolution_source,
            'log_params': log_params,
            **self._interaction_context(inter),
            **extra,
        }
        return {k: v for k, v in payload.items() if v is not None}


    def _log_wiki_debug(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        logger.bind(**self._wiki_bind(inter, **bind_kwargs)).debug(message)


    def _log_wiki_info(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        logger.bind(**self._wiki_bind(inter, **bind_kwargs)).info(message)


    def _log_wiki_warning(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        logger.bind(**self._wiki_bind(inter, **bind_kwargs)).warning(message)


    def _log_wiki_success(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        message: str,
        **bind_kwargs,
    ) -> None:
        logger.bind(**self._wiki_bind(inter, **bind_kwargs)).success(message)


    def _log_wiki_error(
        self,
        inter: ApplicationCommandInteraction | MessageInteraction,
        message: str,
        exc: Exception,
        **bind_kwargs,
    ) -> None:
        logger.bind(**self._wiki_bind(inter, **bind_kwargs)).opt(exception=exc).error(message)


    @staticmethod
    def _snowflake(value) -> 'str | None':
        return str(value) if value is not None else None


    @staticmethod
    def _interaction_context(
        inter: ApplicationCommandInteraction | disnake.MessageInteraction
    ) -> dict:
        user = getattr(inter, 'author', None) or getattr(inter, 'user', None)
        return {
            'user_id': Wikipedia._snowflake(getattr(user, 'id', None)),
            'user_name': getattr(user, 'name', None),
            'user_display_name': getattr(user, 'display_name', None),
            'guild_id': Wikipedia._snowflake(getattr(inter, 'guild_id', None)),
            'channel_id': Wikipedia._snowflake(getattr(inter, 'channel_id', None)),
            'interaction_type': str(getattr(inter, 'type', None)),
        }


    async def search_wikipedia(
        self,
        inter: ApplicationCommandInteraction | disnake.MessageInteraction,
        search_query: str,
        trace_id: str | None = None,
    ) -> Tuple[disnake.Embed, disnake.ui.View, str, str]:
        '''
        Primary function for the `wikipedia` command which takes a search
        query and returns corresponding data.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction | disnake.MessageInteraction) -
            Represents an interaction with an application command or component callback.
        :param search_query: (String) -
            Represents a search query.

        :return: Tuple[disnake.Embed, disnake.ui.View, str, str] -
            An embed, view, resolved search term, and resolved page title.
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        original_query = search_query
        resolved_search_term = FEELING_LUCKY if invocation_mode == 'feeling_lucky' else search_query
        resolution_source = 'wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query'

        try:
            page_content = parse_page(BASE_URL, resolved_search_term, HEADERS, trace_id=trace_id)
            attributes = parse_all(page_content)
            title = attributes['title']
            resolved_search_term = title
            description = attributes['description']
            infobox = attributes['infobox']
            options = attributes['options']
            thumbnail_url = attributes['thumbnail_url']

            self._log_wiki_info(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='resolve',
                    operation='search',
                    subject='search_query',
                    resolved=title,
                ),
                action='resolve',
                stage='resolve',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': original_query,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': title,
                    },
                    {
                        'kind': 'resolver_input',
                        'label': 'resolver_input',
                        'value': FEELING_LUCKY if invocation_mode == 'feeling_lucky' else resolved_search_term,
                    },
                ],
            )

            normalized_query = search_query.rstrip('/')
            if 'Money making guide/' in normalized_query:
                button_url = f'{BASE_URL}Money_making_guide/{slugify(title)}'
            else:
                button_url = f'{BASE_URL}{slugify(title)}'

            colour = disnake.Colour.from_rgb(
                *await extract_colour(
                    self,
                    inter.guild_id,
                    inter.guild.owner_id,
                    thumbnail_url,
                    HEADERS
                )
            )

            if description:
                embed, view = EmbedFactory().create(
                    title=title,
                    description=description.pop(),
                    colour=colour, infobox=infobox,
                    thumbnail_url=thumbnail_url,
                    button_url=button_url
                )
                embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

                if len(embed.description) < 84:
                    embed.set_footer(
                        text=(f'To view more information about this page, click the button below.\nRunebot {DISPLAY_VERSION}')
                    )
                return embed, view, resolved_search_term, title

            self._log_wiki_debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='start',
                    operation='disambiguation',
                    subject='dropdown',
                ),
                action='start',
                stage='start',
                operation='disambiguation',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=title,
                invocation_mode=invocation_mode,
                log_params=[
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': title,
                    },
                    {
                        'kind': 'options_count',
                        'label': 'options_count',
                        'value': len(options) if options is not None else 0,
                    },
                ],
            )

            embed = EmbedFactory().create(
                title=title,
                description=(
                    f'{title} may refer to several articles. Use the dropdown below to select an option.'
                )
            )

            view = DropdownView(options, self, trace_id=trace_id)
            return embed, view, resolved_search_term, title

        except (exceptions.Nonexistence, exceptions.StubArticle, exceptions.WikiRequestFailed) as exc:
            self._log_wiki_warning(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='failure',
                    operation='search',
                ),
                action='fail',
                stage='failure',
                trace_id=trace_id,
                search_query=original_query,
                resolved_search_term=resolved_search_term,
                resolution_source=resolution_source,
                invocation_mode=invocation_mode,
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': original_query,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                ],
                exception_type=type(exc).__name__,
                exception=str(exc),
                handled=True,
                expected_failure=True,
                user_visible=True,
            )
            raise
        except Exception:
            raise


    @commands.slash_command(
        name='wikipedia',
        description='Search for an article from the official OldSchool RuneScape wikipedia.',
        options=[
            Option(
                name='search_query',
                description='Search for an article. Start typing for suggestions or hit `I\'m feeling lucky` for a random page!',
                type=OptionType.string,
                required=True
            ),
        ],
    )
    async def wikipedia(
        self,
        inter: disnake.ApplicationCommandInteraction,
        *,
        search_query: str
    ) -> None:
        '''
        Creates a slash command for the `search_wikipedia` function.

        :param self: -
            Represents this object.
        :param inter: (ApplicationCommandInteraction) -
            Represents an interaction with an application command.
        :param search_query: (String) -
            Represents a search query.

        :return: (None)
        '''

        invocation_mode = 'feeling_lucky' if search_query == 'I\'m feeling lucky\u200a' else 'explicit'
        resolved_search_term = FEELING_LUCKY if invocation_mode == 'feeling_lucky' else search_query
        trace_id = uuid.uuid4().hex

        self._log_wiki_info(
            inter,
            build_log_message(
                command='wikipedia',
                stage='start',
                operation='search',
            ),
            action='start',
            stage='start',
            operation='search',
            search_query=search_query,
            invocation_mode=invocation_mode,
            resolution_source='wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query',
            trace_id=trace_id,
            log_params=[
                {
                    'kind': 'query',
                    'label': 'search_query',
                    'value': search_query,
                }
            ],
        )

        try:
            await inter.response.defer()
            embed, view, resolved_search_term, resolved_page_title = await self.search_wikipedia(
                inter, search_query, trace_id=trace_id
            )
            await inter.followup.send(embed=embed, view=view)

            self._log_wiki_success(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='complete',
                    operation='search',
                ),
                action='complete',
                stage='complete',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                resolved_page_title=resolved_page_title,
                invocation_mode=invocation_mode,
                resolution_source='wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query',
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': search_query,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': resolved_page_title,
                    },
                ],
            )

        except (exceptions.Nonexistence, exceptions.StubArticle, exceptions.WikiRequestFailed) as exc:
            expected_description = str(exc)

            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=expected_description,
                thumbnail_url=GRAYSCALE_THUMBNAILS['filler'],
                colour=0x8B8B8B,
                button_label='Support Server',
                button_url=SUPPORT_SERVER
            )
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

            if inter.response.is_done():
                await inter.followup.send(embed=embed, view=view)
            else:
                await inter.response.send_message(embed=embed, view=view)
            return

        except Exception as exc:
            self._log_wiki_error(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='runtime_failure',
                    operation='search',
                ),
                exc,
                action='fail',
                stage='runtime_failure',
                operation='search',
                trace_id=trace_id,
                search_query=search_query,
                resolved_search_term=resolved_search_term,
                invocation_mode=invocation_mode,
                resolution_source='wiki_special_random' if invocation_mode == 'feeling_lucky' else 'user_query',
                handled=True,
                expected_failure=False,
                user_visible=True,
            )

            if inter.response.is_done():
                await inter.followup.send(
                    'Something went wrong while handling that request.',
                    ephemeral=True,
                )
            else:
                await inter.response.send_message(
                    'Something went wrong while handling that request.',
                    ephemeral=True,
                )
            return


    @wikipedia.autocomplete('search_query')
    async def search_query_autocomplete(self, search_query: str) -> (Union[List[str], str]):
        '''
        Creates a selection of autocomplete suggestions once the user begins
        typing.

        :param self: -
            Represents this object.
        :param search_query: (String) -
            Represents a search query.

        :return: (Union[List[String], String]) -
            A list of possible autocomplete suggestions,
            or "I'm feeling lucky".
        '''

        autocomplete_suggestions = await get_wikipedia_suggestions(self)

        if len(search_query) > 0:
            return [f'{a}\u200a' for a in autocomplete_suggestions if search_query.lower() in a.lower()][:25]
        return ['I\'m feeling lucky\u200a']


class Dropdown(disnake.ui.StringSelect):
    '''
    A class which contains logic for the dropdown options (Select Menu)
    that can be added to a `DropdownView` instance.
    '''

    def __init__(self, options: list, cog, trace_id: str | None = None) -> None:
        '''
        Initialises a new instance of the Dropdown class.

        :param options: (List) -
            A list of dropdown options.
        :param cog: -
            The Wikipedia cog instance.
        
        :return: (None)
        '''

        self.bot = Bot
        self._cog = cog
        self.trace_id = trace_id
        options = options

        super().__init__(
            placeholder='Select an option...',
            min_values=1,
            max_values=1,
            options=options,
        )


    async def callback(self, inter: disnake.MessageInteraction):
        '''
        The callback function for dropdown selection (Select Menu.)

        :param self: -
            Represents this object.
        :param inter: (disnake.MessageInteraction) -
            Represents a message component interaction triggered by the dropdown.

        :return: (None)
        '''

        selected_value = self.values[0] if self.values else None

        self._cog._log_wiki_debug(
            inter,
            build_log_message(
                command='wikipedia',
                stage='start',
                operation='search',
            ),
            action='start',
            stage='start',
            operation='search',
            trace_id=self.trace_id,
            invocation_mode='dropdown_selection',
            search_query=selected_value,
            component_type='dropdown',
            selected_value=selected_value,
            log_params=[
                {
                    'kind': 'query',
                    'label': 'search_query',
                    'value': selected_value,
                }
            ],
        )

        try:
            self._cog._log_wiki_debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='start',
                    operation='defer',
                    subject='dropdown',
                ),
                action='defer',
                stage='start',
                operation='defer',
                trace_id=self.trace_id,
                invocation_mode='dropdown_selection',
                component_type='dropdown',
                selected_value=selected_value,
            )
            await inter.response.defer()

            embed, view, resolved_search_term, resolved_page_title = await self._cog.search_wikipedia(
                inter, selected_value, trace_id=self.trace_id
            )

            self._cog._log_wiki_debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='start',
                    operation='followup_send',
                    subject='dropdown',
                ),
                action='start',
                stage='start',
                operation='followup_send',
                trace_id=self.trace_id,
                invocation_mode='dropdown_selection',
                component_type='dropdown',
                selected_value=selected_value,
            )

            await inter.followup.send(embed=embed, view=view)

            self._cog._log_wiki_debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='complete',
                    operation='followup_send',
                    subject='dropdown',
                ),
                action='complete',
                stage='complete',
                operation='followup_send',
                trace_id=self.trace_id,
                invocation_mode='dropdown_selection',
                component_type='dropdown',
                selected_value=selected_value,
            )

            self._cog._log_wiki_debug(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='complete',
                    operation='search',
                ),
                action='complete',
                stage='complete',
                operation='search',
                invocation_mode='dropdown_selection',
                trace_id=self.trace_id,
                search_query=selected_value,
                resolved_search_term=resolved_search_term,
                resolved_page_title=resolved_page_title,
                resolution_source='user_query',
                component_type='dropdown',
                selected_value=selected_value,
                log_params=[
                    {
                        'kind': 'query',
                        'label': 'search_query',
                        'value': selected_value,
                    },
                    {
                        'kind': 'query',
                        'label': 'resolved_search_term',
                        'value': resolved_search_term,
                    },
                    {
                        'kind': 'page_title',
                        'label': 'resolved_page_title',
                        'value': resolved_page_title,
                    },
                ],
            )
        except (exceptions.Nonexistence, exceptions.StubArticle, exceptions.WikiRequestFailed) as exc:
            embed, view = EmbedFactory().create(
                title='Nothing interesting happens.',
                description=str(exc),
                thumbnail_url=GRAYSCALE_THUMBNAILS['filler'],
                colour=0x8B8B8B,
                button_label='Support Server',
                button_url=SUPPORT_SERVER
            )
            embed.timestamp = inter.created_at
            embed.set_footer(text=f'Runebot {DISPLAY_VERSION}')

            if inter.response.is_done():
                await inter.followup.send(embed=embed, view=view)
            else:
                await inter.response.send_message(embed=embed, view=view)
            return

        except Exception as exc:
            self._cog._log_wiki_error(
                inter,
                build_log_message(
                    command='wikipedia',
                    stage='runtime_failure',
                    operation='search',
                ),
                exc,
                action='fail',
                stage='runtime_failure',
                operation='search',
                invocation_mode='dropdown_selection',
                search_query=selected_value,
                component_type='dropdown',
                selected_value=selected_value,
                trace_id=self.trace_id if hasattr(self, 'trace_id') else None,
                handled=True,
                expected_failure=False,
                user_visible=True,
            )

            if inter.response.is_done():
                await inter.followup.send(
                    'Something went wrong while handling that selection.',
                    ephemeral=True,
                )
            else:
                await inter.response.send_message(
                    'Something went wrong while handling that selection.',
                    ephemeral=True,
                )
            return


class DropdownView(disnake.ui.View):
    '''
    A view class for creating dropdowns in the response.
    '''
    def __init__(self, options: list, cog, trace_id: str | None = None) -> None:
        '''
        Initialises a new instance of the DropdownView class.

        :param options: (List) -
        A list of options for the dropdown.
        :param cog: -
            The Wikipedia cog instance.

        :return: (None)
        '''
        self.bot = Bot
        self.trace_id = trace_id
        super().__init__()
        self.add_item(Dropdown(options, cog, trace_id=trace_id))


def setup(bot) -> None:
    '''
    Defines the bot setup function for the `wikipedia` command.

    :param bot: (Bot) -
        An instance of the Bot class.

    :return: (None)
    '''
    bot.add_cog(Wikipedia(bot))
