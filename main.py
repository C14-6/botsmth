
from keep_alive import keep_alive
keep_alive()

import discord
from discord.ext import commands
import asyncio
from aiohttp import web
import os

# Initialize the bot
bot = commands.Bot(command_prefix="!", self_bot=True, help_command=None)

# --- ASYNC WEB SERVER SETUP (for UptimeRobot) ---
async def handle_health_check(request):
    """Simple endpoint for UptimeRobot to ping."""
    return web.Response(text="Selfbot is alive!")

async def start_web_server():
    """Start the aiohttp web server in the same event loop."""
    app = web.Application()
    app.router.add_get('/', handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("[INFO] Async web server started on port 8080 for UptimeRobot.")
    return runner, site

@bot.event
async def on_ready():
    print(f'[SUCCESS] Logged in as: {bot.user}')
    
    YOUR_GUILD_ID = 123456789012345678   # REPLACE THIS
    YOUR_VOICE_CHANNEL_ID = 123456789012345679  # REPLACE THIS

    target_guild = bot.get_guild(YOUR_GUILD_ID)
    if not target_guild:
        print("[ERROR] Could not find the server.")
        return

    target_channel = target_guild.get_channel(YOUR_VOICE_CHANNEL_ID)
    if not isinstance(target_channel, discord.VoiceChannel):
        print("[ERROR] The channel ID is not for a voice channel.")
        return

    print(f"[INFO] Attempting to join: {target_channel.name}")
    try:
        # Connect with deafen and mute
        vc = await target_channel.connect(self_deaf=True, self_mute=True)
        print(f"[SUCCESS] Connected to voice channel (Deafened & Muted)!")
        
        # Main loop to keep connection alive
        while True:
            await asyncio.sleep(30)  # Check every 30 seconds instead of 10
            
            # Restart silent audio if it stopped (prevents auto-disconnect)
            if not vc.is_playing():
                # Create silent audio source
                vc.play(discord.FFmpegPCMAudio(
                    'pipe:0',
                    before_options='-f lavfi -i anullsrc=r=44100:cl=stereo',
                    options='-vn'
                ))
                print("[INFO] Restarted silent audio stream")
            
            # Reconnect if disconnected
            if not vc.is_connected():
                print("[WARNING] Disconnected. Reconnecting...")
                try:
                    vc = await target_channel.connect(self_deaf=True, self_mute=True)
                except Exception as e:
                    print(f"[ERROR] Reconnect failed: {e}")
                    await asyncio.sleep(10)
                    
    except discord.errors.ClientException as e:
        print(f"[ERROR] Connection failed: {e}.")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

async def main():
    """Main function to start both the web server and Discord bot."""
    # Start web server first
    web_runner, web_site = await start_web_server()
    
    try:
        # Start Discord bot
        TOKEN = os.environ['DISCORD_TOKEN']
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    finally:
        # Cleanup
        await bot.close()
        await web_runner.cleanup()

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())