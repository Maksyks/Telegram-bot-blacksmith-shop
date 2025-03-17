import telebot
from telebot import types
import random
import json

TOKEN = "8145099453:AAF8si672FAE2SB5TN-mQOgm4GKi6jj0M20"

bot = telebot.TeleBot(TOKEN)

def load_profiles(filename="profiles.json"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}  # Если файла нет, возвращаем пустой словарь
    
profiles = load_profiles()    

def save_profiles(profile, filename="profiles.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(profile, file, ensure_ascii=False, indent=4)
    
def create_profiles(user_id, name, profile):
    if str(user_id) not in profile:
        profile[str(user_id)] = {
            "name": name,
            "level": 1,
            "iron": 4,
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

@bot.message_handler(commands=['start'])
def welcome(message):
    keyboard= start_keyboard()
        
    profile = get_profiles(message.from_user.id, profiles)

    if profile == None:
        create_profiles(message.from_user.id, message.from_user.first_name, profiles)

    text = ("Добро пожаловать в кузницу, выбери, чем займемся\n"
            "Профиль покажет твои ресурсы\n"
            "В кузнице ты создашь оружие на продажу\n"
            "В шахте можно добывать железо\n"
            "В магазине можно купить энергию и железо")
    
    bot.send_message(message.chat.id, text, reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "Профиль")
def profile(message):
    profile = get_profiles(message.from_user.id, profiles)
    text = (
        f"👤 Имя: {profile['name']}\n"
        f"⚙️ Уровень: {profile['level']}\n"
        f"🔩 Железо: {profile['iron']}\n"
        f"💰 Золото: {profile['gold']}\n"
        f"⚡ Энергия: {profile['energy']}\n"
        f"📈 Опыт: {profile['xp']}"
    )
    bot.send_message(message.chat.id, text)

    
@bot.message_handler(func=lambda m: m.text == "Кузница")
def blacksmithing(message):
    profile = get_profiles(message.from_user.id, profiles)
    user_level = profile['level']

    weapons = [
        {"name": "Меч", "iron": 3, "gold": 15},
        {"name": "Молот", "iron": 4, "gold": 25},
        {"name": "Щит", "iron": 6, "copper": 2, "gold": 30},
        {"name": "Кинжал", "iron": 1, "copper": 1, "gold": 10},
        {"name": "Топор", "iron": 3, "copper": 2, "gold": 25}
    ]

    # Генерация трех случайных уникальных чисел 
    random_numbers = random.sample(range(len(weapons)), 3)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bonus_gold = (user_level - 1 ) * 10

    for i in random_numbers:
        weapon = weapons[i]

        button_text = (f"{weapon['name']} (Железо: {weapon.get('iron', 0) + user_level - 1}," 
        f"Медь: {weapon.get('copper', 0) + user_level - 1}," 
        f"Золото: {weapon.get('gold', 0) + bonus_gold})")

        keyboard.add(types.KeyboardButton(button_text))
    
    keyboard.add(types.KeyboardButton("Выйти"))
    bot.send_message(message.chat.id, "Выберите оружие:", reply_markup=keyboard)
    
@bot.message_handler(func=lambda m: m.text == "Выйти")
def exit_back(message):
    keyboard = start_keyboard() 
    text = ("Добро пожаловать в кузницу, выбери, чем займемся\n"
        "Профиль покажет твои ресурсы\n"
        "В кузнице ты создашь оружие на продажу\n"
        "В шахте можно добывать железо\n"
        "В магазине можно купить энергию и железо")

    bot.send_message(message.chat.id, text, reply_markup=keyboard)

# @bot.message_handler(func=lambda m: m.text=="Шахта" )

# @bot.message_handler(func=lambda m: m.text=="Магазин" )
    
if __name__ == "__main__":
    print("Бот запущен!")
    bot.polling(none_stop=True)