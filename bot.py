import discord
from discord.ext import commands
from datetime import timedelta
import os
import json

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store timeout counts (user_id: count)
# In production, use a database. For now, we use a JSON file
TIMEOUT_FILE = "timeout_data.json"

def load_timeout_data():
    """Load timeout data from file"""
    try:
        with open(TIMEOUT_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_timeout_data(data):
    """Save timeout data to file"""
    with open(TIMEOUT_FILE, 'w') as f:
        json.dump(data, f)

def get_timeout_duration(count):
    """Calculate timeout duration based on violation count"""
    durations = [
        timedelta(seconds=30),      # 1st offense: 30 seconds
        timedelta(minutes=5),        # 2nd offense: 5 minutes
        timedelta(minutes=30),       # 3rd offense: 30 minutes
        timedelta(hours=1),          # 4th offense: 1 hour
        timedelta(hours=3),          # 5th+ offense: 3 hours (max)
    ]
    
    if count >= len(durations):
        return durations[-1]  # Max timeout
    return durations[count]

def format_duration(td):
    """Format timedelta to readable string"""
    total_seconds = int(td.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds} seconds"
    elif total_seconds < 3600:
        return f"{total_seconds // 60} minutes"
    else:
        return f"{total_seconds // 3600} hour(s)"

@bot.event
async def on_ready():
    print(f'{bot.user} is now online!')
    print(f'Bot ID: {bot.user.id}')

@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author.bot:
        return
    
    # Check if message is a reply
    if message.reference is None:
        return
    
    # Check if message content is "ok" (case-insensitive)
    if message.content.lower().strip() != "ok":
        return
    
    # Get the message being replied to
    try:
        replied_message = await message.channel.fetch_message(message.reference.message_id)
    except:
        return
    
    # Check if the replied-to message is from the protected user
    PROTECTED_USER_ID = 881074063030755400
    
    if replied_message.author.id != PROTECTED_USER_ID:
        return
    
    # This user violated the rule!
    violator = message.author
    
    # Load timeout data
    timeout_data = load_timeout_data()
    user_id_str = str(violator.id)
    
    # Get current violation count
    current_count = timeout_data.get(user_id_str, 0)
    
    # Calculate timeout duration
    timeout_duration = get_timeout_duration(current_count)
    
    # Timeout the user
    try:
        await violator.timeout(timeout_duration, reason="Replied 'ok' to protected user")
        
        # Send warning DM
        try:
            warning_message = (
                f"⚠️ **Warning!**\n\n"
                f"You have been timed out for **{format_duration(timeout_duration)}** "
                f"for replying with 'ok' to <@{PROTECTED_USER_ID}>.\n\n"
                f"This is violation #{current_count + 1}. "
                f"Future violations will result in longer timeouts (max 3 hours)."
            )
            await violator.send(warning_message)
        except discord.Forbidden:
            # User has DMs disabled, send in channel (ephemeral not possible with on_message)
            await message.channel.send(
                f"{violator.mention} {warning_message}",
                delete_after=10
            )
        
        # Increment violation count
        timeout_data[user_id_str] = current_count + 1
        save_timeout_data(timeout_data)
        
        # Delete the offending message
        try:
            await message.delete()
        except:
            pass
        
        print(f"Timed out {violator} for {format_duration(timeout_duration)} (violation #{current_count + 1})")
        
    except discord.Forbidden:
        print(f"Missing permissions to timeout {violator}")
    except Exception as e:
        print(f"Error timing out user: {e}")

# Run the bot
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    print("ERROR: DISCORD_BOT_TOKEN environment variable not set!")
