# main.py
from keep_alive import keep_alive
import discord
import os
from dotenv import load_dotenv
import asyncio
import time
from ai_engine import main as run_strategy  # Import your strategy logic

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
    
    # Send startup message to the #general channel
    for guild in client.guilds:
        for channel in guild.text_channels:
            if channel.name == "general":
                await channel.send("✅ Ayu_Trader_Bot is now active 🚀")
                break

    # Start strategy loop in background
    async def strategy_loop():
        while True:
            print("🔄 Running strategy logic...")
            run_strategy()
            await asyncio.sleep(300)  # Wait 5 minutes

    asyncio.create_task(strategy_loop())  # Run strategy loop in background

# Start Flask keep_alive server
keep_alive()

# Run the bot
client.run(TOKEN)
