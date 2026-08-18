import discord
from discord.ext import commands
import yt_dlp
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")  # Đặt biến môi trường trên Replit

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Cấu hình yt-dlp để tải audio [citation:6][citation:5]
ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': 'audio.%(ext)s',
    'quiet': True,
    'no_warnings': True,
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

@bot.command(name='play', aliases=['p'])
async def play(ctx, *, query: str):
    """Phát nhạc từ YouTube trong voice channel"""
    if not ctx.author.voice:
        await ctx.send("Bạn phải ở trong voice channel!")
        return
    
    voice_client = ctx.voice_client
    if not voice_client:
        voice_client = await ctx.author.voice.channel.connect()
    
    await ctx.send(f"⏳ Đang tìm kiếm: {query}...")
    
    # Tìm video trên YouTube
    ydl_opts = {'quiet': True, 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            url = info['entries'][0]['webpage_url']
            title = info['entries'][0]['title']
        except Exception as e:
            await ctx.send(f"❌ Không tìm thấy video: {e}")
            return
    
    # Tải audio
    await ctx.send(f"🎵 Đang tải: **{title}**...")
    with yt_dlp.YoutubeDL(ytdl_format_options) as ydl:
        try:
            ydl.download([url])
        except Exception as e:
            await ctx.send(f"❌ Lỗi tải audio: {e}")
            return
    
    # Phát audio
    audio_source = discord.FFmpegPCMAudio('audio.mp3', **ffmpeg_options)
    voice_client.play(audio_source, after=lambda e: os.remove('audio.mp3'))
    await ctx.send(f"▶️ Đang phát: **{title}**")

@bot.command(name='stop', aliases=['disconnect', 'dc'])
async def stop(ctx):
    """Ngắt kết nối và dừng phát"""
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("⏹️ Đã ngắt kết nối.")
    else:
        await ctx.send("Bot không ở trong voice channel.")

@bot.command(name='skip')
async def skip(ctx):
    """Bỏ qua bài hát hiện tại"""
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Đã bỏ qua bài hát.")
    else:
        await ctx.send("Không có bài hát nào đang phát.")

@bot.event
async def on_ready():
    print(f'✅ Bot đã sẵn sàng! Tên: {bot.user}')

bot.run(TOKEN)
