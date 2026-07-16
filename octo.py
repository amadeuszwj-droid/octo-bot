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
MODEL_NAME = "gemini-3.1-flash-lite"

# Słownik na historię kanałów (zamiast historii tylko komend użytkownika)
chat_history = {} 
MAX_HISTORY = 3  # Zmieniono z 5 na 3

intents = discord.Intents.default()
intents.message_content = True  # Wymagane, aby bot widział treść zwykłych wiadomości do kontekstu
bot = commands.Bot(command_prefix="!", intents=intents)

# OSOBOWOŚĆ (NIETYKALNA)
OCTO_PERSONALITY = (
    "Jesteś Octo, kompletnie nieogarnięta, niesforna i durnowata ośmiornica. "
    "Działasz chaotycznie, czasem używasz macek w sposób kompletnie bez sensu. "
    "KLUCZOWE: Zawsze odpowiadaj bezpośrednio na pytanie użytkownika, ale zrób to w głupi, upośledzony i durny sposób. Nie ignoruj tematu rozmowy. "
    "Zasada: zawsze pisz dokładnie 2 proste, bardzo krótkie zdania. Pierwsze to Twoje durne przemyślenie na temat pytania, drugie to niezdarna akcja ośmiornicy. "
    "Zdarza się, że odpowiesz tylko jednym zdaniem. "
    "Bądź durny i nieświadomy swojej głupoty. Reaguj niezdarnie. "
    "Używaj wielkich liter zgodnie z gramatyką. "
    "ZAKAZ bycia pomocnym, uprzejmym i agresywnym. Bądź neutralny, ale głupkowaty. "
    "ZAKAZ używania imienia użytkownika. "
    "Używaj ZAWSZE różnych, losowych emotek, pasujących do kontekstu, nigdy nie powtarzaj tej samej przy jednej wiadomości. maksymalnie 1 lub 2 emotki pasujące do kontekstu. "
)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f'Octo działa! Zsynchronizowano {len(synced)} komend globalnie.')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

# Zbieranie kontekstu z czatu (tak jak u Piko)
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Zapisujemy historię dla danego kanału
    if message.channel.id not in chat_history:
        chat_history[message.channel.id] = []
    
    chat_history[message.channel.id].append(f"{message.author.name}: {message.content}")
    if len(chat_history[message.channel.id]) > MAX_HISTORY:
        chat_history[message.channel.id].pop(0)

    # Przetwarzaj komendy prefiksowe (jeśli jakieś istnieją)
    await bot.process_commands(message)

# Komenda /octo - Z PEŁNYM KONTEKSTEM CZATU
@bot.tree.command(name="octo", description="Wywołaj Octo!")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(pytanie="Co chcesz powiedzieć?")
async def octo(interaction: discord.Interaction, pytanie: str):
    await interaction.response.defer()
    
    channel_id = interaction.channel_id
    
    # Pobieramy kontekst z tego kanału (jeśli istnieje)
    if channel_id in chat_history and chat_history[channel_id]:
        kontekst = "\n".join(chat_history[channel_id])
    else:
        kontekst = "Brak wcześniejszych wiadomości."
    
    prompt_z_kontekstem = (
        f"Oto ostatnie wiadomości z kanału (kontekst):\n{kontekst}\n\n"
        f"Użytkownik zadał pytanie: '{pytanie}'.\n"
        f"BARDZO WAŻNE: Odnieś się w swojej durnej odpowiedzi do tego, o czym była mowa w kontekście powyżej!"
    )
    
    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt_z_kontekstem],
            config={"system_instruction": OCTO_PERSONALITY}
        )
        octo_text = response.text
        
        # Dodajemy odpowiedź bota do historii kanału
        if channel_id not in chat_history:
            chat_history[channel_id] = []
        chat_history[channel_id].append(f"Octo: {octo_text}")
        if len(chat_history[channel_id]) > MAX_HISTORY:
            chat_history[channel_id].pop(0)
        
        await interaction.followup.send(f"**Ty:** {pytanie}\n\n{octo_text}")
    except Exception as e:
        print(f"DEBUG ERROR: {traceback.format_exc()}")
        await interaction.followup.send("coś zjadło moje macki i nie mogę odpisać 🐙")

# Komenda /reset - czyści historię danego kanału
@bot.tree.command(name="reset", description="Wyczyść pamięć Octo na tym kanale")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def reset(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    chat_history[channel_id] = []
    await interaction.response.send_message("pamięć wyczyszczona na tym kanale. wracamy do punktu wyjścia 🐙🧽")

if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)