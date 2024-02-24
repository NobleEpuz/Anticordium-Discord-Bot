import json
import os
import random
import time
import nextcord
import openai
import aiohttp
import io
import asyncio
import datetime
from nextcord import Embed, Interaction, SlashOption, ButtonStyle, SelectOption, ui
from nextcord.ext import commands
from nextcord.ui import View, Button

openai.api_key = ""
intents = nextcord.Intents.all()
intents.messages = True

bot = commands.Bot(command_prefix='an!', intents=intents)

@bot.event
async def on_ready():
    print("Бoт зaпycтилcя!")

# Создаем папку, если она не существует
if not os.path.exists("economy"):
    os.makedirs("economy")
    
if not os.path.exists("characters"):
    os.makedirs("characters")
    
if not os.path.exists("wikipedia"):
    os.makedirs("wikipedia")

def load_data(file_path):
    try:
        with open(file_path, "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    return data

def save_data(file_path, data):
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Структурируем команды по категориям
help_pages = {
    "Общие": {
        "/help": "Показать это сообщение со справкой",
        "/about": "Показывает список авторов бота",
        "/servers": "Список серверов Реленовы",
        "/sendmsg": "Позволяет отправить сообщение пользователю (by Askiphy)",
    },
    "ИИ": {
        "/draw": "Генерация картинок с помощи ИИ",
        "/ask": "Генерация текста с помощи ИИ",
        "/reset": "Сброс истории диалога у ИИ",
    },
    "Управление": {
        "/wiki": "Википедия по Реленове",
        "/clear": "Очистка сообщений",
        "/accept": "Принять персонажа в РП",
        "/characters": "Список персонажей РП",
        "/remove": "Удалить персонажа из списка РП"
    },
    "Экономика":{
        "/balance": "Посмотреть баланс",
        "/withdraw": "Взять деньги из банка",
        "/deposit": "Положить деньги в банк",
        "/inventory": "Открывать инвентарь",
        "/use": "Использовать предмет из инвентаря",
        "/pay": "Отправить деньги другому участнику",
        "/work": "Получить деньги",
        "/shop": "Открыть магазин",
        "/buy": "Приобрести предмет в магазине"
        }
}

# Класс кнопки для справки
class HelpButton(Button):
    def __init__(self, label):
        super().__init__(label=label, style=nextcord.ButtonStyle.grey)

    async def callback(self, interaction: nextcord.Interaction):
        page_contents = help_pages[self.label]
        embed = nextcord.Embed(title=f"Команды: {self.label}", color=0x00FF00)
        for name, description in page_contents.items():
            embed.add_field(name=name, value=description, inline=False)
        # Обновляем сообщение с новой страницей помощи
        await interaction.response.edit_message(embed=embed, view=self.view)

# Класс для помощи с навигацией
class HelpView(View):
    def __init__(self):
        super().__init__(timeout=180)  # Установите нужный timeout
        self.add_item(HelpButton("Общие"))
        self.add_item(HelpButton("ИИ"))
        self.add_item(HelpButton("Управление"))
        self.add_item(HelpButton("Экономика"))

@bot.slash_command(name="help", description="Показать справку по командам")
async def help_command(interaction: nextcord.Interaction):
    # Начальная страница справки
    start_category = "Общие"
    embed = nextcord.Embed(title=f"Команды: {start_category}", color=0x00FF00)
    for name, description in help_pages[start_category].items():
        embed.add_field(name=name, value=description, inline=False)
    view = HelpView()
    await interaction.response.send_message(embed=embed, view=view)

@bot.check
async def check_command(ctx):
    if isinstance(ctx.channel, nextcord.DMChannel):
        await ctx.send("Извините, я не могу выполнять команды в ЛС.\nВы можете зайти на сервер разработки LuniAssist: https://discord.gg/tVNY5xtcpv")
        return False
    return True

@bot.slash_command(name="draw", description="Генерирует изображение на основе указанного текста")
async def draw(ctx, prompt: str):
    try:
        await ctx.send('Идёт генерация изображения...')

        # Создайте изображение с помощью OpenAI API
        response = openai.Image.create(
            model="sdxl",
            prompt=prompt,
            n=1  # количество изображений
        )

        # Получите URL изображения
        image_url = response['data'][0]['url']

        # Скачайте изображение
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_content = await resp.read()

        # Отправьте изображение в канал
        await ctx.send(file=nextcord.File(io.BytesIO(image_content), 'image.png'))

    except Exception as e:
        await ctx.send(f'Произошла ошибка: {e}')

@bot.slash_command(name="wiki", description="Википедия по Реленове")
async def wiki_command(interaction: nextcord.Interaction, filename: str = "Список"):
    file_path = os.path.join(os.getcwd(), 'wikipedia', f'{filename}.txt')

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        if len(content) <= 6000:
            embed = nextcord.Embed(title=filename, description=content)
            await interaction.response.send_message(embed=embed)
        else:
            parts = [content[i:i + 6000] for i in range(0, len(content), 6000)]
            for i, part in enumerate(parts):
                embed = nextcord.Embed(title=f'{filename} (часть {i+1})', description=part)
                await interaction.followup.send(embed=embed)
    else:
        await interaction.response.send_message(f'Информация о {filename} не найдена.')

@bot.slash_command(description="Отправить сообщение пользователю :D")
async def sendmsg(interaction: Interaction, where: nextcord.Member, theme: str, msg: str):
    emb = nextcord.Embed(title=f"[Новое сообщение от {interaction.user}]", color=nextcord.Color.green())
    emb.add_field(name="Тема:", value=theme, inline=False)
    emb.add_field(name="Сообщение:", value=msg, inline=False)
    emb.add_field(name="И помните:", value="askiphy заботится о Вас!", inline=False)
    emb.set_footer(text="© Все права защищены. 2022 год", icon_url=client.user.avatar)
    try:
        await where.send(embed=emb)
    except:
        await interaction.response.send_message(f"Пользователю **{where}** невозможно отправить сообщение!")

@bot.slash_command(name="clear", description="Очистка сообщений")
async def clear_command(interaction: nextcord.Interaction, amount: int = 5):
    if interaction.user.guild_permissions.manage_messages:
        await interaction.channel.purge(limit=amount + 1)
        await interaction.response.send_message(f'{amount} сообщений удалено.')
    else:
        await interaction.response.send_message('У вас нет прав на удаление сообщений.')
        
conversations = {}
@bot.slash_command(name="ask", description="Задайте вопрос боту")
async def chat_command(interaction: nextcord.Interaction, prompt: str):
    user_id = str(interaction.user.id)

    # Показываем сообщение о том, что идет генерация текста
    await interaction.response.send_message("Идёт генерация текста...")

    # Добавляем запрос пользователя в историю беседы
    if user_id not in conversations:
        conversations[user_id] = [
            {"role": "system", "content": "Ты полезный помощник и ассистент по имени Луни. Ты идентифицируешь себя как девушку."},
            {"role": "user", "content": prompt}
        ]
    else:
        conversations[user_id].append({"role": "user", "content": prompt})

    # Взаимодействие с GPT (специфика взаимодействия может отличаться)
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversations[user_id]
    )

    response = completion.choices[0].message['content']

    # Очищаем ответ от возможных служебных сообщений
    response = response.strip()

    # Создаем Embed сообщение
    embed = nextcord.Embed(title="LuniGPT", description=response, color=nextcord.Color.green())

    # Обновляем исходное сообщение на Embed с сгенерированным текстом
    await interaction.edit_original_message(content=None, embed=embed)

    # Обновляем историю бесед с пользователем
    conversations[user_id].append({"role": "assistant", "content": response})
    
@bot.command(name='ask')
async def chat_command(ctx, *, query):
    user_id = str(ctx.author.id)
    
    # Check if conversation history exists
    if user_id not in conversations:
        conversations[user_id] = [
            {"role": "system", "content": "Ты полезный помощник и ассистент по имени Луни. Ты идентифицируешь себя как девушку."},
            {"role": "user", "content": query}
        ]
    else:
        conversations[user_id].append({"role": "user", "content": query})

    # "Bot is typing" indicator
    async with ctx.typing():
        # Interaction with GPT
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversations[user_id]
        )

        response = completion.choices[0].message['content']

        # Split the response if it's too long
        max_message_length = 4096
        if len(response) > max_message_length:
            parts = [response[i:i + max_message_length] for i in range(0, len(response), max_message_length)]
            for i, part in enumerate(parts):
                conversations[user_id].append({"role": "assistant", "content": part})
                # Create an Embed message with part number
                embed = nextcord.Embed(title=f"LuniGPT {i + 1}/{len(parts)}", description=part, color=nextcord.Color.green())
                # Send the Embed message to the Discord chat
                await ctx.send(embed=embed)
        else:
            conversations[user_id].append({"role": "assistant", "content": response})
            # Create an Embed message
            embed = nextcord.Embed(title="LuniGPT", description=response, color=nextcord.Color.green())
            # Send the Embed message to the Discord chat
            await ctx.send(embed=embed)

@bot.slash_command(name="reset", description="Сбросить историю беседы с ботом")
async def reset_command(interaction: nextcord.Interaction):
    user_id = str(interaction.user.id)
    if user_id in conversations:
        del conversations[user_id]
    await interaction.response.send_message("История беседы успешно сброшена!")
      
@bot.slash_command(name="accept", description="Принять персонажа в РП")
async def accept_command(interaction: nextcord.Interaction, character_name: str, member: nextcord.Member):
    # Check if the author of the interaction is an administrator
    if interaction.user.guild_permissions.administrator:
        characters_folder = 'characters'
        if not os.path.exists(characters_folder):
            os.mkdir(characters_folder)

        characters_file = f'{characters_folder}/characters.json'

        if os.path.exists(characters_file):
            with open(characters_file, 'r') as file:
                characters = json.load(file)
        else:
            characters = []

        character = {'name': character_name, 'user': member.id}
        characters.append(character)

        with open(characters_file, 'w') as file:
            json.dump(characters, file, indent=4)

        await interaction.response.send_message(f'Пepcoнaж {character_name} был принят и добавлен к {member.mention} в список!')
    else:
        await interaction.response.send_message('У вас нет прав на выполнение этой команды!')

@bot.slash_command(name="characters", description="Список персонажей РП")
async def characters_command(interaction: nextcord.Interaction, member: nextcord.Member = None):
    characters_file = 'characters/characters.json'

    if os.path.exists(characters_file):
        with open(characters_file, 'r') as file:
            characters = json.load(file)

        if member is None:
            member = interaction.user  # If no member is mentioned, show the characters of the user who invoked the command

        member_characters = [character['name'] for character in characters if character['user'] == member.id]

        if not member_characters:
            await interaction.response.send_message(f'{member.name} нет зарегистрированных персонажей.')
        else:
            character_list = '\n'.join(member_characters)
            await interaction.response.send_message(f'Персонажи {member.mention}:\n{character_list}')
    else:
        await interaction.response.send_message('Список персонажей пуст.')

@bot.slash_command(name="remove", description="Удалить персонажа из списка РП")
async def remove_command(interaction: nextcord.Interaction, character_name: str):
    characters_file = 'characters/characters.json'

    with open(characters_file, 'r') as file:
        characters = json.load(file)

    matching_characters = [character for character in characters if character['name'] == character_name]

    if len(matching_characters) == 0:
        await interaction.response.send_message(f'Персонаж {character_name} не найден.')
    elif len(matching_characters) > 1:
        await interaction.response.send_message('Найдено несколько персонажей с одинаковым именем. Укажите уникальное имя персонажа.')
    else:
        characters.remove(matching_characters[0])
        with open(characters_file, 'w') as file:
            json.dump(characters, file)
        await interaction.response.send_message(f'Персонаж {character_name} был удален из списка.')

@bot.slash_command(name="balance", description="Узнать баланс пользователя")
async def balance_command(interaction: nextcord.Interaction, member: nextcord.Member = None):
    user = member or interaction.user
    cash_data = load_data(f"economy/{user.id}_cash.json")
    bank_data = load_data(f"economy/{user.id}_bank.json")
    cash_balance = cash_data.get("balance", 0)
    bank_balance = bank_data.get("balance", 0)
    total_balance = cash_balance + bank_balance
    await interaction.response.send_message(f"Баланс {user.mention}: \nНаличные: {cash_balance} :gem:\nБанк: {bank_balance} :gem:\nВсего: {total_balance} :gem:")

@bot.slash_command(name="deposit", description="Положить деньги на счет")
async def deposit_command(interaction: nextcord.Interaction, amount: str):
    user = interaction.user
    cash_data = load_data(f"economy/{user.id}_cash.json")
    bank_data = load_data(f"economy/{user.id}_bank.json")
    cash_balance = cash_data.get("balance", 0)
    if amount.lower() in ["all", "все"]:
        amount_to_deposit = cash_balance
    else:
        amount_to_deposit = int(amount)

    if amount_to_deposit > 0:
        if cash_balance >= amount_to_deposit:
            cash_data["balance"] = cash_balance - amount_to_deposit
            bank_data["balance"] = bank_data.get("balance", 0) + amount_to_deposit
            save_data(f"economy/{user.id}_cash.json", cash_data)
            save_data(f"economy/{user.id}_bank.json", bank_data)
            await interaction.response.send_message(f"{user.mention}, вы успешно положили {amount_to_deposit} :gem: в банк")
        else:
            await interaction.response.send_message(f"{user.mention}, у вас недостаточно наличных средств для совершения депозита")
    else:
        await interaction.response.send_message(f"{user.mention}, пожалуйста, введите положительное количество :gem:")

@bot.slash_command(name="withdraw", description="Снять деньги со счета")
async def withdraw_command(interaction: nextcord.Interaction, amount: str):
    user = interaction.user
    cash_data = load_data(f"economy/{user.id}_cash.json")
    bank_data = load_data(f"economy/{user.id}_bank.json")
    cash_balance = cash_data.get("balance", 0)
    bank_balance = bank_data.get("balance", 0)
    if amount.lower() in ["all", "все"]:
        amount_to_withdraw = bank_balance
    else:
        amount_to_withdraw = int(amount)
        
    if amount_to_withdraw > 0:
        if bank_balance >= amount_to_withdraw:
            cash_data["balance"] = cash_balance + amount_to_withdraw
            bank_data["balance"] = bank_balance - amount_to_withdraw
            save_data(f"economy/{user.id}_cash.json", cash_data)
            save_data(f"economy/{user.id}_bank.json", bank_data)
            await interaction.response.send_message(f"{user.mention}, вы успешно сняли {amount_to_withdraw} :gem: со счета")
        else:
            await interaction.response.send_message(f"{user.mention}, у вас недостаточно средств на банковском счету для совершения снятия")
    else:
        await interaction.response.send_message(f"{user.mention}, пожалуйста, введите положительное количество :gem:")

@bot.slash_command(name="work", description="Получить валюту")
async def work_command(interaction: nextcord.Interaction):
    user = interaction.user
    cash_data = load_data(f"economy/{user.id}_cash.json")
    earnings = random.randint(40, 70)
    earnings_message = random.choice(earnings_messages).format(amount=earnings)
    cash_data["balance"] = cash_data.get("balance", 0) + earnings
    save_data(f"economy/{user.id}_cash.json", cash_data)
    await interaction.response.send_message(f"{user.mention}, {earnings_message}", ephemeral=True)

# Список возможных сообщений о заработке
earnings_messages = [
    "В своём почтовом ящике вы нашли {amount} :gem:.",
    "Какой-то добрый дядя дал вам в конверте {amount} :gem:. Помимо денег, в конверте лежал какой-то странный порошок. Вы его высыпали в мусорку, подумав, что это какой-то растёртый мел или мука.",
    "С неба на голову вам упали {amount} :gem:. Что это могло быть?.",
    "Вы приехали в отель «Виоленс» и заселились в номер. Когда вы зашли туда, вас обеспокоили странно приклеенные обои у телевизора. Вы немного их отодрали и заметили незапертый в стене сейф, где лежали {amount} :gem:.",
    "Вы устроились на работу чистильщиком водосточных труб Антомифа. Когда вы чистили одну из труб, вы нашли мертвого человека с кучей шприцов и чуть не наступили на них. Вам дали {amount} :gem: в качестве компенсации и наказали не разглашать информацию об этой ситуации.",
    "Вы начали несанкционированные раскопки в долине Каменного Сердца, нашли там большое месторождение золота. Но вы успели взять золота на сумму {amount} :gem: и скрыться, прежде чем сюда приехала полиция.",
    "Вы шли по переулкам города и увидели драку алкашей. Вы засняли это и выложили в интернет. Через пару часов вам кто-то прислал письмо с {amount} :gem: и с просьбой удалить это видео. Вы, конечно же, его удалили, потому что не хотите проблем с законом.",
    "Вы устроились работать в кофейню в качестве уборщика. Проработав там неделю, вы получили {amount} :gem:."
]

@bot.slash_command(name="pay", description="Перевести деньги другому пользователю")
async def pay_command(interaction: nextcord.Interaction, member: nextcord.Member, amount: int):
    user = interaction.user
    user_cash_data = load_data(f"economy/{user.id}_cash.json")
    recipient_cash_data = load_data(f"economy/{member.id}_cash.json")
    user_cash_balance = user_cash_data.get("balance", 0)
    if 0 < amount <= user_cash_balance:
        user_cash_data["balance"] = user_cash_balance - amount
        recipient_cash_data["balance"] = recipient_cash_data.get("balance", 0) + amount
        save_data(f"economy/{user.id}_cash.json", user_cash_data)
        save_data(f"economy/{member.id}_cash.json", recipient_cash_data)
        await interaction.response.send_message(f"{user.mention}, вы успешно отправили {amount} :gem: пользователю {member.mention}")
    else:
        await interaction.response.send_message(f"{user.mention}, у вас недостаточно наличных средств для совершения перевода")

@bot.slash_command(name="shop", description="Показывает предметы в магазине в виде эмбеда")
async def shop_command(interaction: nextcord.Interaction):
    with open('economy/shop.json', 'r', encoding='utf-8') as file:
        shop_items = json.load(file)
    
    embed = nextcord.Embed(title="Предметы в магазине", color=0x0000ff)
    
    for item_id, item in shop_items.items():
        name = item["name"]
        cost = item["cost"]
        description = item.get("description", "Описание отсутствует")
        embed.add_field(name=f"{name} (ID: {item_id})", value=f"Стоимость: {cost} :gem:\nОписание: {description}", inline=False)
    
    await interaction.response.send_message(embed=embed)
    
def load_shop_items():
    with open('economy/shop.json', 'r', encoding='utf-8') as file:
        return json.load(file)
    
@bot.slash_command(name="buy", description="Покупает предмет из магазина")
async def buy_command(
    interaction: nextcord.Interaction,
    item_id: int = SlashOption(
        name="item",
        description="Выберите предмет для покупки",
        required=True,
        # Данные о предметах будут загружены из shop.json для создания списка опций
        choices={item["name"]: item_id for item_id, item in load_shop_items().items()}
    )
):
    shop_items = load_shop_items()
    user = interaction.user
    cash_data = load_data(f"economy/{user.id}_cash.json")
    cash_balance = cash_data.get("balance", 0)

    if str(item_id) in shop_items:
        item = shop_items[str(item_id)]
        if cash_balance >= item["cost"]:
            cash_data["balance"] -= item["cost"]
            save_data(f"economy/{user.id}_cash.json", cash_data)
            
            inventory_data = load_data(f"economy/inventory/{user.id}_inventory.json")
            if str(item_id) in inventory_data:
                inventory_data[str(item_id)]["quantity"] += 1
            else:
                inventory_data[str(item_id)] = {
                    "name": item["name"],
                    "quantity": 1
                }
            save_data(f"economy/inventory/{user.id}_inventory.json", inventory_data)
            await interaction.response.send_message(f"{user.mention}, вы успешно купили {item['name']} за {item['cost']} :gem:")
        else:
            await interaction.response.send_message(f"{user.mention}, у вас недостаточно :gem: для покупки этого предмета")
    else:
        await interaction.response.send_message(f"{user.mention}, нет предмета с этим ID в магазине")

@bot.slash_command(name="inventory", description="Показывает инвентарь пользователя в виде эмбеда")
async def inventory_command(interaction: nextcord.Interaction):
    user = interaction.user
    inventory_data = load_data(f"economy/inventory/{user.id}_inventory.json")
    
    embed = nextcord.Embed(title="Инвентарь пользователя", color=0x00ff00)
    
    if inventory_data:
        for item_id, item in inventory_data.items():
            quantity = item['quantity']
            # Загрузим описание из файла магазина
            shop_items = load_shop_items()
            # Получим описание предмета, или текст, сообщающий об отсутствии описания
            description = shop_items.get(item_id, {}).get("description", "Описание отсутствует")
            embed.add_field(name=f"{item['name']} (ID: {item_id})", value=f"Количество: {quantity}\nОписание: {description}", inline=False)
    else:
        embed.description = "Инвентарь пуст"
    
    await interaction.response.send_message(embed=embed)
    
@bot.slash_command(name="use", description="Использование предмета из инвентаря")
async def use_command(interaction: nextcord.Interaction, item_id: int):
    user = interaction.user
    inventory_data = load_data(f"economy/inventory/{user.id}_inventory.json")
    shop_items = load_shop_items()  # Загружаем данные из shop.json
    if str(item_id) in inventory_data:
        item = inventory_data[str(item_id)]
        if item["quantity"] > 0:
            # Уменьшение количества предмета на 1
            item["quantity"] -= 1
            # Удаление предмета из инвентаря, если его количество равно нулю
            if item["quantity"] == 0:
                del inventory_data[str(item_id)]
            
            # Получение информации о предмете из магазина
            shop_item = shop_items.get(str(item_id), {})
            # Проверяем, есть ли атрибут awarded_role_id у предмета
            awarded_role_id = shop_item.get("awarded_role_id")
            if awarded_role_id:
                # Выдача роли пользователю
                role = interaction.guild.get_role(awarded_role_id)
                if role:
                    await user.add_roles(role)
            
            # Сохранение измененного инвентаря
            save_data(f"economy/inventory/{user.id}_inventory.json", inventory_data)
            
            # Отправка пользователю сообщения об использовании предмета
            if shop_item.get("use_message"):
                await interaction.response.send_message(shop_item["use_message"])
            else:
                await interaction.response.send_message(f"{user.mention}, предмет {shop_item['name']} успешно использован")
        else:
            await interaction.response.send_message(f"{user.mention}, у вас нет этого предмета в инвентаре")
    else:
        await interaction.response.send_message(f"{user.mention}, предмет с ID {item_id} отсутствует в вашем инвентаре")

bot.run("")
