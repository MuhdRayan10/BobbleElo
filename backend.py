import configparser
import discord
import logging
import sys
from discord.ext import commands
from discord.ui import Button, View
from colorlog import ColoredFormatter
import random
import string
import sqlite3

db = sqlite3.connect("elo.db")
c = db.cursor()

c.execute("CREATE TABLE IF NOT EXISTS elo(userid INT, rating INT)")
db.commit()

try:
    # Loading config.ini
    config = configparser.ConfigParser()

    try:
        config.read('data/config.ini')
    except Exception as e:
        print("Error reading the config.ini file. Error: " + str(e))
        sys.exit()


    # Initializing the logger
    def colorlogger(name='bot'):
        # disabler loggers
        for logger in logging.Logger.manager.loggerDict:
            logging.getLogger(logger).disabled = True
        logger = logging.getLogger(name)
        stream = logging.StreamHandler()
        log_format = "%(reset)s%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s"
        stream.setFormatter(ColoredFormatter(log_format))
        logger.addHandler(stream)
        return logger  # Return the logger


    log = colorlogger()

    try:
        discord_token: str = config.get('secret', 'discord_token')

        log_level: str = config.get('main', 'log_level')
        owner_ids = config.get('main', 'owner_ids').strip().split(',')
        owner_guilds = config.get('main', 'owner_guilds').strip().split(',')
        backup_interval: int = config.getint('main', 'backup_interval')
        status_interval: int = config.getint('main', 'status_interval')

        embed_footer: str = config.get('discord', 'embed_footer')
        embed_color: int = int(config.get('discord', 'embed_color'), base=16)
        embed_title: str = config.get('discord', 'embed_title')
        embed_url: str = config.get('discord', 'embed_url')


    except Exception as err:
        log.critical("Error reading the config.ini file. Error: " + str(err))
        sys.exit()

    if log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        log.setLevel(log_level.upper())
    else:
        log.warning(f"Invalid log level {log_level}. Defaulting to INFO.")
        log.setLevel("INFO")

    owner_ids = tuple([int(i) for i in owner_ids])
    log.debug(owner_ids)

    owner_guilds = tuple([int(i) for i in owner_guilds])
    log.debug(owner_guilds)

    client = commands.Bot(help_command=None, command_prefix="!", intents=discord.Intents.all(), application_id="1135592064852181062")  # Setting prefix

    _embed_template = discord.Embed(
        title="Title!",
        color=embed_color,
        url=embed_url
    )
    _embed_template.set_footer(text=embed_footer)

    embed_template = lambda: _embed_template.copy()

    def error_template(description: str) -> discord.Embed:
        _error_template = discord.Embed(
            title="Error!",
            description=description,
            color=0xff0000,
            url=embed_url
        )
        _error_template.set_footer(text=embed_footer)

        return _error_template.copy()

    def calculate_rating(player1, player2, result):
        outcome = 1 / (1 + (10**((player1 - player2) / 400)))

        rating1 = player1 + (32 * (result - outcome))
        rating2 = player2 + (32 * ((not result if result != 0.5 else 0.5) - outcome))

        return round(rating1, 2), round(rating2, 2)


    def calculate_team_rating(team1, team2, result):
        team1_r = sum(team1)/len(team1)
        team2_r = sum(team2)/len(team2)

        new_ratings = calculate_rating(team1_r, team2_r, result)

        change1, change2 = new_ratings[0] - team1_r, new_ratings[1] - team2_r

        return [round(change1+p, 2) for p in team1], [round(change2+p, 2) for p in team2]

    def get_current_ratings(userids):
        c.execute("SELECT * FROM elo")
        data = c.fetchall()

        return {user:elo for user, elo in data if user in userids}

    def update_ratings(users, ratings):
        for x in range(len(users)):
            c.execute("UPDATE elo SET rating=:r WHERE userid=:u", {"r":ratings[0], "u":users[0]})
        db.commit()

    """
        BUTTON CLASSES
    """

    class Game(View):
        def __init__(self, team1, team2, msg, *items):
            super().__init__(*items)
            self.msg = msg

            self.team1 = {d:0 for d in team1}
            self.team2 = {d:0 for d in team2}

            self.player_count = len(self.team1) + len(self.team2)

        @discord.ui.button(label="Winner A", style=discord.ButtonStyle.blurple)
        async def winner_a(self, interaction, button):
            if interaction in self.team1:
                self.team1[interaction] = 1
            else:
                self.team2[interaction] = 1

            winner = self.check_winner()

            if winner:
                await self.winner(winner)

        async def winner(self, winner):
            team1_elo = get_current_ratings(list(self.team1.keys()))
            team2_elo = get_current_ratings(list(self.team2.keys()))

            new_elos = calculate_team_rating(team1_elo, team2_elo, winner if winner == 1 else 0)

            update_ratings(list(team1_elo) + list(team2_elo), new_elos[0] + new_elos[1])

            await self.update_embed(winner, new_elos[0], new_elos[1])


        @discord.ui.button(label="Winner B", style=discord.ButtonStyle.blurple)
        async def winner_b(self, interaction, button):
            if interaction in self.team1:
                self.team1[interaction] = 2
            else:
                self.team2[interaction] = 2

            winner = self.check_winner()
            if winner:
                await self.winner(winner)

        async def update_embed(self, w, team1, team2):
            embed = embed_template()

            embed.title(f"Team {'A' if w else 'B'}")

            t1, t2 = list(self.team1.keys()), list(self.team2.keys())
            embed.add_field(name="Team A", value=f'\n{"⬆️" if w == 1 else "⬇️"}'.join([f'<@{t1[x]}> (`{team1[x]}`)' for x in range(len(t1))]))
            embed.add_field(name="Team B", value=f'\n{"⬆️" if w == 2 else "⬇️"}'.join([f'<@{t2[x]}> (`{team2[x]}`)' for x in range(len(t2))]))

            await self.msg.edit(embed=embed, view=None)

        def check_winner(self):

            votes = set(self.team1.values()).union(set(self.team2.values()))

            return list(votes)[0].pop() if len(votes) == 1 else None



    class InitializeGame(View):

        def __init__(self, creator, msg, *items):
            super().__init__(*items)
            self.msg = msg

            self.team1, self.team2 = set(), set()
            self.creator = creator
            self.game_id = gen_game_id()

        @discord.ui.button(label="Team A", style=discord.ButtonStyle.blurple)
        async def join_team1(self, interaction, button):

            if interaction.user.id in self.team2:
                await interaction.response.send_message("You are already in another team", ephemeral=True)
                return

            team_length = len(self.team1)
            if team_length < 4:
                self.team1.add(interaction.user.id)
            else:
                button.disabled = True

            await interaction.response.send_message("You have joined Team A!", ephemeral=True)

            if team_length != len(self.team1):
                await self.update_embed()

        @discord.ui.button(label="Team B", style=discord.ButtonStyle.blurple)
        async def join_team2(self, interaction, button):
            team_length = len(self.team2)
            if interaction.user.id in self.team1:
                await interaction.response.send_message("You are already in another team", ephemeral=True)
                return

            if team_length < 4:
                self.team2.add(interaction.user.id)
            else:
                button.disabled = True

            await interaction.response.send_message("You have joined Team B!", ephemeral=True)

            if team_length != len(self.team2):
                await self.update_embed()

        async def update_embed(self):
            embed = embed_template()

            embed.title = "Game Lobby"
            embed.add_field(name="Team A", value='\n'.join([f"<@{p}>" for p in self.team1]))
            embed.add_field(name="Team B", value='\n'.join([f"<@{p}>" for p in self.team2]))

            await self.msg.edit(embed=embed)

        @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green)
        async def start_game(self, interaction, _):
            if interaction.user.id != self.creator:
                await interaction.response.send_message("Shh, only the person who created this match can start the game!", ephemeral=True)
                return

            if not self.team1 or not self.team2:
                await interaction.response.send_message("You need at least 1 players in each team to start the game!", ephemeral=True)
                return


            await self.msg.edit(view=Game(self.team1, self.team2, self.msg))


        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
        async def cancel_game(self, interaction, _):
            if interaction.user.id != self.creator:
                await interaction.response.send_message("Shh, only the person who created this match can cancel the game!", ephemeral=True)
                return

            await self.msg.delete()

    def gen_game_id():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

except Exception as e:
    print(e)