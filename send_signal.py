import discord
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

class SignalBot(discord.Client):
    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

        # ✅ Set bot presence status
        activity = discord.Activity(type=discord.ActivityType.watching, name="BTC 15m chart...")
        await self.change_presence(status=discord.Status.online, activity=activity)

        # ✅ Render log confirmation
        print("🟢 Project X Bot is ONLINE and watching BTC 15m chart...")

        try:
            with open("last_signal.json", "r") as f:
                signal_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load signal: {e}")
            await self.close()
            return

        message = f"""
📡 **Project X Signal – {signal_data['symbol']} ({signal_data['timeframe']})**

**Direction:** {signal_data['direction']}  
**Entry:** {signal_data['entry']}  
**Stoploss:** {signal_data['sl']}  
**Take Profit:** {signal_data['tp']}  
**Vote Count:** {signal_data['votes']}

🧠 **AI Votes:**  
• ChatGPT: {signal_data['chatgpt']}  
• Grok: {signal_data['grok']}  
• Deepshik: {signal_data['deepshik']}  
"""

        try:
            channel = await self.fetch_channel(CHANNEL_ID)
            await channel.send(message)
            print("✅ Signal sent using bot.")
        except Exception as e:
            print(f"❌ Failed to send message: {e}")

        await self.close()

intents = discord.Intents.default()
client = SignalBot(intents=intents)
client.run(TOKEN)
