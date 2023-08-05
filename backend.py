import asyncio
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
import asyncio

db = sqlite3.connect("data/elo.db")
c = db.cursor()

c.execute("CREATE TABLE IF NOT EXISTS elo(userid INT, rating INT)")
db.commit()

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

client = commands.Bot(help_command=None, command_prefix="!", intents=discord.Intents.all(),
                      application_id="1135592064852181062")  # Setting prefix

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


def add_to_db(userids):
    c.execute("SELECT userid FROM elo")
    users = [u[0] for u in c.fetchall()]

    for user in userids:
        if user not in users:
            c.execute("INSERT INTO elo values(?,?)", (user, 1500))

    db.commit()


def calculate_rating(player1, player2, result):
    outcome = 1 / (1 + (10 ** ((player2 - player1) / 400)))

    rating1 = player1 + (32 * (result - outcome))
    rating2 = player2 + (32 * ((not result) - 1 + outcome))

    return round(rating1, 2), round(rating2, 2)


def calculate_team_rating(team1, team2, result):
    team1_r = sum(team1) / len(team1)
    team2_r = sum(team2) / len(team2)

    new_ratings = calculate_rating(team1_r, team2_r, result)

    change1, change2 = new_ratings[0] - team1_r, new_ratings[1] - team2_r

    return [round(change1 + p, 2) for p in team1], [round(change2 + p, 2) for p in team2]


def get_current_ratings(userids):
    c.execute("SELECT * FROM elo")
    data = c.fetchall()

    return {user: elo for user, elo in data if user in userids}


def update_ratings(users, ratings):
    for x in range(len(users)):
        c.execute("UPDATE elo SET rating=:r WHERE userid=:u", {"r": ratings[x], "u": users[x]})
    db.commit()


async def match_result(interaction, player1, player2, player3, player4, winner):

    if interaction.user.id not in [984245773887766551, 837584356988944396]:
        await interaction.response.send_message("no perms dude, sorry :sweat_smile:")
        return


    users_1, users_2 = [player.id for player in [player1, player3] if player], [player.id for player in
                                                                                [player2, player4] if player]

    add_to_db(users_1 + users_2)

    team1 = get_current_ratings(users_1)
    team2 = get_current_ratings(users_2)

    new_elos = calculate_team_rating(team1.values(), team2.values(), winner)

    update_ratings(users_1 + users_2, new_elos[0] + new_elos[1])

    await interaction.response.send_message("Done!!!")


"""
    BUTTON CLASSES
"""

class LeaveTeam(View):
    def __init__(self, team, func, *items):
        super().__init__(*items)
        self.team = team

        self.remove_func = func

    @discord.ui.button(label="Leave Team", style=discord.ButtonStyle.red)
    async def leave_team(self, interaction, button):
        button.disabled = True
        await self.remove_func(interaction, interaction.user.id, self.team)


class Game(View):
    def __init__(self, team1, team2, msg, *items):
        super().__init__(*items)
        self.msg = msg

        self.team1 = {d: 0 for d in team1}
        self.team2 = {d: 0 for d in team2}

    @discord.ui.button(label="Winner A", style=discord.ButtonStyle.blurple)
    async def winner_a(self, interaction, _):

        if interaction.user.id in self.team1:
            self.team1[interaction.user.id] = 1
        else:
            self.team2[interaction.user.id] = 1

        await interaction.response.send_message("You have voted for Team A!", ephemeral=True)

        winner = self.check_winner()

        print([user for user, x in list(self.team1.items()) + list(self.team2.items()) if x])

        if winner:
            await self.winner(winner)

    async def winner(self, winner):
        t1, t2 = list(self.team1.keys()), list(self.team2.keys())

        add_to_db(t1 + t2)
        team1_elo = get_current_ratings(t1)
        team2_elo = get_current_ratings(t2)

        new_elo = calculate_team_rating(team1_elo.values(), team2_elo.values(), winner if winner == 1 else 0)

        update_ratings(list(team1_elo) + list(team2_elo), new_elo[0] + new_elo[1])

        await self.update_embed(winner, new_elo[0], new_elo[1])



    @discord.ui.button(label="Winner B", style=discord.ButtonStyle.blurple)
    async def winner_b(self, interaction, _):
        print("vote for b")

        if interaction.user.id in self.team1:
            self.team1[interaction.user.id] = 2
        else:
            self.team2[interaction.user.id] = 2

        print("sending msg")
        await interaction.response.send_message("You have voted for Team B", ephemeral=True)

        print([user for user, x in list(self.team1.items()) + list(self.team2.items()) if x])

        winner = self.check_winner()
        if winner:
            await self.winner(winner)

    async def update_embed(self, w, team1, team2):
        print("uwu")
        embed = embed_template()
        embed.title = f"Team {'A' if w==1 else 'B'} wins"

        # Getting the new player scores
        t1, t2 = list(self.team1.keys()), list(self.team2.keys())

        print(t1, t2, team1, team2)

        # May god help whoever has to debug this
        embed.add_field(
            name="Team A",
            value='\n'.join([f'{"⬆️" if w == 1 else "⬇️"} <@{t1[x]}> (`{team1[x]}`)' for x in range(len(t1))])
        )
        embed.add_field(
            name="Team B",
            value='\n'.join([f'{"⬆️" if w == 2 else "⬇️"} <@{t2[x]}> (`{team2[x]}`)' for x in range(len(t2))])
        )

        await self.msg.edit(embed=embed, view=None)

    def check_winner(self):
        votes = set(self.team1.values()).union(set(self.team2.values()))

        return list(votes)[0] if len(votes) == 1 else None


class InitializeGame(View):

    def __init__(self, creator, msg, *items):
        super().__init__(*items)
        self.msg = msg

        self.team1, self.team2 = [], []
        self.creator = creator
        self.game_id = gen_game_id()

    async def remove_from_team(self, interaction, user, team):
        team.remove(user)
        await interaction.response.send_message("Removed", ephemeral=True)

        await self.update_embed()


    @discord.ui.button(label="Team A", style=discord.ButtonStyle.blurple)
    async def join_team1(self, interaction, button):

        if interaction.user.id in self.team2:
            await interaction.response.send_message("You are already in another team", ephemeral=True)
            return

        team_length = len(self.team1)
        if team_length < 4 and interaction.user.id not in self.team1:
            self.team1.append(interaction.user.id)
            await self.update_embed()
        else:
            button.disabled = True

        await interaction.response.send_message("You have joined Team A!", ephemeral=True, view=LeaveTeam(self.team1, self.remove_from_team))



    @discord.ui.button(label="Team B", style=discord.ButtonStyle.blurple)
    async def join_team2(self, interaction, button):
        team_length = len(self.team2)
        if interaction.user.id in self.team1:
            await interaction.response.send_message("You are already in another team", ephemeral=True)
            return

        if team_length < 4 and interaction.user.id not in self.team2:
            self.team2.append(interaction.user.id)
            await self.update_embed()
        else:
            button.disabled = True

        await interaction.response.send_message("You have joined Team B!", ephemeral=True, view=LeaveTeam(self.team2, self.remove_from_team))


    async def update_embed(self):
        embed = embed_template()

        embed.title = "Game Lobby"
        embed.add_field(name="Team A", value='\n'.join([f"<@{p}>" for p in self.team1]))
        embed.add_field(name="Team B", value='\n'.join([f"<@{p}>" for p in self.team2]))

        await self.msg.edit(embed=embed)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, row=2)
    async def start_game(self, interaction, _):
        await interaction.response.defer()

        if interaction.user.id != self.creator:
            await interaction.followup.send(
                "Only the person who created this match can start the game!",
                ephemeral=True
            )
            return

        if not self.team1 or not self.team2:
            await interaction.followup.send(
                "You need at least 1 player in each team to start the game!",
                ephemeral=True
            )
            return

        await self.msg.edit(view=Game(self.team1, self.team2, self.msg))

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, row=2)
    async def cancel_game(self, interaction, _):
        await interaction.response.defer()

        if interaction.user.id != self.creator:
            await interaction.followup.send(
                "Only the person who created this match can cancel the game!",
                ephemeral=True
            )
            return

        await self.msg.delete()



def gen_game_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
