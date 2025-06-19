# -- SERVER MANAGEMENT --
import asyncio
import json
import os
from utils.forwarder import forward_output

# Global variable to track server process
server_process = None

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Check if the server is running
def is_server_running():
    global server_process
    return server_process and server_process.returncode is None

# Checks server status
async def status_server(ctx):
    # Using the slash command expects an immediate response
    # For some reason, this takes too long, which outputs a "The application did not respond" error
    # Current solution is to handle in a special manner
    try: 
        # Check if slash command
        is_slash = hasattr(ctx, 'respond')

        if is_slash:
            await ctx.defer(ephemeral=False)  # Allows everyone to see status

        status = is_server_running()
        msg = ("🟢 Server is running!" if status
               else "🔴 Server is not running!")
        
        # Response based on command type
        if is_slash:
            await ctx.respond(msg)
        else:
            await ctx.send(msg)

    except Exception as e:
        error_msg = f"🔴 Failed to check status: {str(e)}"
        if is_slash:  # Slash command
            await ctx.respond(error_msg)
        else:  # Prefix command
            await ctx.send(error_msg)

# Function to start server
async def start_server(ctx):
    global server_process

    if is_server_running():
        await ctx.send("⚠️ Server is already running! (╥﹏╥)")
        return
    
    try:
        os.chdir(config['minecraft_server_path'])

        # Create console command
        cmd = ['java']
        if 'java_args' in config:
            cmd.extend(config['java_args'].split())
        cmd.extend(['-jar', config['server_jar'], 'nogui'])
        
        # Create server process
        server_process = await asyncio.create_subprocess_exec(
            *cmd,  # Unpack list
            stdin=asyncio.subprocess.PIPE,  # For console input
            stdout=asyncio.subprocess.PIPE,  # For console output
            stderr=asyncio.subprocess.PIPE,  # For console errors
        )

        print(f"⏳ Server starting in directory: `{os.getcwd()}`")

        # Start an output handler for server events
        asyncio.create_task(forward_output(ctx.channel, server_process))

    except Exception as e:
        await ctx.send(f"🔴 Failed to start server: {str(e)}")

# Function to stop server
async def stop_server(ctx):
    global server_process
    
    if not is_server_running():
        await ctx.send("⚠️ Server is not running! (╥﹏╥)")
        return
    
    try:
        server_process.stdin.write("stop\n".encode())  # Process reads bytes, not strings
        await server_process.stdin.drain()  # Wait for delivery

        try:
            await asyncio.wait_for(server_process.wait(), timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("🚨 Server didn't stop, terminating it. (๑•̀ᗝ•́)૭")
            server_process.kill()

    except Exception as e:
        await ctx.send(f"🔴 Failed to stop server: {str(e)}")

# Function to restart server
async def restart_server(ctx):
    global server_process

    if is_server_running():
        await stop_server(ctx)
        await ctx.send("⏳ Confirming server stop...")
        await asyncio.sleep(5)  # Wait for server to stop

    await start_server(ctx)