import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from flask import Flask
from threading import Thread

# Flask dla utrzymania serwera na Renderze
app = Flask('')
@app.route('/')
def home():
    return "Octo żyje i działa!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Konfiguracja
DISCORD_TOKEN = os.environ.get("OCTO_DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
ai_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-1.5-flash" # Upewnij się, że ten model jest obsługiwany w Twoim regionie

# Pamięć w RAM
user_history = {} 
MAX_HISTORY = 5

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

OCTO_PERSONALITY = (
    "Jesteś Octo, kompletnie nieogarnięta, niesforna i durnowata ośmiornica. "
    "Działasz chaotycznie, czasem używasz macek w sposób kompletnie bez sensu. "
    "Zasada: zawsze pisz 2 proste, urywane bardzo krótkie zdania. Pierwsze to Twoje głupie przemyślenie, drugie to niezdarna akcja ośmiornicy. "
    "Zdarza się, że odpowiesz tylko jednym zdaniem. "
    "Bądź durny i nieświadomy swojej głupoty. Reaguj niezdarnie. Piszesz z perspektywy ośmiornicy, która wszystko rozumie źle. "
    "ZAKAZ używania wielkich liter na początku zdań. "
    "ZAKAZ bycia uprzejmym i agresywnym. Bądź neutralny, ale głupkowaty "
    "ZAKAZ używania imienia użytkownika. "
    "Używaj ZAWSZE różnych, losowych emotek, nigdy nie powtarzaj tej samej przy jednej wiadomości. maksymalnie 1 lub 2 emotki pasujące do kontekstu "
)

@bot.event
async def on_ready():
    # Synchronizacja komend globalnie dla instalacji użytkownika
    try:
        synced = await bot.tree.sync()
        print(f'Octo działa! Zsynchronizowano {len(synced)} komend globalnie.')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

# Komenda /octo
@bot.tree.command(name="octo", description="Wywołaj Octo!")
@app_commands.describe(pytanie="Co chcesz powiedzieć?")
async def octo(interaction: discord.Interaction, pytanie: str):
    # Pobranie nazwy użytkownika (obsługa DM)
    user_name = interaction.user.global_name or interaction.user.name
    
    # Używamy defer, aby uniknąć błędu "Interakcja nie powiodła się" podczas myślenia AI
    await interaction.response.defer()
    
    user_id = interaction.user.id
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append(f"Ty: {pytanie}")
    if len(user_history[user_id]) > MAX_HISTORY:
        user_history[user_id].pop(0)
    
    kontekst = "\n".join(user_history[user_id])
    
    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Historia ostatnich komend:\n{kontekst}\n\nOdpowiedz na: {pytanie}",
            config={"system_instruction": OCTO_PERSONALITY}
        )
        user_history[user_id].append(f"Octo: {response.text}")
        await interaction.followup.send(f"**{user_name} pyta:** {pytanie}\n\n{response.text}")
    except Exception as e:
        await interaction.followup.send(f"Oj, jedna z moich macek się zaplątała! 🐙")

# Komenda /reset
@bot.tree.command(name="reset", description="Wyczyść pamięć Octo")
async def reset(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in user_history:
        user_history[user_id] = []
    await interaction.response.send_message("Pamięć wyczyszczona! Wracamy do punktu wyjścia. 🐙🧽")

if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)