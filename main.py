import os
import logging
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from moviepy.editor import VideoFileClip

# --- Web Server (Render အိပ်မပျော်အောင် လုပ်ခြင်း) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("မင်္ဂလာပါ! 👋\nRender Server ကနေ ကြိုဆိုပါတယ်။ Video ပို့လိုက်ပါ။")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📥 Downloading...")
    input_path = f"in_{update.message.id}.mp4"
    output_path = f"out_{update.message.id}.mp4"
    
    try:
        video_file = await update.message.video.get_file()
        await video_file.download_to_drive(input_path)
        
        await msg.edit_text("✂️ Processing...")
        clip = VideoFileClip(input_path)
        
        # Crop Logic
        w, h = clip.size
        target_ratio = 9/16
        if w/h > target_ratio:
            new_w = h * target_ratio
            crop_x = (w - new_w) / 2
            final_clip = clip.crop(x1=crop_x, width=new_w, height=h)
        else:
            final_clip = clip
            
        final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac", preset="ultrafast", bitrate="1000k")
        clip.close()
        final_clip.close()
        
        await msg.edit_text("📤 Uploading...")
        await update.message.reply_video(video=open(output_path, 'rb'), caption="✅ Done via Render!")
        
    except Exception as e:
        await msg.edit_text(f"Error: {e}")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

def main():
    # Render Setting ထဲက Token ကို လှမ်းယူမည်
    TOKEN = os.environ.get("BOT_TOKEN")
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.VIDEO, process_video))
    
    # Start Web Server
    keep_alive()
    
    # Start Bot
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
