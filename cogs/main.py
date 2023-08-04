import discord
from discord.ext import commands
from discord import app_commands
from backend import log, embed_template, error_template, gen_game_id, InitializeGame, match_result
import sqlite3


class Main(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.tree.sync()


    @app_commands.command(name="create-game")
    async def create_game(self, interaction):

        # Create the embed
        embed = embed_template()
        embed.title = "Create Game"
        embed.description = f"Match started by <@{interaction.user.id}>"

        # Send the embed and edit it with the view
        await interaction.response.send_message(embed=embed)
        view = InitializeGame(interaction.user.id, (await interaction.original_response()))
        await interaction.edit_original_response(embed=embed, view=view)

    @app_commands.command(name='add-match')
    async def add_match(self, interaction, winner:int, player1:discord.User, player2:discord.User, player3:discord.User=None, player4:discord.User=None):
        await match_result(interaction, player1, player2, player3, player4, winner)


    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction, amount: int = 10):
        await interaction.response.defer()
        if amount > 25:
            amount = 25
        elif amount < 1:
            amount = 1

        db = sqlite3.connect("data/elo.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM elo ORDER BY rating DESC LIMIT ?", (amount,))
        res = cursor.fetchall()
        # res format - [(user_id, rating), (user_id, rating), ...]

        print('fetched data', res)

        embed = embed_template()
        embed.title = "Leaderboard"


        for i, (user_id, rating) in enumerate(res):
            user = await self.client.fetch_user(user_id)
            print(user)
            embed.add_field(name=f"#{i+1} `{user.name}`", value=f"Rating: {rating}", inline=False)


        await interaction.followup.send(embed=embed)









async def setup(bot):
    await bot.add_cog(Main(bot))