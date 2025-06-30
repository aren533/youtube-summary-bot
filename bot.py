import os
import yt_dlp
import requests
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

openai.api_key = os.getenv("OPENAI_API_KEY")

# Получение URL субтитров через yt-dlp
def get_subtitle_url(video_url):
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return info['automatic_captions']['en'][0]['url']

# Загрузка субтитров
def download_subtitles(sub_url):
    resp = requests.get(sub_url)
    data = resp.json()
    segments = []
    for event in data.get('events', []):
        if 'segs' in event:
            for seg in event['segs']:
                segments.append(seg.get('utf8', ''))
    return ' '.join(segments)

# Генерация саммари
def summarize(text):
    messages = [
        {"role": "system", "content": "Ты кратко пересказываешь видео с YouTube."},
        {"role": "user", "content": f"Сделай саммари для этого текста: {text}"}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        max_tokens=500
    )
    return response.choices[0].message.content

# Обработка команды /summary
async def summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        video_url = context.args[0]
        await update.message.reply_text("⏳ Получаю субтитры...")
        sub_url = get_subtitle_url(video_url)
        text = download_subtitles(sub_url)
        await update.message.reply_text("🧠 Генерирую саммари...")
        result = summarize(text)
        await update.message.reply_text("✅ Саммари:\n" + result)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

# Запуск бота
if __name__ == "__main__":
    from telegram.ext import ApplicationBuilder

    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(telegram_token).build()
    app.add_handler(CommandHandler("summary", summary_handler))
    app.run_polling()
