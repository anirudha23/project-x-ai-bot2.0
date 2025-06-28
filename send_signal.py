import discord
import json
import os
import asyncio

# Load from environment
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

class SignalBot(discord.Client):
    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

        try:
            # Load the signal from the latest signal file
            with open("last_signal.json", "r") as f:
                signal = json.load(f)

            # Required fields for message
            required_fields = ["time", "direction", "entry", "sl", "tp"]
            missing = [field for field in required_fields if field not in signal]
            if missing:
                print(f"❌ Missing required fields in signal: {missing}")
                await self.close()
                return

            # Format the message
            message = (
                f"📊 **BTC Signal ({signal['time']})**\n"
                f"📈 Direction: `{signal['direction']}`\n"
                f"💰 Entry: `{signal['entry']}`\n"
                f"🛑 Stoploss: `{signal['sl']}`\n"
                f"🎯 Target: `{signal['tp']}`\n"
            )

            # Send to channel
            channel = self.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(message)
                print("✅ Signal sent to Discord channel.")
            else:
                print("❌ Discord channel not found. Check CHANNEL_ID.")

        except FileNotFoundError:
            print("❌ File last_signal.json not found.")
        except json.JSONDecodeError:
            print("❌ Error decoding JSON. File might be corrupted.")
        except Exception as e:
            print("❌ Exception occurred:", e)

        await self.close()  # Exit after sending

def run_bot():
    intents = discord.Intents.default()
    client = SignalBot(intents=intents)
    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()
