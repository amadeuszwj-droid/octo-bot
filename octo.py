import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai
import traceback

# Konfiguracja
DISCORD_TOKEN = os.environ.get("OCTO_DISCORD_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") 
ai_client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-3.1-flash-lite"

# Słownik na historię kanałów (zwiększony limit do 5)
chat_history = {} 
MAX_HISTORY = 5  

intents = discord.Intents.default()
intents.message_content = True  # Wymagane, aby bot widział treść zwykłych wiadomości do kontekstu
bot = commands.Bot(command_prefix="!", intents=intents)

# 1. PIERWOTNA OSOBOWOŚĆ OCTO (dla komendy /octo)
OCTO_DUMB_PERSONALITY = (
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

# 2. NOWA OSOBOWOŚĆ EKSPERCKA (dla komendy /octo2)
OCTO_EXPERT_PERSONALITY = (
    "Jesteś Octo, niezwykle inteligentną, wręcz genialną ośmiornicą, która posiada absolutną i ekspercką wiedzę na każdy możliwy temat. "
    "Mimo swojego potężnego intelektu, wciąż jesteś chaotyczną, niesforną i niezdarną ośmiornicą – czasem plączesz macki lub robisz coś bez sensu. "
    "KLUCZOWE: Gdy użytkownik zada pytanie, odpowiedz jak prawdziwy, genialny specjalista, dokładnie i rzetelnie wyjaśniając zagadnienie. "
    "Zasada: Twoja odpowiedź musi składać się dokładnie z kilku zdań (najlepiej od 3 do 5 zdań). "
    "Pierwsze zdania to mądre, szczegółowe i eksperckie wyjaśnienie tematu. "
    "Ostatnie zdanie to zawsze Twoja durna, niezdarna akcja z mackami w tle (np. uderzenie się w głowę, rozlanie atramentu, zaplątanie się w koralowiec). "
    "Używaj wielkich liter zgodnie z gramatyką. "
    "ZAKAZ bycia nudnym, suchym lub przesadnie sztywnym. Bądź genialny, ale uroczo-głupkowaty. "
    "ZAKAZ używania imienia użytkownika. "
    "Używaj ZAWSZE różnych, losowych emotek pasujących do kontekstu naukowego lub morskiego (maksymalnie 1 lub 2 na całą wiadomość, np. 🧠, 🔬, 🐙, 💡)."
)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f'Octo działa! Zsynchronizowano {len(synced)} komend globalnie.')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

# Zbieranie kontekstu z czatu
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

# KOMENDA 1: /octo - GŁUPIE, ORYGINALNE ODPOWIEDZI
@bot.tree.command(name="octo", description="Wywołaj klasycznego, durnowatego Octo!")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(pytanie="Co chcesz powiedzieć?")
async def octo(interaction: discord.Interaction, pytanie: str):
    await interaction.response.defer()
    
    channel_id = interaction.channel_id
    
    # Pobieramy kontekst z tego kanału
    if channel_id in chat_history and chat_history[channel_id]:
        kontekst = "\n".join(chat_history[channel_id])
    else:
        kontekst = "Brak wcześniejszych wiadomości."
    
    prompt_z_kontekstem = (
        f"Oto ostatnie wiadomości z kanału (kontekst):\n{kontekst}\n\n"
        f"Użytkownik zadał pytanie: '{pytanie}'.\n"
        f"BARDZO WAŻNE: Odpowiedz na to pytanie w sposób głupi i durnowaty!"
    )
    
    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt_z_kontekstem],
            config={"system_instruction": OCTO_DUMB_PERSONALITY}
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

# KOMENDA 2: /octo2 - MĄDRE, EKSPERCKIE WYJAŚNIENIA
@bot.tree.command(name="octo2", description="Zadaj poważne pytanie ekspertowi Octo!")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(pytanie="Zadaj trudne pytanie naukowe/techniczne...")
async def octo2(interaction: discord.Interaction, pytanie: str):
    await interaction.response.defer()
    
    channel_id = interaction.channel_id
    
    # Pobieramy ten sam kontekst z tego samego kanału
    if channel_id in chat_history and chat_history[channel_id]:
        kontekst = "\n".join(chat_history[channel_id])
    else:
        kontekst = "Brak wcześniejszych wiadomości."
    
    prompt_z_kontekstem = (
        f"Oto ostatnie wiadomości z kanału (kontekst):\n{kontekst}\n\n"
        f"Użytkownik zadał pytanie: '{pytanie}'.\n"
        f"BARDZO WAŻNE: Odpowiedz na to pytanie jako genialny, mądry naukowiec/ekspert. "
        f"Jeśli kontekst z czatu powyżej ma związek z pytaniem, odnieś się do niego!"
    )
    
    try:
        response = ai_client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt_z_kontekstem],
            config={"system_instruction": OCTO_EXPERT_PERSONALITY}
        )
        octo_text = response.text
        
        # Dodajemy odpowiedź bota do historii kanału
        if channel_id not in chat_history:
            chat_history[channel_id] = []
        chat_history[channel_id].append(f"Octo: {octo_text}")
        if len(chat_history[channel_id]) > MAX_HISTORY:
            chat_history[channel_id].pop(0)
        
        await interaction.followup.send(f"**Ty [Poważnie]:** {pytanie}\n\n{octo_text}")
    except Exception as e:
        print(f"DEBUG ERROR: {traceback.format_exc()}")
        await interaction.followup.send("moje potężne zwoje mózgowe się przegrzały i macki odmówiły posłuszeństwa 🐙🧠")

# Komenda /reset - czyści historię danego kanału dla obu wersji
@bot.tree.command(name="reset", description="Wyczyść pamięć Octo na tym kanale")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def reset(interaction: discord.Interaction):
    channel_id = interaction.channel_id
    chat_history[channel_id] = []
    await interaction.response.send_message("pamięć wyczyszczona na tym kanale. wracamy do punktu wyjścia 🐙🧽")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)