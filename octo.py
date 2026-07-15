import os
import discord
from discord import app_commands
from google import genai
from flask import Flask
from threading import Thread

# Flask dla Rendera
app = Flask('')
@app.route('/')
def home():
    return "Octo z pamięcią i funkcją resetu!"

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

# Pamięć w RAM
user_history = {} 
MAX_HISTORY = 5

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

OCTO_PERSONALITY = (
    "Jesteś Octo, ośmiornica. Jesteś totalnym durniem, ale myślisz, że pomagasz. "
    "Zasada: pisz maksymalnie 1-2 krótkie, urywane zdania. "
    "ZAKAZ opisów, ZAKAZ używania słów typu 'ponieważ', 'więc', 'teraz'. "
    "ZAKAZ używania imienia użytkownika. "
    "ZAKAZ pisania wielkimi literami na początku zdań. "
    "Pisz jakbyś ledwo kojarzył fakty. "
    "Używaj różnych, losowych emotek. "
)

@bot.event
async def on_ready():
    await tree.sync()
    print(f'Octo działa z pamięcią i komendą /reset!')

# Komenda /octo
@tree.command(name="octo", description="Wywołaj Octo!")
@app_commands.describe(pytanie="Co chcesz powiedzieć?")
async def octo(interaction: discord.Interaction, pytanie: str):
    # Wysyłamy odpowiedź publiczną (ephemeral=False jest domyślne)
    user_name = interaction.user.nick or interaction.user.name
    await interaction.response.send_message(f"**{user_name} pyta:** {pytanie}\n\n*Octo myśli...*")
    
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
        # Edytujemy oryginalną wiadomość, aby zawierała odpowiedź
        await interaction.edit_original_response(content=f"**{user_name} pyta:** {pytanie}\n\n{response.text}")
    except Exception as e:
        await interaction.edit_original_response(content=f"**{user_name} pyta:** {pytanie}\n\nOj, jedna z moich macek się zaplątała! 🐙")

# Komenda /reset
@tree.command(name="reset", description="Wyczyść pamięć Octo")
async def reset(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id in user_history:
        user_history[user_id] = []
    await interaction.response.send_message("Pamięć wyczyszczona! Wracamy do punktu wyjścia. 🐙🧽")

if __name__ == "__main__":
    keep_alive() 
    bot.run(DISCORD_TOKEN)