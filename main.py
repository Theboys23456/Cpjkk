import os
import requests
import m3u8
from pyrogram import Client, filters
from pyrogram.types import Message
from Crypto.Cipher import AES

BOT_TOKEN = os.environ.get("8078418472:AAHN802dzlaLZX2D9g3URDTlic6W7IX0Fb4")
API_ID = int(os.environ.get("21567814"))
API_HASH = os.environ.get("cd7dc5431d449fd795683c550d7bfb7e")

bot = Client("classx_drm_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@bot.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply("👋 Send /download <m3u8_url> to get the decrypted ClassX video.")

@bot.on_message(filters.command("download"))
async def download(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a `.m3u8` link.")

    m3u8_url = message.command[1]
    await message.reply("🔄 Downloading and decrypting...")

    try:
        os.makedirs("segments", exist_ok=True)
        playlist = m3u8.load(m3u8_url)
        key_url = playlist.keys[0].uri
        key = requests.get(key_url).content
        segments = playlist.segments

        for i, segment in enumerate(segments):
            uri = segment.absolute_uri
            iv = segment.key.iv
            if iv is None:
                iv = (i+1).to_bytes(16, byteorder='big')
            else:
                iv = bytes.fromhex(iv.replace("0x", "").zfill(32))
            enc_data = requests.get(uri).content
            cipher = AES.new(key, AES.MODE_CBC, iv)
            dec_data = cipher.decrypt(enc_data)
            with open(f"segments/seg_{i:05d}.ts", "wb") as f:
                f.write(dec_data)

        with open("output.ts", "wb") as merged:
            for i in range(len(segments)):
                with open(f"segments/seg_{i:05d}.ts", "rb") as f:
                    merged.write(f.read())

        os.system("ffmpeg -y -i output.ts -c copy final_video.mp4")
        await message.reply_document("final_video.mp4", caption="✅ Your decrypted video")

    except Exception as e:
        await message.reply(f"❌ Error: {e}")
    finally:
        for f in ["output.ts", "final_video.mp4"]:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists("segments"):
            for seg in os.listdir("segments"):
                os.remove(os.path.join("segments", seg))
            os.rmdir("segments")

bot.run()
