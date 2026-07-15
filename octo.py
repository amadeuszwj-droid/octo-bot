import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from flask import Flask
from threading import Thread
import traceback

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
MODEL_NAME = "gemini-1.5-flash"

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
    "Używaj ZAWSZE różnych, losowych emotek, pasujących do kontekstu, nigdy nie powtarzaj tej samej przy jednej wiadomości. maksymalnie 1 lub 2 emotki pasujące do kontekstu "
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
    # Pobranie nazwy użytkownika (bezpieczna wersja dla wiadomości prywatnych DM)
    user_name = interaction.user.global_name or interaction.user.name
    
    # Używamy defer, aby uniknąć błędu "Interakcja nie powiodła się" podczas oczekiwania na Gemini
    await interaction.response.defer()
    
    user_id = interaction.user.id
    if user_id not in user_history:
        user_history[user_id] = []
    
    user_history[user_id].append(f"Ty: {pytanie}")
    if len(user_history[user_id]) > MAX_HISTORY:
        user_history[user_id].pop(0)
    
    kontekst = "\n".join(user_history[user_id])
    
    try:
        # Poprawiona składnia przesyłania treści (contents jako lista)
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=[f"Historia:\n{kontekst}\n\nOdpowiedz na: {pytanie}"],
            config={"system_instruction": OCTO_PERSONALITY}
        )
        octo_text = response.text
        user_history[user_id].append(f"Octo: {octo_text}")
        
        # Wyświetlanie Twojego pytania i odpowiedzi bota
        await interaction.followup.send(f"**Ty:** {pytanie}\n\n{octo_text}")
    except Exception as e:
        # Dokładny log błędu w konsoli Rendera, abyśmy od razu wiedzieli co jest nie tak
        print(f"DEBUG ERROR: {traceback.format_exc()}")
        await interaction.followup.send("coś zjadło moje macki i nie mogę odpisać 🐙")

# Komenda /reset
@bot.tree.command(name="reset", description="Wyczyść pamięć Octo")
async def reset(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_history[user_id] = []
    await interaction.response.send_message("pamięć wyczyszczona. wracamy do punktu wyjścia 🐙🧽")

if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)