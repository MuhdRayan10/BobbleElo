import configparser
import discord
import logging
import sys
from discord.ext import commands
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

    return [round(change1+p) for p in team1], [round(change2+p) for p in team2]


