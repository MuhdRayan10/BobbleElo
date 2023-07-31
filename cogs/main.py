import discord
from discord.ext import commands
from discord import app_commands
from backend import log, embed_template, error_template, gen_game_id

class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create-game")
    async def create_game(self, interaction):
        await interaction.response.defer()

        game_id = gen_game_id()

        embed = embed_template()
        embed.title = "Create Game"
        embed.description = ""






        await interaction.folowup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Main(bot))