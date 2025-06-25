from keep_alive import keep_alive
import discord
import os
from dotenv import load_dotenv
import subprocess  # For running the scheduler

# Load environment variables
load_dotenv()

# Load Discord bot token
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up Discord client with proper intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Bot is live as {client.user}")
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == "general":
                await channel.send("✅ Ayu_Trader_Bot is now active 🚀")
                return

# Keep the bot alive with a Flask web server
keep_alive()

# 🔁 Start the background process to send signal every 5 minutes
subprocess.Popen(["python3", "scheduler.py"])

# Run the bot
client.run(TOKEN)