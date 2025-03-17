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
            "iron": 4,
            "copper": 2,
            "gold": 15,
            "energy": 30,
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
        types.KeyboardButton("Профиль"),
        types.KeyboardButton("Кузница"),
        types.KeyboardButton("Шахта"),
        types.KeyboardButton("Магазин")]
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

@bot.message_handler(func=lambda m: m.text == "Профиль")
def profile(message):
    profile = get_profiles(message.from_user.id, profiles)
    text = (
        f"👤 Имя: {profile['name']}\n"
        f"⚙️ Уровень: {profile['level']}\n"
        f"🔩 Железо: {profile['iron']}\n"
        f"🔩 Медь: {profile['copper']}\n"
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
   
@bot.message_handler(func=lambda m: m.text == "Кузница")#выбор оружия для крафта
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
        f"🔩 Медь: {profile['copper']}\n"
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


@bot.message_handler(func=lambda m: "Ур." in m.text)  # Крафт
def craft_weapon(message):
    profile = get_profiles(message.from_user.id, profiles)
    button_text = message.text

    # Регулярное выражение с опциональной медью
    match = re.match(r"Ур\. (\d+) Золото: (\d+), Железо: (\d+)(?:, Медь: (\d+))?", button_text)
    
    weapon_level = int(match.group(1))
    earned_gold = int(match.group(2)) 
    required_iron = int(match.group(3)) 
    required_copper = int(match.group(4)) if match.group(4) else 0  # Требуемая медь (если есть)

    if (profile["iron"] >= required_iron and
        (required_copper == 0 or profile["copper"] >= required_copper)):

        # Уменьшаем ресурсы
        profile["iron"] -= required_iron
        if required_copper > 0:  # Если медь требуется
            profile["copper"] -= required_copper
        profile["gold"] += earned_gold

        xp_reward = 10 + (weapon_level * 2)
        profile["xp"] += xp_reward
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
                         f"⚡ Затрачено: Железо {required_iron}, Медь {required_copper}\n"
                         f"🎁 Получено: {earned_gold} золота и {xp_reward} опыта")
    else:
        # Если ресурсов не хватает
        bot.send_message(message.chat.id, 
                         f"❌ Недостаточно ресурсов!\n"
                         f"🔩 Нужно: Железо {required_iron}, Медь {required_copper}\n"
                         f"📦 У вас: Железо {profile['iron']}, Медь {profile['copper']}")

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

# @bot.message_handler(func=lambda m: m.text=="Шахта" )

# @bot.message_handler(func=lambda m: m.text=="Магазин" )
    
if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)