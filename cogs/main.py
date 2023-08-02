import discord
from discord.ext import commands
from discord import app_commands
from backend import log, embed_template, error_template, gen_game_id, InitializeGame, match_result
import aiosqlite


class Main(commands.Cog):
    def __init__(self, client):
        self.client = client

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

    @app_commands.command(name='add-match')
    async def add_match(self, interaction, winner:int, player1:discord.User, player2:discord.User, player3:discord.User=None, player4:discord.User=None):
        match_result(interaction, player1, player2, player3, player4, winner)




    @app_commands.command(name="leaderboard")
    async def leaderboard(self, interaction, amount: int = 10):
        if amount > 25:
            amount = 25
        elif amount < 1:
            amount = 1

        db = await aiosqlite.connect("data.db")
        cursor = await db.execute("SELECT * FROM eco ORDER BY rating DESC LIMIT ?", (amount,))
        res = await cursor.fetchall()
        # res format - [(user_id, rating), (user_id, rating), ...]

        embed = embed_template()
        embed.title = "Leaderboard"

        for i, (user_id, rating) in enumerate(res):
            user = await self.client.fetch_user(user_id)
            embed.add_field(name=f"#{i+1} {user.name}", value=f"Rating: {rating}", inline=False)

        await interaction.response.send_message(embed=embed)









async def setup(bot):
    await bot.add_cog(Main(bot))