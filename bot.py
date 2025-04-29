import discord
from discord.ext import commands
import subprocess
import os
import json
import asyncio
from datetime import datetime

# dev note - I need to modularize the file into multiple files............

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Privileged Gateway Intents
intents = discord.Intents().all()

# Set prefix and intents
bot = commands.Bot(command_prefix='!', intents=intents, heartbeat_timeout=120)

# Global variable to track server process
server_process = None

def is_server_running():
    global server_process
    return server_process and server_process.poll() is None

def extract_player_name(log_line: str) -> str:
    # Remove timestamp if present
    clean_line = log_line.split('] ')[-1] if ']' in log_line else log_line
    
    # Handle all possible formats:
    # 1. "Notch joined the game"
    # 2. "Player Notch joined the game"
    # 3. "[Notch] left the game"
    # 4. "[Server thread/INFO]: Notch joined the game"
    # 5. "<Notch> message"
    
    try:
        # Case 4: Server thread format
        if 'INFO]:' in clean_line:
            clean_line = clean_line.split('INFO]: ')[1]
        
        parts = clean_line.split()
        
        # Case 2: "Player Name..."
        if parts[0] == "Player":
            return parts[1]
        
        # Case 1/3: "Name..." or "[Name]..."
        if parts[1] in ["joined", "left"]:
            return parts[0].strip('[]')  # Handles both "Name" and "[Name]"
        
        # Case 5: Chat format
        if clean_line.startswith('<') and '>' in clean_line:
            return clean_line.split('>')[0][1:]
        
    except Exception:
        pass

    return "Unknown Player"  # Fallback

def extract_achievement(log_line: str) -> str:
    # Example lines:
    # "Notch has made the advancement [Diamonds!]"
    # "Notch has completed the challenge [Monster Hunter]"
    
    if 'made the advancement' in log_line:
        achievement = log_line.split('[', 1)[1].split(']')[0]
        return f"made the advancement **{achievement}**"
    
    if 'completed the challenge' in log_line:
        challenge = log_line.split('[', 1)[1].split(']')[0]
        return f"completed the challenge **{challenge}**"
    
    # For other types of achievements
    if 'has reached the goal' in log_line:
        goal = log_line.split('[', 1)[1].split(']')[0]
        return f"reached the goal **{goal}**"
    
    return "earned an achievement"  # Fallback

async def forward_output(channel):
    log_dir = os.path.join(config['minecraft_server_path'], 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"server_{datetime.now().strftime('%Y-%m-%d')}.log")
    
    with open(log_file, 'a') as f:
        while True:
            if server_process and not server_process.poll():
                line = await bot.loop.run_in_executor(
                    None,
                    lambda: server_process.stdout.readline()
                )
                
                if line:
                    # Write raw log to file
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {line}")
                    f.flush()

                    lower_line = line.lower()
                    
                    # Player Join
                    if "joined the game" in lower_line:
                        player = extract_player_name(line)
                        embed = discord.Embed(
                            title=f"🎮 {player} Joined",
                            description=f"**{player}** has entered the server ;)",
                            color=0x55ff55
                        )
                        await channel.send(embed=embed)
                    
                    # Player Leave
                    elif "left the game" in lower_line:
                        player = extract_player_name(line)
                        embed = discord.Embed(
                            title=f"🚪 {player} Left",
                            description=f"**{player}** has left the server ;(",
                            color=0xffaa55
                        )
                        await channel.send(embed=embed)
                    
                    # Achievements
                    elif any(x in lower_line for x in ["made the advancement", "completed the challenge"]):
                        player = extract_player_name(line)
                        achievement = extract_achievement(line)
                        embed = discord.Embed(
                            title=f"🏆 {player}'s Achievement",
                            description=achievement,
                            color=0x55aaff
                        )
                        embed.set_thumbnail(url="https://i.imgur.com/C7TAKlP.jpeg")
                        await channel.send(embed=embed)
                    
                    # Death Messages
                    elif "was slain by" in lower_line or "fell from" in lower_line:
                        embed = discord.Embed(
                            description=f"`💀 {line.strip()}`",
                            color=0x992d22
                        )
                        await channel.send(embed=embed)
                    
                    # Server Start/Stop
                    elif "done" in lower_line:
                        await channel.send("🟢 **server is now online!** `(｡•̀ᴗ-)✧`")
                    elif "stopping server" in lower_line:
                        await channel.send("🔴 **server is shutting down...** `(˘･_･˘)`")
                    
                    # Errors
                    elif any(x in lower_line for x in ["error", "exception", "crash"]):  # no "warn" for now
                        embed = discord.Embed(
                            title="⚠️ Server Alert",
                            description=f"```{line.strip()}```",
                            color=0xff5555
                        )
                        await channel.send(embed=embed)
            
            await asyncio.sleep(0.1)

@bot.command(name='start')
async def start_server(ctx):
    global server_process
    
    if is_server_running():
        await ctx.send("server is already running! >:(")
        return
    
    try:
        os.chdir(config['minecraft_server_path'])
        cmd = ['java']
        if 'java_args' in config:
            cmd.extend(config['java_args'].split())
        cmd.extend(['-jar', config['server_jar'], 'nogui'])
        
        server_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        await ctx.send(f"server starting in directory: `{os.getcwd()}`")

        # Start the output handler for this server instance
        bot.loop.create_task(forward_output(ctx.channel))
        
    except Exception as e:
        await ctx.send(f"failed to start server: {str(e)}")

@bot.command(name='stop')
async def stop_server(ctx):
    global server_process
    
    if not is_server_running():
        await ctx.send("server is not running! >:(")
        return
    
    try:
        server_process.stdin.write("stop\n")
        server_process.stdin.flush()
        await ctx.send("server stopping...")

    except Exception as e:
        await ctx.send(f"failed to stop server: {str(e)}")
        print(f"error stopping server: {e}")

@bot.command(name='restart')
async def restart_server(ctx):
    if is_server_running():
        await stop_server(ctx)
        await asyncio.sleep(5)  # Wait for server to stop

    await start_server(ctx)

@bot.command(name='status')
async def server_status(ctx):
    if is_server_running():
        await ctx.send("🟢 server is running :3")
    else:
        await ctx.send("🔴 server is not running :(")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    await ctx.send(f"An error occurred: {str(error)}")

bot.run(config['discord_token'])