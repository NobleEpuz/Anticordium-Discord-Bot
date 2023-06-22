import discord
from discord.ext import commands
import json
import openai
import os

# Установите свой API-ключ от OpenAI
OPENAI_API_KEY = ''

intents = discord.Intents.all()
intents.messages = True

bot = commands.Bot(command_prefix='an!', intents=intents)
translator = Translator()

# Устанавливаем API-ключ OpenAI
openai.api_key = OPENAI_API_KEY
    
#Нейросеть для рисования на сервере pollinations
@bot.command()
async def draw(ctx, *, prompt):
    # Замена пробелов на знак "_"
    prompt = prompt.replace(" ", "-")
    # Отправка изображения пользователю, вызвавшему команду
    await ctx.send('https://image.pollinations.ai/prompt/' + prompt)

#Хэлп-команда
@bot.command()
async def commands(ctx):
    msg = '''an!commands - показывает данное сообщение
an!draw - рисует картинки по запросу
an!register - команда для создания паспорта пользователя
an!passport - показывает данные вашего паспорта
an!chat - спросить меня (ChatGPT)
an!wiki - позволяет смотреть википедию ||(для просмотра доступных статей - an!wiki list)||
an!sendmsg - отправить письмо пользователя ||(by Askiphy)||
an!clear - очистка сообщений в чате ||(по умолчанию будет очищаться 5 сообщении)||
an!about - о авторах бота'''
    await ctx.send(msg)

#Регистрация паспорта
@bot.command()
async def register(ctx):
    user_id = ctx.author.id
    
    # Проверяем, есть ли уже карточка пользователя
    try:
        with open(f"passports/{user_id}.json") as f:
            card_data = json.load(f)
    except FileNotFoundError:
        card_data = {"name": "", "age": 0, "gender": ""}
    
    # Спрашиваем у пользователя данные
    await ctx.send("Введите ваше имя:")
    name_response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    card_data["name"] = name_response.content
    
    await ctx.send("Введите ваш возраст:")
    age_response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    card_data["age"] = int(age_response.content)
    
    await ctx.send("Введите ваш пол:")
    gender_response = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    card_data["gender"] = gender_response.content
    
    # Сохраняем данные в файл
    if not os.path.exists("passports"):
        os.makedirs("passports")
        
    with open(f"passports/{user_id}.json", 'w') as f:
        json.dump(card_data, f)
        
    await ctx.send("Паспорт пользователя успешно создан!")

#Просмотр паспорта
@bot.command()
async def passport(ctx):
    user_id = ctx.author.id
    
    # Проверяем, есть ли карточка пользователя
    try:
        with open(f"passports/{user_id}.json") as f:
            card_data = json.load(f)
            
            name = card_data["name"]
            age = card_data["age"]
            gender = card_data["gender"]
            
        await ctx.send(f"<:name:1116708039546916945> Имя: {name}\n<:age:1116708055011307642> Возраст: {age}\n<:gender:1116708046853390397> Пол: {gender}")
    except FileNotFoundError:
        await ctx.send("Паспорт пользователя не найден!")
        
# ChatGPT с задаными правила
@bot.command(name='chat')
async def chat_command(ctx, *, query):
    # Показываем индикатор "Bot is typing"
    async with ctx.typing():
        # Интеграция с GPT-3.5 Turbo
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты полезный помощник."},
                {"role": "user", "content": query}
            ]
        )

        # Получаем ответ от GPT-3.5 Turbo
        response = completion.choices[0].message['content']

        # Отправляем ответ в чат Discord
        await ctx.send(response)

#Об боте
@bot.command()
async def about(ctx):
    msg = '''NobleEpuz - главный кодер бота
rinchik12 - помощник с командами
Askiphy - код системы почты

Благодарности:
ChatGPT - за помощь с кодом :3'''
    await ctx.send(msg)

#Википедия(папка wikipedia для файлов с инфой)
@bot.command()
async def wiki(ctx, filename):
    file_path = os.path.join(os.getcwd(), 'wikipedia', f'{filename}.txt')
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()

        await ctx.send(f'{content}')
    else:
        await ctx.send(f'Информация об {filename} не найдена.')

#Система почты
@bot.command(description="Отправить сообщение пользователю :D")
async def sendmsg(ctx, where: discord.Member, theme: str, *, msg: str):
    emb = discord.Embed(title=f"Новое сообщение от {ctx.author.display_name}", color=discord.Color.green())
    emb.add_field(name="Тема:", value=theme, inline=False)
    emb.add_field(name="Сообщение:", value=msg, inline=False)
    try:
        await where.send(embed=emb)
        await ctx.send(f"Сообщение отправлено пользователю {where.mention}!")
    except discord.Forbidden:
        await ctx.send(f"Невозможно отправить сообщение пользователю {where.mention}!")

#Очистка сообщений
@bot.command()
async def clear(ctx, amount: int = 5):
    channel = ctx.channel
    messages = []
    async for message in channel.history(limit=amount + 1):
        messages.append(message)
    await channel.delete_messages(messages)
            
bot.run('')
