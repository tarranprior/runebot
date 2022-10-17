from disnake.ext import commands
from disnake.ext.commands import Context
from disnake import Option, OptionType

from templates.bot import Bot
from config import *
from utils import *


class Wiki(commands.Cog, name='wiki'):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    '''
    Wikipedia general lookup function. Takes the given search query and returns the results in an embed.
    :param query: (String) - Represents a search query.
    '''
    def fetch_wiki_data(self, query: str) -> None:
        query = search_query(query)

        if query == str('random') or query == str("i'm_feeling_lucky"):
            page_content = parse_page(BASE_URL, FEELING_LUCKY, HEADERS)
            attributes = parse_all(page_content)
        else:
            page_content = parse_page(BASE_URL, query, HEADERS)
            attributes = parse_all(page_content)

        title = attributes['title']
        description = attributes['description']
        infobox = attributes['infobox']
        options = attributes['options']
        thumbnail_url = attributes['thumbnail_url']

        if description:
            embed, view = EmbedFactory().create(title=title, description=description.pop(), infobox=infobox, thumbnail_url=thumbnail_url, button_url=f'{BASE_URL}{attributes["title"].replace(" ", "_")}')
            if len(embed.description) < 84:
                embed.set_footer(text="To view more information about this page, click the button below.")
            return(embed, view)
        embed, view = EmbedFactory().create(title=title, description=f'{title} may refer to several articles. Use the dropdown below to select an option.', options=options)
        return(embed, view)

    @commands.command(name='wiki', description='Look up an entry from the official Old School RuneScape wikipedia.')
    async def wiki(self, ctx: Context, *, query) -> None:
        embed, view = self.fetch_wiki_data(query.lower())
        await ctx.send(embed=embed, view=view)

        '''
        Select option #1.
        This function is for sending reponses to the previous dropdown interaction for nested options.
        Ex: Tools > Tool Store.

        :param interaction_1: (Interaction) - Represents the previous dropdown (select) menu.
        '''
        async def select_option(interaction_1) -> None:
            inter_1_embed, inter_1_view = self.fetch_wiki_data(view.children[0].values[0])
            await interaction_1.response.send_message(embed=inter_1_embed, view=inter_1_view)

            '''
            Select option #2.
            Another function for sending responses to the previous dropdown interaction for further nested options.
            Ex: Tools > Tool Store > Tool Store 1.

            :param interaction_2: (Interaction) - Represents the previous dropdown (select) menu.
            '''
            async def select_option_2(interaction_2) -> None:
                inter_2_embed, inter_2_view = self.fetch_wiki_data(inter_1_view.children[0].values[0])
                await interaction_2.response.send_message(embed=inter_2_embed, view=inter_2_view)

            inter_1_view.children[0].callback = select_option_2

        view.children[0].callback = select_option

    @commands.slash_command(name="wiki", description="Look up an entry from the official Old School RuneScape wikipedia.", options=[
            Option(
                name="query",
                description='Search for an article. Type "Random" to search for a random article!',
                type=OptionType.string,
                required=True
            )
        ]
    )
    async def wiki_slash(self, inter: disnake.ApplicationCommandInteraction, *, query: str) -> None:
        await inter.response.defer()
        embed, view = self.fetch_wiki_data(query.lower())
        await inter.followup.send(embed=embed, view=view)

        async def select_option(interaction_1) -> None:
            await interaction_1.response.defer()
            inter_1_embed, inter_1_view = self.fetch_wiki_data(view.children[0].values[0])
            await interaction_1.followup.send(embed=inter_1_embed, view=inter_1_view)

            async def select_option_2(interaction_2) -> None:
                await interaction_2.response.defer()
                inter_2_embed, inter_2_view = self.fetch_wiki_data(inter_1_view.children[0].values[0])
                await interaction_2.followup.send(embed=inter_2_embed, view=inter_2_view)

            inter_1_view.children[0].callback = select_option_2
        
        view.children[0].callback = select_option

def setup(bot) -> None:
    bot.add_cog(Wiki(bot))