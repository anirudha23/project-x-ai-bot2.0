# ✅ FILE: main.py

from keep_alive import keep_alive
import discord
import os
from dotenv import load_dotenv
import asyncio
from ai_engine import main as run_strategy  # Use your strategy logic

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Set up Discord bot client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"\u2705 Bot is live as {client.user}")

    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == "general":
                await channel.send("\u2705 Ayu_Trader_Bot is now active \ud83d\ude80")
                break

    # Start the strategy loop
    async def strategy_loop():
        while True:
            print("\ud83d\udd01 Running Project-X strategy...")
            try:
                run_strategy()
            except Exception as e:
                print("\u274c Error in strategy:", e)
            await asyncio.sleep(300)  # Run every 5 minutes

    asyncio.create_task(strategy_loop())

# Start Flask keep-alive server
keep_alive()

# Run the Discord bot
client.run(TOKEN)
