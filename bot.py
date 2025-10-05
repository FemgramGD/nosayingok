import discord
from discord.ext import commands
from datetime import timedelta
import os
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_timeout_data():
    try:
        with open("timeout_data.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_timeout_data(data):
    with open("timeout_data.json", 'w') as f:
        json.dump(data, f)

def get_timeout_duration(count):
    durations = [
        timedelta(seconds=30),
        timedelta(minutes=5),
        timedelta(minutes=30),
        timedelta(hours=1),
        timedelta(hours=3),
    ]
    
    if count >= len(durations):
        return durations[-1]
    return durations[count]

def format_duration(td):
    seconds = int(td.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes"
    else:
        return f"{seconds // 3600} hour(s)"

@bot.event
async def on_ready():
    print(f'{bot.user} is now online!')
    print(f'Bot ID: {bot.user.id}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.reference is None:
        return
    
    if message.content.lower().strip() != "ok":
        return
    
    try:
        replied_msg = await message.channel.fetch_message(message.reference.message_id)
    except:
        return
    
    PROTECTED_USER = 881074063030755400
    
    if replied_msg.author.id != PROTECTED_USER:
        return
    
    user = message.author
    data = load_timeout_data()
    user_id = str(user.id)
    
    count = data.get(user_id, 0)
    duration = get_timeout_duration(count)
    
    try:
        await user.timeout(duration, reason="Replied 'ok' to protected user")
        
        try:
            msg = (
                f"⚠️ **Warning!**\n\n"
                f"You have been timed out for **{format_duration(duration)}** "
                f"for replying with 'ok' to <@{PROTECTED_USER}>.\n\n"
                f"This is violation #{count + 1}. "
                f"Future violations will result in longer timeouts (max 3 hours)."
            )
            await user.send(msg)
        except discord.Forbidden:
            await message.channel.send(f"{user.mention} {msg}", delete_after=10)
        
        data[user_id] = count + 1
        save_timeout_data(data)
        
        try:
            await message.delete()
        except:
            pass
        
        print(f"Timed out {user} for {format_duration(duration)} (violation #{count + 1})")
        
    except discord.Forbidden:
        print(f"Missing permissions to timeout {user}")
    except Exception as e:
        print(f"Error timing out user: {e}")

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
