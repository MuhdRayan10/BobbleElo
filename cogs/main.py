import discord
from discord.ext import commands
from discord import app_commands
from backend import log, embed_template, error_template, gen_game_id, InitializeGame

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create-game")
    async def create_game(self, interaction):
        print("e")


        embed = embed_template()
        embed = discord.Embed(title="Match", description=f"Match started by <@{interaction.user.id}>")
        embed.add_field(name="ㅤㅤTeam 1", value=" 🤖  Player 1\n 👾  Player 2")
        embed.add_field(name="ㅤvs", value="ㅤㅤㅤㅤ")
        embed.add_field(name="Team 2", value="Player 3  🥷\nPlayer 4  🎃")

        embed.set_footer(text="Made with <3 by muhdrayan & rajdave")

        embed.title = "Create Game"

        print(interaction)


        await interaction.response.send_message(embed=embed)
        view = InitializeGame(interaction.user.id, (await interaction.original_response()))

        print("a")
        await interaction.edit_original_response(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Main(bot))