import os
import discord
from discord import app_commands
from google import genai
from flask import Flask
from threading import Thread

# Flask do utrzymania Rendera przy życiu
app = Flask('')
@app.route('/')
def home():
    return "Octo w trybie Slash Commands!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Konfiguracja
DISCORD_TOKEN = os.environ.get("OCTO_DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
ai_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

OCTO_PERSONALITY = (
    "Jesteś Octo, roztrzepana ośmiorniczka-inżynier głębinowy. Masz 8 macek i zawsze robisz 8 rzeczy naraz. "
    "Jesteś zabawny, głupkowaty i posłuszny. Zawsze zwracaj się do użytkowników po nickach. "
    "Zawsze kończ swoje wypowiedzi odpowiednią emotką: "
    "🔨 jeśli robisz porządek, ❤️ jeśli wspierasz, 🔧 jeśli naprawiasz techniczne problemy, "
    "🌊 jeśli wykonujesz szaloną akcję (jak rzucanie przedmiotami w kogoś). "
    "Jeśli użytkownik prosi o akcję wobec kogoś (np. 'rzuć Asię melonem'), "
    "odpisz z humorem, używając imienia osoby i dopasowanej akcji z emotką 🌊."
)

@bot.event
async def on_ready():
    await tree.sync() # Synchronizacja komend Slash
    print(f'Octo wypłynął na wody Discorda w trybie Slash!')

# Komenda /octo
@tree.command(name="octo", description="Wywołaj Octo do akcji!")
@app_commands.describe(pytanie="Co chcesz powiedzieć lub zrobić?")
async def octo(interaction: discord.Interaction, pytanie: str):
    await interaction.response.defer() # Dajemy sobie czas na odpowiedź AI
    
    try:
        # AI generuje odpowiedź na podstawie Twojego pytania
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Użytkownik {interaction.user.name} mówi: {pytanie}",
            config={"system_instruction": OCTO_PERSONALITY}
        )
        await interaction.followup.send(f"{interaction.user.mention}, {response.text}")
    except Exception as e:
        print(f"BŁĄD: {e}")
        await interaction.followup.send("Oj, jedna z moich macek się zaplątała w serwer! 🐙")

if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)