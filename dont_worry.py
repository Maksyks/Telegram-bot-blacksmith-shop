import telebot
from telebot import types
import random
import json
import re

TOKEN = "8145099453:AAF8si672FAE2SB5TN-mQOgm4GKi6jj0M20"

bot = telebot.TeleBot(TOKEN)

def load_profiles(filename="profiles.json"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # Если файла нет, возвращаем пустой словарь
      
def save_profiles(profile, filename="profiles.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(profile, file, ensure_ascii=False, indent=4)
    
def create_profiles(user_id, name, profile):
    if str(user_id) not in profile:
        profile[str(user_id)] = {
            "name": name,
            "level": 1,
            "iron": 9,
            "copper": 5,
            "gold": 30,
            "energy": 50,
            "xp": 0
        }
        save_profiles(profile)  # Сохраняем обновленные данные

def get_profiles(user_id, profile):
    return profile.get(str(user_id))
    

def update_profiles(user_id, key, value, profile):
    if str(user_id) in profile:
        profile[str(user_id)][key] = value
        save_profiles(profile)  # Сохраняем обновленные данные

def start_keyboard():
    keyboard= types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons =[
        types.KeyboardButton("👤 Профиль"),
        types.KeyboardButton("⚙️ Кузница"),
        types.KeyboardButton("⛏️ Шахта"),
        types.KeyboardButton("🛒 Магазин")]
    for button in buttons:
        keyboard.add(button) #добавляем кнопки
    return keyboard  

def calculate_level(xp):
    level = 1
    xp_required = 20 

    while xp >= xp_required:
        level += 1
        xp_required += xp_required * 1.5  # Увеличиваем порог на 50% каждый раз

    return level

def update_level(user_id, xp_earned, profiles):
    profile = profiles.get(str(user_id))
    profile["xp"] += xp_earned
    new_level = calculate_level(profile["xp"])

    if new_level > profile["level"]:
        profile["level"] = new_level
        bot.send_message(user_id, f"🎉 Поздравляем! Вы достигли уровня {new_level}!")

    update_profiles(user_id, "xp", profile["xp"], profiles)

profiles = load_profiles()  
user_last_keyboards = {}

@bot.message_handler(commands=['start'])
def welcome(message):
    keyboard= start_keyboard()
        
    profile = get_profiles(message.from_user.id, profiles)

    if profile == None:
        create_profiles(message.from_user.id, message.from_user.first_name, profiles)

    text = ("Добро пожаловать в кузницу, выбери, чем займемся\n"
            "1. Профиль покажет твои ресурсы\n"
            "2. В кузнице ты создашь оружие на продажу\n"
            "3. В шахте можно добывать железо и медь\n"
            "4. В магазине можно купить энергию, железо или медь")
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    profile = get_profiles(message.from_user.id, profiles)
    text = (
        f"👤 Имя: {profile['name']}\n"
        f"⚙️ Уровень: {profile['level']}\n"
        f"🔩 Железо: {profile['iron']}\n"
        f"🟠 Медь: {profile['copper']}\n"
        f"💰 Золото: {profile['gold']}\n"
        f"⚡ Энергия: {profile['energy']}\n"
        f"📈 Опыт: {profile['xp']}"
    )
    bot.send_message(message.chat.id, text)


weapons = [
    {"name": "Меч", "iron": 3, "gold": 15},
    {"name": "Молот", "iron": 4, "gold": 25},
    {"name": "Щит", "iron": 6, "copper": 2, "gold": 30},
    {"name": "Кинжал", "iron": 1, "copper": 1, "gold": 10},
    {"name": "Топор", "iron": 3, "copper": 2, "gold": 25}
]
   
@bot.message_handler(func=lambda m: m.text == "⚙️ Кузница")#выбор оружия для крафта
def blacksmithing(message):
    profile = get_profiles(message.from_user.id, profiles)

    # Генерация трех случайных уникальных чисел 
    random_numbers = random.sample(range(len(weapons)), 3)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)

    for i in random_numbers:
        weapon = weapons[i]

        resources_text = "Железо"
        if 'copper' in weapon:
            resources_text += ", Медь"
        
        button_text = f"{weapon['name']}: требуются {resources_text}"
        keyboard.add(types.KeyboardButton(button_text))
    
    keyboard.add(types.KeyboardButton("Выйти в меню"))
    user_last_keyboards[message.from_user.id] = keyboard #сохраняем клаву, чтобы вернуться
    text = ("Твои ресурсы:\n"
        f"⚙️ Уровень: {profile['level']}\n"
        f"🔩 Железо: {profile['iron']}\n"
        f"🟠 Медь: {profile['copper']}\n"
        f"💰 Золото: {profile['gold']}\n"
        "Что создаем?\n"
    )
    bot.send_message(message.chat.id, text, reply_markup=keyboard)
    


@bot.message_handler(func=lambda m: any(weapon["name"] in m.text for weapon in weapons))#выбор уровня оружия
def select_weapon_level(message):
    profile = get_profiles(message.from_user.id, profiles)
    user_level = profile['level']

    for weapon in weapons: #какое оружие выбрано
        if weapon["name"] in message.text:
            selected_weapon = weapon
            break

    if selected_weapon:
        # Проверяем, хватает ли ресурсов
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        weapon_levels = [
            user_level - 1 if user_level > 1 else 0,
            user_level,
            user_level + 1]

        #бонусы за уровень игрока
        required_iron = int(selected_weapon.get("iron", 0) - user_level*4/3)
        if 'copper' in selected_weapon:
            required_copper = int(selected_weapon.get("copper", 0) - user_level*4/3)
        earned_gold = int(selected_weapon.get("gold", 0) - user_level*4/3) 

        #выбор ресурсов и золота в зависимости от уровня
        increment_resource = 0
        increment_gold = 0
        for lvl in weapon_levels:
            if lvl !=0 :#обработка нулевого уровня оружия
                required_iron = selected_weapon["iron"] + (lvl * 3) + increment_resource
                if 'copper' in selected_weapon:
                    required_copper = int(selected_weapon["copper"] + ((lvl * 3)/2)) + increment_resource
                earned_gold = selected_weapon["gold"] + (lvl * 3) + 12 + increment_gold

                button_text = f"Ур. {lvl} Золото: {earned_gold}, Железо: {required_iron}"
                if 'copper' in selected_weapon:
                    button_text += f", Медь: {required_copper}"
                keyboard.add(types.KeyboardButton(button_text))
                increment_gold += 13
                increment_resource +=4


        keyboard.add(types.KeyboardButton("Назад"))
        keyboard.add(types.KeyboardButton("Выйти в меню"))
        bot.send_message(message.chat.id, "Выбери уровень", reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, "Оружие не найдено.")


@bot.message_handler(func=lambda m: "Ур." in m.text)  # Крафт (выбрали уровень оружия)
def craft_weapon(message):
    profile = get_profiles(message.from_user.id, profiles)
    button_text = message.text
    user_level = profile['level']
    # Регулярное выражение для извлечения данных
    match = re.match(r"Ур\. (\d+) Золото: (\d+), Железо: (\d+)(?:, Медь: (\d+))?", button_text)
    if not match:
        bot.send_message(message.chat.id, "Ошибка: неверный формат кнопки.")
        return

    weapon_level = int(match.group(1))
    earned_gold = int(match.group(2)) 
    required_iron = int(match.group(3)) 
    required_copper = int(match.group(4)) if match.group(4) else 0  # Требуемая медь (если есть)

    # Проверяем, хватает ли ресурсов
    if (profile["iron"] >= required_iron and
        (required_copper == 0 or profile["copper"] >= required_copper)):

        # Предлагаем игроку выбрать число от 1 до 18
        bot.send_message(message.chat.id, "Выбери число от 1 до 18:")

        # Сохраняем данные для следующего шага
        bot.register_next_step_handler(message, lambda m: check_number(m, weapon_level, user_level, earned_gold, required_iron, required_copper))
    else:
        # Если ресурсов не хватает
        bot.send_message(message.chat.id, 
                         f"❌ Недостаточно ресурсов!\n"
                         f"🔩 Нужно: Железо {required_iron}, Медь {required_copper}\n"
                         f"📦 У вас: Железо {profile['iron']}, Медь {profile['copper']}")

def check_number(message, weapon_level, user_level, earned_gold, required_iron, required_copper):
    try:
        player_number = int(message.text)
        if player_number < 1 or player_number > 18:
            bot.send_message(message.chat.id, "Число должно быть от 1 до 18. Попробуй еще раз.")
            return
    except ValueError:
        bot.send_message(message.chat.id, "Это не число. Попробуй еще раз.")
        return

    # Генерация случайного числа ботом
    bot_number = random.randint(1, 18)

    # Определяем порог для успеха в зависимости от уровня оружия
    if weapon_level == user_level - 1 if user_level > 1 else 0:
        threshold = 7  # Шанс успеха ~77%
    elif weapon_level == user_level:
        threshold = 5  # Шанс успеха ~55%
    elif weapon_level == user_level + 1:
        threshold = 3  # Шанс успеха ~33%
    else:
        threshold = 5  # Значение по умолчанию 

    # Проверяем, насколько близко число игрока к числу бота
    difference = abs(player_number - bot_number)
    if difference <= threshold:
        complete_craft(message, weapon_level, earned_gold, required_iron, required_copper, success = True)
    else:
        complete_craft(message, weapon_level, earned_gold, required_iron, required_copper, success = False)

def complete_craft(message, weapon_level, earned_gold, required_iron, required_copper, success=True):
    profile = get_profiles(message.from_user.id, profiles)

    if success:
        profile["iron"] -= required_iron
        if required_copper > 0:  # Если медь требуется
            profile["copper"] -= required_copper
        profile["gold"] += earned_gold

        xp_reward = 10 + (weapon_level * profile['level'])
        update_level(message.from_user.id, xp_reward, profiles)

        # Сохраняем обновленный профиль
        update_profiles(message.from_user.id, "iron", profile["iron"], profiles)
        if required_copper > 0:  # Если медь была использована
            update_profiles(message.from_user.id, "copper", profile["copper"], profiles)
        update_profiles(message.from_user.id, "gold", profile["gold"], profiles)
        update_profiles(message.from_user.id, "xp", profile["xp"], profiles)

        # Отправляем сообщение об успехе
        bot.send_message(message.chat.id, 
                         f"✅ Успех!\n"
                         f"⚡ Затрачено: 🔩 Железо {required_iron}, 🟠 Медь {required_copper}\n"
                         f"🎁 Получено: 💰 {earned_gold} золота и 📈 {xp_reward} опыта")
    else:
        # В случае неудачи забираем 3/5 ресурсов
        lost_iron = int(required_iron * 3 / 5)
        lost_copper = int(required_copper * 3 / 5) if required_copper > 0 else 0

        profile["iron"] -= lost_iron
        if required_copper > 0:  # Если медь требуется
            profile["copper"] -= lost_copper

        # Сохраняем обновленный профиль
        update_profiles(message.from_user.id, "iron", profile["iron"], profiles)
        if required_copper > 0:  # Если медь была использована
            update_profiles(message.from_user.id, "copper", profile["copper"], profiles)

        # Отправляем сообщение о неудаче
        bot.send_message(message.chat.id, 
                         f"❌ Неудача!\n"
                         f"⚡ Потеряно: 🔩 Железо {lost_iron}, 🟠 Медь {lost_copper}\n"
                         f"💰 Золото не начислено.")

@bot.message_handler(func=lambda m: m.text == "Выйти в меню")
def exit_back(message):
    keyboard = start_keyboard() 
    text = ("Выбери, чем займемся\n"
        "1. Профиль покажет твои ресурсы\n"
        "2. В кузнице ты создашь оружие на продажу\n"
        "3. В шахте можно добывать железо и медь\n"
        "4. В магазине можно купить энергию, железо или медь")

    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "Назад")
def back(message):
    last_keyboard = user_last_keyboards.get(message.from_user.id)

    if last_keyboard:
        bot.send_message(message.chat.id, "Возвращаемся назад:", reply_markup=last_keyboard)
    else:
        bot.send_message(message.chat.id, "Нет предыдущей клавиатуры.", reply_markup=start_keyboard())

@bot.message_handler(func=lambda m: m.text == "⛏️ Шахта")
def mine(message):
    profile = get_profiles(message.from_user.id, profiles)
    
    if profile['energy'] < 4:
        bot.send_message(message.chat.id, "⚡ Ты слишком устал!")
        return
    
    profile['energy'] -= 4
    update_profiles(message.from_user.id, "energy", profile['energy'], profiles)
    
    # Определяем успешность добычи
    success = random.choice([True, True, False])
    user_level = profile['level']
    if success: #добыча
        iron_gained = random.randint(2 + user_level, 9 + user_level)
        copper_gained = random.randint(1 + user_level, 5 + user_level)  
        profile['iron'] += iron_gained
        profile['copper'] += copper_gained
        update_profiles(message.from_user.id, "iron", profile['iron'], profiles)
        update_profiles(message.from_user.id, "copper", profile['copper'], profiles)
        
        resulttext = f"⛏️ Ты добыл 🔩 железа: {iron_gained} и 🟠 меди: {copper_gained}"
    else:
        failure_messages = [
            "⛏️ В шахте обвал! Ничего не найдено.",
            "⛏️ Сегодня не твой день. Руды совсем не нашлось.",
            "⛏️ Все твои ресурсы украли шахтеры-разбойники."
        ]
        resulttext = random.choice(failure_messages)
    
    # Отправляем результат
    bot.send_message(message.chat.id, resulttext)

@bot.message_handler(func=lambda m: m.text == "🛒 Магазин")
def shop(message):
    profile = get_profiles(message.from_user.id, profiles)
    
    # Товары в магазине
    shop_items = [
        {"name": "⚡ Энергия", "price": 10, "key": "energy", "amount": 5},
        {"name": "🔩 Железо", "price": 15, "key": "iron", "amount": 3},
        {"name": "🟠 Медь", "price": 20, "key": "copper", "amount": 2}
    ]
    
    # Создаем клавиатуру для магазина
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in shop_items:
        button_text = f"{item['name']} {item['amount']} - цена {item['price']}"
        keyboard.add(types.KeyboardButton(button_text))
    keyboard.add(types.KeyboardButton("Выйти в меню"))
    
    # Отправляем сообщение с товарами
    text = (
        "🛒 Добро пожаловать в магазин!\n"
        f"💰 Ваш баланс: {profile['gold']} золота\n"
        "Выбери товар для покупки:"
    )
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(func=lambda m: any(item["name"] in m.text for item in [
    {"name": "⚡ Энергия"}, {"name": "🔩 Железо"}, {"name": "🟠 Медь"}]))
def buy_item(message):
    profile = get_profiles(message.from_user.id, profiles)
    
    # Определяем, какой товар выбран
    if "⚡ Энергия" in message.text:
        item = {"name": "⚡ Энергия", "price": 10, "resource": "energy", "amount": 5}
    elif "🔩 Железо" in message.text:
        item = {"name": "🔩 Железо", "price": 15, "resource": "iron", "amount": 3}
    elif "🟠 Медь" in message.text:
        item = {"name": "🟠 Медь", "price": 20, "resource": "copper", "amount": 2}
    else:
        bot.send_message(message.chat.id, "Ошибка: товар не найден.")
        return
    
    # Проверяем, можно ли купить товар
    if profile["gold"] < item["price"]:
        bot.send_message(
            message.chat.id,
            f"❌ Недостаточно золота!\n"
            f"💰 Нужно: {item['price']} золота\n"
            f"💰 У тебя: {profile['gold']} золота"
        )
        return
    
    # Проверяем ограничение на энергию (не более 50)
    if item["resource"] == "energy" and (profile["energy"] + item["amount"]) > 50:
        bot.send_message(
            message.chat.id,
            f"❌ Нельзя купить больше 50 энергии!\n"
            f"⚡ У тебя уже: {profile['energy']} энергии\n"
        )
        return
    
    # Покупка товара
    profile["gold"] -= item["price"]
    profile[item["resource"]] += item["amount"]
    update_profiles(message.from_user.id, "gold", profile["gold"], profiles)
    update_profiles(message.from_user.id, item["resource"], profile[item["resource"]], profiles)
    
    bot.send_message(
        message.chat.id,
        f"📦 Получено: {item['amount']} {item['name']}\n"
        f"💰 Остаток золота: {profile['gold']}"
    )
    
if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)