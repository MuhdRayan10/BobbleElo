import configparser
import discord
import logging
import sys
from discord.ext import commands
from discord.ui import Button, View
from colorlog import ColoredFormatter

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

client = commands.Bot(help_command=None, command_prefix="!", intents=discord.Intents.none())  # Setting prefix

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


"""
    BUTTON CLASSES
"""


class InitializeGame(View):

    def __init__(self, creator):
        self.team1, self.team2 = set(), set()
        self.creator = creator
    @discord.ui.button(label="Team A", style=discord.ButtonStyle.blue)
    async def join_team1(self, interaction, button):
        if len(self.team1) < 4:
            self.team1.add(interaction.response.author)
        else:
            button.disabled = True


        self.update_embed()

    @discord.ui.button(label="Team B", style=discord.ButtonStyle.blue)
    async def join_team2(self, interaction, button):
        if len(self.team2) < 4:
            self.team2.add(interaction.user)
        else:
            button.disabled = True

        await self.update_embed()

    async def update_embed(self):
        embed = discord.Embed()
        # TO DO: represent teams here

        self.msg = await self.msg.edit(embed=embed)

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green)
    async def start_game(self, interaction, _):
        if interaction.user.id != self.creator:
            await interaction.response.send_message("Shh, only the person who created this match can start the game!", ephemeral=True)
            return

        pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel_game(self):
        if interaction.user.id != self.creator:
            await interaction.response.send_message("Shh, only the person who created this match can cancel the game!", ephemeral=True)
            return

        await self.msg.delete()