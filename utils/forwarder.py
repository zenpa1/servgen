# -- CONSOLE FORWARDER --
import asyncio
from datetime import datetime
import discord
import json
import os
from pathlib import Path

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# List of events
events = [
    "joined",  # Players joining
    "left",  # Players leaving
    "has",  # Players getting an achievement
    "was",  # Death messages
    "fell",
    "burned",
]

# Name extractor
def extract_player_name(log_line: str) -> str:
    # Remove timestamp if present
    clean_line = log_line.split('] ')[-1] if ']' in log_line else log_line

    try:
        # Case 1: [Server thread/INFO]: Notch joined the game
        if 'INFO]:' in clean_line:
            clean_line = clean_line.split('INFO]: ')[1]
        
        parts = clean_line.split()
        
        # Case 2: Player Notch joined the game
        if parts[0] == "Player":
            return parts[1]
        
        # Case 3/4: Notch/[Notch] joined the game
        if parts[1] in events:
            return parts[0].strip('[]')  # Handles both "Name" and "[Name]"
        
        # Case 5: <Notch> message
        if clean_line.startswith('<') and '>' in clean_line:
            return clean_line.split('>')[0][1:]
        
    except Exception:
        pass

    return "Unknown Player"  # Fallback

# Achievement extractor
def extract_achievement(log_line: str) -> str:

    try:
        # Notch has made the advancement [Diamonds!]
        if 'has made the advancement' in log_line:
            achievement = log_line.rsplit('[', 1)[1].split(']')[0]
            return f"made the advancement **{achievement}**"
        
        # Notch has completed the challenge [Monster Hunter]
        if 'has completed the challenge' in log_line:
            challenge = log_line.rsplit('[', 1)[1].split(']')[0]
            return f"completed the challenge **{challenge}**"
        
        # For other types of achievements
        if 'has reached the goal' in log_line:
            goal = log_line.rsplit('[', 1)[1].split(']')[0]
            return f"reached the goal **{goal}**"
    
    except Exception:
        pass
    
    return "earned an achievement"  # Fallback

# Forwards console output to terminal, logs (todo), and Discord
async def forward_output(channel, process):
    # Server logging (found in your server folder)
    log_dir = os.path.join(config['minecraft_server_path'], 'logs')  # Combine into a single path
    os.makedirs(log_dir, exist_ok=True)  # Creates a directory if none
    log_file = os.path.join(log_dir, f"server_{datetime.now().strftime('%Y-%m-%d')}.log")  # Create a log file

    # Get path relative to bot location (for thumbnails, optional)
    # assets_dir = Path(__file__).parent.parent / "assets"  # file -> utils -> servgen / assets

    try:
        async for line in process.stdout:
            try:
                decoded = line.decode().strip()
                lower_line = decoded.lower()

                # Print to terminal
                print(f"🖥️  Server: {decoded}")

                # Write to log file (todo)
                await asyncio.to_thread(
                    lambda: open(log_file, 'a').write(f"{decoded}\n")
                )

                # Forward to Discord
                # Player Join
                if "joined the game" in lower_line:
                    # image_path = assets_dir / "player_joined.jpg"
                    player = extract_player_name(decoded)

                    # Create embed
                    embedVar = discord.Embed(
                         title=f"🎮 {player} joined the server!",
                        description=f"Join us at **{str(config['server_address'])}**!",
                        color=0x00ffff
                    )

                    # fileVar = discord.File(image_path, filename=image_path.name)
                    # embedVar.set_thumbnail(url=f"attachment://{image_path.name}")
                    # await channel.send(file=fileVar, embed=embedVar)
                    await channel.send(embed=embedVar)

                # Player Leave
                elif "left the game" in lower_line:
                    # image_path = assets_dir / "player_left.jpg"
                    player = extract_player_name(decoded)

                    # Create embed
                    embedVar = discord.Embed(
                        title=f"👋 {player} left the server!",
                        description=f"Join us at **{str(config['server_address'])}**!",
                        color=0xffaa55
                    )

                    # fileVar = discord.File(image_path, filename=image_path.name)
                    # embedVar.set_thumbnail(url=f"attachment://{image_path.name}")
                    # await channel.send(file=fileVar, embed=embedVar)
                    await channel.send(embed=embedVar)

                # Player Achievement
                elif "made the advancement" in lower_line or "completed the challenge" in lower_line or "has reached the goal" in lower_line:
                    # image_path = assets_dir / "player_achievement.jpg"
                    player = extract_player_name(decoded)
                    achievement = extract_achievement(decoded)

                    # Create embed
                    embedVar = discord.Embed(
                        title=f"🏆 {player} got an achievement!",
                        description=f"{player} {achievement}!",
                        color=0x55aaff
                    )

                    # fileVar = discord.File(image_path, filename=image_path.name)
                    # embedVar.set_thumbnail(url=f"attachment://{image_path.name}")
                    # await channel.send(file=fileVar, embed=embedVar)
                    await channel.send(embed=embedVar)

                # Player Death
                elif "was slain by" in lower_line or "fell from" in lower_line or "burned" in lower_line:
                    # image_path = assets_dir / "player_death.jpg"
                    player = extract_player_name(decoded)

                    # Create embed
                    embedVar = discord.Embed(
                        title=f"💀 {player} died!",
                        description=f"💀 {decoded}",
                        color=0xff4500
                    )

                    # fileVar = discord.File(image_path, filename=image_path.name)
                    # embedVar.set_thumbnail(url=f"attachment://{image_path.name}")
                    # await channel.send(file=fileVar, embed=embedVar)
                    await channel.send(embed=embedVar)

                # Server Start
                elif 'done' in lower_line:
                    # Create embed
                    embedVar = discord.Embed(
                        title=f"🟢 Server is now online! (˶ˆᗜˆ˵)",
                        description=f"Join us at **{str(config['server_address'])}**!",
                        color=0x00ff00
                    )
                    await channel.send(embed=embedVar)

                # Server Stop
                elif "all dimensions are saved" in lower_line:
                    # Create embed
                    embedVar = discord.Embed(
                        title=f"🔴 Server is now offline! (っ˕ -｡)",
                        description=f"Join us at **{str(config['server_address'])}**!",
                        color=0xff0000
                    )
                    await channel.send(embed=embedVar)

                # Warnings/Errors
                elif any(x in lower_line for x in ["error", "exception", "crash"]):
                    # Create embed
                    embedVar = discord.Embed(
                        title="⚠️ Server Alert",
                        description=f"```{decoded}```",
                        color=0xff5555
                    )

                    await channel.send(embed=embedVar)
            except Exception as e:
                print(f"🔴 Error processing line: {e}")
    except Exception as e:
        print(f"🔴 Output handler crashed: {str(e)}")
        await channel.send(f"🔴 Output forwarding stopped! Error: {e}")