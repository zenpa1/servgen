# -- MINECRAFT SERVER COMMANDS --
import discord
from discord.ext import bridge, commands
from utils.server import status_server, start_server, stop_server, restart_server

class Minecraft(commands.Cog):
    def __init__(self, bot):  # Called when cog is loaded
        self.bot = bot

    # Server status command
    @bridge.bridge_command(name="status", description="Check server status.")
    async def status(self, ctx):
        try:
            print("⏳ Checking server status")
            await status_server(ctx)
        except Exception as e:
            await ctx.send(f"🔴 Failed to check server status: {str(e)}")

    # Server start command
    @bridge.bridge_command(name="start", description="Start the server.")
    async def start(self, ctx):
        try:
            print("⏳ Attempting to start server.")
            await ctx.respond("⏳ Starting server...")
            await start_server(ctx)
        except Exception as e:
            await ctx.send(f"🔴 Failed to start server: {str(e)}")

    # Server stop command
    @bridge.bridge_command(name="stop", description="Stop the server.")
    async def stop(self, ctx):
        try: 
            print("⏳ Attempting to stop server.")
            await ctx.respond("⏳ Stopping server...")
            await stop_server(ctx)
        except Exception as e:
            await ctx.send(f"🔴 Failed to stop server: {str(e)}")

    # Server restart command
    @bridge.bridge_command(name="restart", description="Restart the server.")
    async def restart(self, ctx):
        try:
            print("⏳ Attempting to restart server.")
            await ctx.respond("⏳ Restarting server...")
            await restart_server(ctx)
        except Exception as e:
            await ctx.send(f"🔴 Failed to restart server: {str(e)}")

def setup(bot):  # Setup cog
    bot.add_cog(Minecraft(bot))  # Add cog to bot