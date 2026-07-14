import os
import discord
from discord.ext import commands
from google import genai
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home():
    return "Octo naprawia kable w Rowie Mariańskim!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

DISCORD_TOKEN = os.environ.get("OCTO_DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
ai_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

chat_history = {}
MAX_HISTORY = 5

OCTO_PERSONALITY = (
    "Jesteś Octo, roztrzepana ośmiorniczka-inżynier głębinowy. Masz 8 macek i zawsze robisz 8 rzeczy naraz. "
    "Jesteś zabawny, głupkowaty i posłuszny. Zawsze zwracaj się do użytkowników po nickach. "
    "Dopasowuj emotki: 🔨 przy porządku, ❤️ przy wsparciu, 🔧 przy technice."
)

@bot.event
async def on_ready():
    print(f'Octo wypłynął na wody Discorda!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.id not in chat_history:
        chat_history[message.channel.id] = []
    chat_history[message.channel.id].append(f"{message.author.name}: {message.content}")
    if len(chat_history[message.channel.id]) > MAX_HISTORY:
        chat_history[message.channel.id].pop(0)

    msg_lower = message.content.lower()
    if "octo" in msg_lower or bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f'<@{bot.user.id}>', '').strip()
        kontekst = "\n".join(chat_history[message.channel.id])
        prompt_z_kontekstem = f"Historia: {kontekst}\n\nPolecenie od {message.author.name}: '{clean_prompt}'"

        async with message.channel.typing():
            try:
                response = ai_client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt_z_kontekstem,
                    config={"system_instruction": OCTO_PERSONALITY}
                )
                await message.reply(response.text)
            except Exception as e:
                await message.reply("Oj, jedna z moich macek się zaplątała w serwer! 🐙")

if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)