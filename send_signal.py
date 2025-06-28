import discord
import json
import os
import asyncio

# Load credentials
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

class SignalBot(discord.Client):
    async def on_ready(self):
        print(f"✅ Logged in as {self.user}")

        try:
            with open("last_signal.json", "r") as f:
                signal = json.load(f)

            required_fields = ["time", "direction", "entry", "sl", "tp"]
            missing = [field for field in required_fields if field not in signal]
            if missing:
                print(f"❌ Missing required fields: {missing}")
                await self.close()
                return

            icon = "🟢" if signal["direction"].upper() == "BUY" else "🔴"

            # Voting logic
            vote_summary = ""
            if "votes" in signal:
                vote_summary = "\n🤖 AI Votes:\n" + "\n".join(
                    [f"• {k.title()}: `{v}`" for k, v in signal["votes"].items()]
                )

            # Optional reason
            reason = f"\n📚 Reason: {signal.get('reason', 'N/A')}"

            # Message
            message = (
                f"{icon} **BTC Trade Signal** ({signal['time']})\n"
                f"📈 Direction: `{signal['direction']}`\n"
                f"💰 Entry: `{signal['entry']}`\n"
                f"🛑 Stoploss: `{signal['sl']}`\n"
                f"🎯 Target: `{signal['tp']}`"
                f"{vote_summary}"
                f"{reason}"
            )

            channel = self.get_channel(CHANNEL_ID)
            if channel:
                if "image_url" in signal:
                    embed = discord.Embed()
                    embed.set_image(url=signal["image_url"])
                    await channel.send(content=message, embed=embed)
                else:
                    await channel.send(message)
                print("✅ Signal sent to Discord.")
            else:
                print("❌ Discord channel not found. Check CHANNEL_ID.")

        except FileNotFoundError:
            print("❌ last_signal.json not found.")
        except json.JSONDecodeError:
            print("❌ JSON decode error.")
        except Exception as e:
            print("❌ Error sending signal:", e)

        await self.close()

def run_bot():
    intents = discord.Intents.default()
    client = SignalBot(intents=intents)
    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()
