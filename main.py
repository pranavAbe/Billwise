import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import logging


logging.basicConfig(level=logging.INFO)
load_dotenv()

bot = commands.Bot(command_prefix='.')

@bot.event
async def on_ready():
    print(f'Logged in to Discord as {bot.user.name}.')

for folder in os.listdir("modules"):
    if os.path.exists(os.path.join("modules", folder, "cog.py")):
        bot.load_extension(f"modules.{folder}.cog")

@bot.command(name="ping", description="Returns Bot Latency")
async def ping(context):
    await context.send(f"Latency: {bot.latency * 1000}ms")

bot.run(os.environ.get('DISCORD_TOKEN'))
