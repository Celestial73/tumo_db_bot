import telebot
import time
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3

API_KEY = '2035136795:AAEmsoaL6MTUnQha1lb8L0aJ3fj0kx_-3GM'
bot = telebot.TeleBot(API_KEY)

current_id = 0
current_activity_id = 0
default_coins = 800
names_to_descs ={}
admin_ids = []
admin1 =994625451
admin2 =2
admin3 =3

@bot.message_handler(commands=["start", "help"])
def start_mes(message):
    bot.reply_to(message, "Привет! \nВот список команд:"
                          "\n"
                          "\n/new_account - создать новый аккаунт"
                          "\n/coins - узнать количество монет"
                          "\n"
                          "\n/event_list - узнать, какие сейчас существуют события"
                          "\n/buy_a_ticket - купить билет на событие"
                          "\n/my_events - список купленных билетов")

@bot.message_handler(commands=["admin_help"])
def show_admin_commands(message):
    bot.reply_to(message, "Привет! Вот список админских команд: "
                          "\n\n/add_new_admin - добавить нового админа"
                          "\n/show_all_users - показать все аккаунты"
                          "\n/add_money - добавить (убавить) пользователю монет"
                          "\n/new_event - создать новое событие"
                          "\n/show_event_participants - показать всех участников события"
                          "\n/delete_event - удалить событие")

@bot.message_handler(commands=["learn_chat_id"])
def learn_chat_id(message):
    bot.reply_to(message, message.chat.id)

@bot.message_handler(commands=["learn_id"])
def learn_id(message):
    bot.reply_to(message, str(message.from_user.id))


def onRestart_update_data():
    try:
        global admin_ids
        global current_id
        global  current_activity_id

        with open('admins.txt') as f:
            lines = f.readlines()
            admin_ids = lines[0].split()
            print(admin_ids)
        c = sqlite3.connect("TUMO_MAIN_DB.db", isolation_level=None)
        cursor = c.cursor()
        create_table_coins = """CREATE TABLE IF NOT EXISTS tumo_coins_main_table(
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            coins INTEGER NOT NULL,
                            tg_id TEXT NOT NULL UNIQUE,
                            activities TEXT);"""
        create_table_activities = """CREATE TABLE IF NOT EXISTS tumo_activities_main_table(
                                    id INTEGER PRIMARY KEY,
                                    name TEXT NOT NULL UNIQUE,
                                    price TEXT NOT NULL,
                                    descript TEXT NOT NULL,
                                    participants TEXT);"""
        c.execute(create_table_coins)
        c.execute(create_table_activities)
        c.execute('pragma journal_mode=wal')
        sql_select_query = """select id from tumo_coins_main_table"""
        cursor.execute(sql_select_query)
        id_data = cursor.fetchall()
        for row in id_data:
            if max(row) > current_id:
                current_id= max(row)
        current_id+= 1
        activity_select_query = """select id from tumo_activities_main_table"""
        cursor.execute(activity_select_query)
        act_id_data = cursor.fetchall()
        for row1 in act_id_data:
            if max(row1) > current_activity_id:
                current_activity_id = max(row1)
        current_activity_id += 1
        c.close()
    except sqlite3.Error as e:
        print(e)
        pass
onRestart_update_data()

@bot.message_handler(commands=["show_event_participants"])
def show_event_participants(message):
    if str(message.from_user.id) not in admin_ids:
        bot.reply_to(message, "Вы не администратор.")
        return
    nameMsg = bot.send_message(message.from_user.id, "Введите название события: ")
    bot.register_next_step_handler(nameMsg, show_participants)

@bot.message_handler(commands=["delete_event"])
def delete_event_message(message):
    if str(message.from_user.id) not in admin_ids:
        bot.reply_to(message, "Вы не администратор.")
        return
    nameMsg = bot.send_message(message.from_user.id, "Введите название события: ")
    bot.register_next_step_handler(nameMsg, confirm_deleting_an_event)

def confirm_deleting_an_event (message):
    try:
        event_name = message.text
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        get_names_and_ids = """SELECT name from tumo_activities_main_table"""
        c.execute(get_names_and_ids)
        events = c.fetchall()
        con.close()
        exists = False
        for e in events:
            if str(e[0]) == str(event_name):
                exists = True
                break
        if not exists:
            bot.send_message(message.chat.id, "Такого события не существует.")
            return
        markup_inline = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text="Да", callback_data= "Event_name###$$$%%%^^^" + event_name)
        item_no = types.InlineKeyboardButton(text="Нет", callback_data="activity_delete_denied")
        markup_inline.add(item_yes, item_no)
        bot.send_message(message.chat.id, f"Вы уверены, что хотите удалить событие {event_name}?",  reply_markup=markup_inline)
    except Exception as e:
        print(e)
        pass

@bot.callback_query_handler(func = lambda call: True)
def activity_get_ans(call):
    try:
        if call.data == "activity_denied":
            bot.send_message(call.message.chat.id, "Событие не добавлено.")
        elif call.data == "activity_delete_denied":
            bot.send_message(call.message.chat.id, "Событие не удалено.")
        elif call.data.split("###$$$%%%^^^")[0] == "Event_name":
            ans = call.data.split("###$$$%%%^^^")
            con = sqlite3.connect("TUMO_MAIN_DB.db")
            c = con.cursor()
            get_names_and_ids = """DELETE from tumo_activities_main_table where name = ?"""
            c.execute(get_names_and_ids, (ans[1], ) )
            con.commit()
            con.close()
            bot.send_message(call.message.chat.id, "Событие удалено.")
        elif call.data == "ticket_purchase_aborted":
            bot.send_message(call.message.chat.id, "Покупка отменена.")
        elif len(call.data.split("~~~")) == 2:
                global names_to_descs
                global current_activity_id
                ans = call.data.split("~~~")
                print(names_to_descs)
                create_new_activity(current_activity_id, ans[1], ans[0], names_to_descs[ans[1]])
                bot.send_message(call.message.chat.id, f'Событие "{ans[1]}" добавлено.')
                names_to_descs.pop(ans[1], None)


        elif len(call.data.split("~~~")) == 4:
            ans = call.data.split("~~~")
            con = sqlite3.connect("TUMO_MAIN_DB.db")
            cursor = con.cursor()
            get_user_name_and_activities = """SELECT name,activities from tumo_coins_main_table where tg_id =?"""
            get_event_participants = """SELECT participants from tumo_activities_main_table where name = ?"""
            cursor.execute(get_user_name_and_activities, (call.message.chat.id, ))
            results_name_and_act = cursor.fetchall()
            name = results_name_and_act[0][0]
            user_init_activities = str(results_name_and_act[0][1])
            cursor.execute(get_event_participants, (ans[0], ))
            participants = str(cursor.fetchall()[0][0])
            update_participants = """UPDATE tumo_activities_main_table SET participants = ? where name = ?"""
            if participants == None:
                cursor.execute(update_participants, (f"{name} ({call.message.chat.id})", ans[0]))
                con.commit()
            else:
                cursor.execute(update_participants, (participants + f"\n{name} ({call.message.chat.id})", ans[0]))
                con.commit()
            con.commit()
            update_user_coins_and_activities = """UPDATE tumo_coins_main_table SET coins = ?, activities = ? where tg_id = ?"""
            if user_init_activities == None:
                cursor.execute(update_user_coins_and_activities,
                               (str(int(ans[2]) - int(ans[1])), ans[0] , call.message.chat.id))
                con.commit()
            else:
                cursor.execute(update_user_coins_and_activities,
                               (str(int(ans[2]) - int(ans[1])),  user_init_activities +"\n"+ ans[0], call.message.chat.id))
                con.commit()
            con.commit()
            con.close
            bot.send_message(call.message.chat.id, f'Вы приобрели билет на событие "{ans[0]}".')
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=call.message.text, reply_markup= None)
        bot.answer_callback_query(callback_query_id=call.id)
    except sqlite3.Error or Exception as e:
        print(e)
        pass

def show_participants(message):
    try:
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        get_names_and_ids = """SELECT participants from tumo_activities_main_table where name = ?"""
        c.execute(get_names_and_ids, (message.text,))
        res = c.fetchall()
        if res == []:
            bot.send_message(message.chat.id, "Такого события не существует.")
            return
        results = res[0][0]
        if results == None:
            bot.send_message(message.chat.id, "На событие пока никто не записался.")
        else:
            bot.send_message(message.chat.id, "Вот список участвующих: \n" + results)
            return
    except sqlite3.Error or Exception as e:
        print(e)
        pass

@bot.message_handler(commands=["add_new_admin"])
def add_new_admin(message):
    if str(message.from_user.id) not in admin_ids:
        bot.reply_to(message, "Вы не администратор.")
        return
    idMsg = bot.send_message(message.chat.id, "Введите телеграм - id нового администратора. Свой id можно узнать, используя команду /learn_id")
    def new_admin(message):
        with open('admins.txt', 'a') as f:
            f.write(' ' + message.text)
        bot.send_message(message.chat.id, "Новый администратор добавлен.")
    bot.register_next_step_handler(idMsg, new_admin)

@bot.message_handler(commands=["show_all_users"])
def show_all_users(message):
    try:
        if str(message.from_user.id) not in admin_ids:
            bot.reply_to(message, "Вы не администратор.")
            return
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c= con.cursor()

        get_names_and_ids = """SELECT name,tg_id,coins from tumo_coins_main_table"""
        c.execute(get_names_and_ids)
        results = c.fetchall()
        n=0
        contin = True
        while contin:
            fin_text = ""
            for i in range(len(results)):
                if n == len(results):
                    break
                t = results[n]
                fin_text = fin_text + f"\n{n+1})    Имя:    {t[0]};    Telegram_id: {t[1]};    Монеты: {t[2]}"
                n+=1
                if n>=25 and n%25 ==0:
                    break
                if str(t[1]) == str(results[-1][1]):
                    contin = False
            bot.send_message(message.chat.id, fin_text)
        con.close()
    except Exception as e:
        print(e)
        pass
@bot.message_handler(commands = ["add_money"])
def add_money(message):
    if str(message.from_user.id) not in admin_ids:
        bot.reply_to(message, "Вы не администратор.")
        return
    id_message = bot.send_message(message.chat.id, "Введите id того, кому нужно начислить монет: ")
    bot.register_next_step_handler(id_message, add_money2)

def add_money2(message):
    try:
        id_message = message.text
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        find_initial_coins = """SELECT tg_id from tumo_coins_main_table"""
        c.execute(find_initial_coins)
        names = c.fetchall()[0]
        exists = False
        for i in names:
            print(str(i))
            if str(i) == id_message:
                exists = True
        if not exists:
            bot.send_message(message.chat.id, "Такого пользователя не существует.")
            return

        money_message = bot.send_message(message.chat.id, "Введите количество монет: ")
        bot.register_next_step_handler(money_message, add_money3, id_message)
    except Exception as e:
        print(e)
        pass
def add_money3(message, id_message):
    try:
        money_message = message.text
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        find_initial_coins = """SELECT coins, name from tumo_coins_main_table where tg_id = ?"""
        update_coins = """UPDATE tumo_coins_main_table SET coins = ? where tg_id = ?"""
        c.execute(find_initial_coins, (id_message, ))
        initital_coins_and_name = c.fetchall()[0]
        initital_coins = initital_coins_and_name[0]
        name = initital_coins_and_name[1]
        final_coins =  int(initital_coins) + int(money_message)
        c.execute(update_coins, (str(final_coins), str(id_message)))
        con.commit()
        con.close()
        bot.send_message(message.from_user.id, f"Вы успешно зачислили на аккаунт {id_message} ({name}) {money_message} монет.")
    except Exception as e:
        print(e)
        pass

@bot.message_handler(commands=["new_account"])
def new_account(message):
    try:
        global default_coins
        user_id = str(message.from_user.id)
        if check_if_acc_exists(user_id):
            bot.reply_to(message, "Ваш аккаунт уже существует.")
            return
        nameMsg = bot.send_message(message.chat.id, "Введите имя аккаунта (без пробелов, латинские или русские буквы). \nНапример: Василий_Васильевич")
        def account_create(message):
            if len(message.text.split(" ")) != 1:
                bot.send_message(message.chat.id, "В имени аккаунта не может быть пробелов.")
                new_account(message)
                return
            create_new_user(current_id, message.text, default_coins, user_id)
            bot.reply_to(message, "Ваш аккаунт успешно создан! На него зачислено " + str(default_coins) + " монет.")
        bot.register_next_step_handler(nameMsg, account_create)
    except Exception as e:
        print(e)
        pass

def create_new_user(id, name, coins, tg_id):
    try:
        global current_id
        sqlite_connection = sqlite3.connect('TUMO_MAIN_DB.db')
        c = sqlite_connection.cursor()

        new_user_insert = """INSERT INTO tumo_coins_main_table
                            (id, name, coins, tg_id)
                            VALUES (?, ?, ?, ?);"""


        data_tuple = (id, name, coins, tg_id)
        current_id += 1
        c.execute(new_user_insert, data_tuple)
        sqlite_connection.commit()
        c.close()
    except sqlite3.Error as e:
        print(e)
        pass

def check_if_acc_exists(user_id):
    try:
        sqlite_connection = sqlite3.connect('TUMO_MAIN_DB.db')
        c = sqlite_connection.cursor()
        sql_select_query = """select tg_id from tumo_coins_main_table"""
        c.execute(sql_select_query)
        id_data = c.fetchall()
        sqlite_connection.close()
        for row in id_data:
            if row[0] == user_id:
                return True
        return False
    except sqlite3.Error as e:
        print(e)
        pass

@bot.message_handler(commands=["coins"])
def get_coins(message):
    try:
        user_id = str(message.from_user.id)
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        if not check_if_acc_exists(user_id):
            bot.reply_to(message, "У вас нет аккаунта! Чтобы его создать, используйте команду /new_account ")
            return
        get_coins_data = """SELECT coins from tumo_coins_main_table where tg_id =?"""
        c.execute(get_coins_data, (user_id,))
        coins_data = c.fetchall()
        con.close()
        bot.reply_to(message, "На вашем аккаунте " + str(coins_data[0][0]) + " монет. ")
    except sqlite3.Error or Exception as e:
        print(e)
        pass

@bot.message_handler(commands=["new_event"])
def new_act_1(message):
    try:
        if str(message.from_user.id) not in admin_ids:
            bot.reply_to(message, "Вы не администратор.")
            return
        nameMsg = bot.send_message(message.chat.id, "Введите название нового события (до 16 символов) : ")
        bot.register_next_step_handler(nameMsg, new_act_2)
    except sqlite3.Error or Exception as e:
        print(e)
        pass

def new_act_2(message):
    try:
        act_name = message.text
        if len(act_name) >16:
            bot.send_message(message.chat.id, "Название события слишком длинное.")
            return
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        get_names = """SELECT name from tumo_activities_main_table"""
        c.execute(get_names)
        res = c.fetchall()
        for act in res:
            if act_name in act:
                bot.send_message(message.chat.id, "Событие с таким названием уже существует.")
                return
        priceMsg = bot.send_message(message.chat.id, "Введите стоимость нового события: ")
        bot.register_next_step_handler(priceMsg, new_act_3, act_name)
        con.close()
        return
    except Exception as e:
        print(e)
        pass

def new_act_3(message, name):
    try:
        price = message.text
        try:
            price_int = int(price)
        except Exception as e:
            bot.send_message(message.from_user.id, "Стоимость должна быть числом.")
            return
        descMsg = bot.send_message(message.chat.id, "Введите описание нового события: ")
        bot.register_next_step_handler(descMsg, new_act_4, name, price)
    except Exception as e:
        print(e)
        pass

def new_act_4(message, name, price):
    try:
        global names_to_descs
        desc = message.text
        names_to_descs[name] = desc
        markup_inline = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text="Да", callback_data= price + "~~~" + name)
        item_no = types.InlineKeyboardButton(text="Нет", callback_data="activity_denied")
        markup_inline.add(item_yes, item_no)
        bot.send_message(message.chat.id, "Создать событие?"
                                                            "\n Название: " +name+
                                                            "\n Цена: " +price +
                                                            "\n Описание: "+ desc, reply_markup= markup_inline)
    except Exception as e:
        print(e)
        pass

def create_new_activity(id, name, price, description):

        global current_activity_id
        sqlite_connection = sqlite3.connect('TUMO_MAIN_DB.db')
        c = sqlite_connection.cursor()

        new_user_insert = """INSERT INTO tumo_activities_main_table
                                    (id, name, price, descript)
                                    VALUES (?, ?, ?, ?);"""

        data_tuple = (id, name, price, description)
        current_activity_id += 1
        c.execute(new_user_insert, data_tuple)
        sqlite_connection.commit()
        sqlite_connection.close()

@bot.message_handler(commands=["event_list"])
def send_activity_list(message):
    bot.send_message(message.chat.id, show_activities(message))

def show_activities(message):
    try:
        n =1
        text = "Вот доступные события: \n"
        con = sqlite3.connect("TUMO_MAIN_DB.db")
        c = con.cursor()
        get_activities = """SELECT * from tumo_activities_main_table"""
        get_user_coins = """SELECT coins from tumo_coins_main_table where tg_id = ?"""
        c.execute(get_user_coins, (message.chat.id,))
        init_coins = c.fetchall()[0][0]
        c.execute(get_activities)
        activities = c.fetchall()

        get_events = """SELECT activities from tumo_coins_main_table where tg_id = ?"""
        c.execute(get_events, (message.chat.id, ))
        user_events = c.fetchall()[0][0].split("\n")
        nums_to_names = {}
        nums_to_prices = {}
        for act in activities:
            if act[1] in user_events:
                bilet = "куплен."
            else:
                bilet = "не куплен."
            text+= f" \t\n{n})  Название: {act[1]} \n\t     Цена: {act[2]} \n\t     Описание: {act[3]}\n\t     Билет: {bilet}\n"
            nums_to_names[n] = act[1]
            nums_to_prices[n] = act[2]
            n+=1
        return [text, len(activities), nums_to_names, nums_to_prices, init_coins, user_events]
        con.close()
    except sqlite3.Error or Exception as e:
        print(e)
        pass

@bot.message_handler(commands=["buy_a_ticket"])
def buy_a_ticket(message):
    try:
        if not check_if_acc_exists(str(message.from_user.id)):
            bot.send_message(message.chat.id, "Вашего аккаунта не существует. Чтобы его создать, используйте команду /new_account")
            return
        text_num = show_activities(message)
        text = text_num[0]
        max_num = text_num[1]
        nums_to_names = text_num[2]
        nums_to_prices = text_num[3]
        init_coins = text_num[4]
        user_events = text_num[5]
        text+= f"\n\nНа вашем аккануте {init_coins} монет. \nВведите номер события, которого хотите посетить. \n Введите 0 чтобы отменить покупку."
        activity_num = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(activity_num, confirm_ticket_purchase, max_num, nums_to_names, nums_to_prices, init_coins, user_events)
    except Exception as e:
        print(e)
        pass

def confirm_ticket_purchase(message, max_num, nums_to_names, nums_to_prices, init_coins, user_events):
    try:
        try:
            ansr = int(message.text)
            if ansr > max_num:
                bot.send_message(message.chat.id, "Такого числа нет в списке событий.")
                return
        except Exception as e:
            bot.send_message(message.chat.id, 'Когда я говорю "вводите число", вводите число.')
            buy_a_ticket(message)
            return
            pass
        if nums_to_names[ansr] in user_events:
            bot.send_message(message.chat.id, "У вас уже есть билет на это событие!")
            return
        if init_coins < int(nums_to_prices[ansr]):
            bot.send_message(message.chat.id, "У вас недостаточно монет.")
            return
        markup_inline = types.InlineKeyboardMarkup()
        item_yes = types.InlineKeyboardButton(text="Да", callback_data= str(nums_to_names[ansr]) + "~~~" +str(nums_to_prices[ansr] + "~~~" + str(init_coins) + "~~~" + str(1)))
        item_no = types.InlineKeyboardButton(text="Нет", callback_data="ticket_purchase_aborted")
        markup_inline.add(item_yes, item_no)
        bot.send_message(message.chat.id, f"Вы уверены, что хотите купить билет на событие {nums_to_names[ansr]} за {nums_to_prices[ansr]} монет?", reply_markup= markup_inline)
    except Exception as e:
        print(e)
        pass

@bot.message_handler(commands = ["my_events"])
def get_events(message):
    if not check_if_acc_exists(str(message.from_user.id)):
        bot.send_message(message.chat.id,
                         "Вашего аккаунта не существует. Чтобы его создать, используйте команду /new_account")
        return
    con = sqlite3.connect("TUMO_MAIN_DB.db")
    c = con.cursor()
    get_events = """SELECT activities from tumo_coins_main_table where tg_id = ?"""
    c.execute(get_events, (message.chat.id,))
    events = c.fetchall()[0][0]
    bot.send_message(message.chat.id, "Вот список событий, на которые у вас есть билет: " + events)

while True:
    try:
        bot.polling()
    except:
        time.sleep(10)
        bot.polling()
