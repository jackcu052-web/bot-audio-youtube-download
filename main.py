import discord
from discord import app_commands
import yt_dlp
import os
import tempfile
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("Thiếu DISCORD_TOKEN trong Secrets!")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Cấu hình yt-dlp tải audio MP3
YDL_OPTS = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'ignoreerrors': True,
    'no_check_certificate': True,
}

# Lệnh /download
@tree.command(
    name='download',
    description='Tải audio từ YouTube về dạng MP3'
)
@app_commands.describe(
    link='Link YouTube (ví dụ: https://youtu.be/xxx hoặc https://www.youtube.com/watch?v=xxx)'
)
async def download_audio(
    interaction: discord.Interaction,
    link: str
):
    await interaction.response.defer(thinking=True)

    # Kiểm tra link
    if not link.startswith(('http://', 'https://')):
        await interaction.followup.send("❌ Link không hợp lệ. Vui lòng nhập URL YouTube bắt đầu bằng http:// hoặc https://")
        return

    try:
        await interaction.followup.send(f"⏳ Đang tải audio từ YouTube...\n🔗 {link}")

        # Tải audio bằng yt-dlp
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(link, download=True)
            title = info.get('title', 'audio')
            # Lấy đường dẫn file MP3
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            # Kiểm tra file tồn tại
            if not os.path.exists(file_path):
                # Tìm file MP3 trong thư mục temp
                temp_dir = tempfile.gettempdir()
                for f in os.listdir(temp_dir):
                    if f.endswith('.mp3') and title in f:
                        file_path = os.path.join(temp_dir, f)
                        break

        # Gửi file MP3 về Discord
        await interaction.followup.send(
            f"✅ **Tải thành công!**\n"
            f"🎵 **Tên:** {title}\n"
            f"📁 **Định dạng:** MP3 (192kbps)",
            file=discord.File(file_path, filename=f"{title}.mp3")
        )

        # Xóa file tạm sau khi gửi
        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi tải audio: {str(e)}")

# Lệnh /download_with_bpm (tùy chọn thêm BPM)
@tree.command(
    name='download_bpm',
    description='Tải audio từ YouTube và điều chỉnh BPM'
)
@app_commands.describe(
    link='Link YouTube',
    bpm='BPM mong muốn (mặc định: 120)'
)
async def download_audio_with_bpm(
    interaction: discord.Interaction,
    link: str,
    bpm: float = 120.0
):
    await interaction.response.defer(thinking=True)

    if not link.startswith(('http://', 'https://')):
        await interaction.followup.send("❌ Link không hợp lệ.")
        return

    try:
        await interaction.followup.send(f"⏳ Đang tải và xử lý audio từ YouTube...")
        
        # Tải audio
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(link, download=True)
            title = info.get('title', 'audio')
            file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

        # (Tùy chọn) Xử lý BPM ở đây nếu cần
        # Hiện tại chỉ gửi file MP3 với thông báo BPM

        await interaction.followup.send(
            f"✅ **Tải thành công!**\n"
            f"🎵 **Tên:** {title}\n"
            f"🎵 **BPM:** {bpm}\n"
            f"📁 **Định dạng:** MP3 (192kbps)",
            file=discord.File(file_path, filename=f"{title}.mp3")
        )

        try:
            os.remove(file_path)
        except:
            pass

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi: {str(e)}")

# Khởi chạy bot
@client.event
async def on_ready():
    await tree.sync()
    print(f'✅ Bot đã sẵn sàng!')
    print(f'📋 Guilds: {len(client.guilds)}')
    commands = await tree.fetch_commands()
    print(f'📋 Lệnh đã đồng bộ: {[cmd.name for cmd in commands]}')

if __name__ == '__main__':
    client.run(TOKEN)
