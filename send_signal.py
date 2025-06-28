import discord
import json
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))  # Replace 0 if not using .env

class SignalBot(discord.Client):
    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

        try:
            with open("last_signal.json", "r") as f:
                signal = json.load(f)

            message = (
                f"📊 **BTC ({signal['time']})**\n"
                f"📈 Direction: `{signal['direction']}`\n"
                f"💰 Entry: `{signal['entry']}`\n"
                f"🛑 SL: `{signal['sl']}`\n"
                f"🎯 TP: `{signal['tp']}`\n"
            )

            channel = self.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(message)
                print("✅ Signal sent to Discord channel.")
            else:
                print("❌ Channel not found or ID invalid.")

        except Exception as e:
            print("❌ Error sending signal:", e)

        await self.close()  # Exit after sending

def run_bot():
    intents = discord.Intents.default()
    client = SignalBot(intents=intents)
    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()
