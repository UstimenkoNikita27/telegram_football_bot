from telebot import TeleBot, types
import sqlite3

bot = TeleBot('')

squads = []
list_all_players = []
total_players = 10
players_in_one_team = int(total_players / 2)
number_of_possible_commands = 3
line_limit = 500

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('/+'))
    markup.add(types.KeyboardButton('/-'))
    markup.add(types.KeyboardButton('/рег'))
    markup.add(types.KeyboardButton('/я'))
    markup.add(types.KeyboardButton('/таблица'))
    markup.add(types.KeyboardButton('/очистка'))
    markup.add(types.KeyboardButton('/все'))
    markup.add(types.KeyboardButton('/рейтинг'))
    markup.add(types.KeyboardButton('/рейтингвсе'))
    markup.add(types.KeyboardButton('/рейтингмои'))
    markup.add(types.KeyboardButton('/помощь'))
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS players (player VARCHAR(35), rating INTEGER, sum_ratings INTEGER, number_of_ratings INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS dict_of_registered (player VARCHAR(35), rating INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS default_players (id INTEGER, player VARCHAR(35), name TEXT, rating_name TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS poll_answer (poll_id INTEGER, player VARCHAR(35))")
    bot.send_message(message.chat.id, 'Готов к работе', reply_markup=markup)
    output_help(message_id=message.chat.id)

@bot.message_handler(commands=['+'])
def plus(message):
    flag, full_name = more_one_word(text=message.text)
    if flag:
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT player FROM players WHERE player='{full_name}'")
            fetchone = c.fetchone()
        if fetchone:
            adding_without_duplicates(message_id=message.chat.id, player=full_name)
        else:
            bot.send_message(message.chat.id, 'Необходимо сначала зарегистрировать этого игрока')
    else:
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT player FROM default_players WHERE id='{message.from_user.id}'")
            fetchone = c.fetchone()[0]
        if fetchone:
            adding_without_duplicates(message_id=message.chat.id, player=fetchone)
        else:
            bot.send_message(message.chat.id, 'Необходимо ввести /+ если вы уже зарегистрировались по умолчнию или /+ и человека, которого хотите записать (он обязательно должен быть зарегистрирован)')

@bot.message_handler(commands=['-'])
def minus(message):
    flag, full_name = more_one_word(text=message.text)
    if flag:
        minus_player(message_id=message.chat.id, player=full_name)
    else:
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT player FROM default_players WHERE id='{message.from_user.id}'")
            fetchone = c.fetchone()[0]
        if fetchone:
            minus_player(message_id=message.chat.id, player=fetchone)
        else:
            bot.send_message(message.chat.id, 'Необходимо сначала зарегистрировать этого игрока')

@bot.message_handler(commands=['рег', 'Рег'])
def registration(message):
    flag, full_name = more_one_word(text=message.text)
    if flag:
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT player FROM players WHERE player='{full_name}'")
            if c.fetchone() is None:
                bot.send_message(message.chat.id, f'Игрок {full_name} успешно добавлен')
                c.execute("INSERT INTO players VALUES (?, ?, ?, ?)", [full_name, 0, 0 ,0])
            else:
                bot.send_message(message.chat.id, f'Игрок {full_name} уже зарегистрирован')
    else:
        bot.send_message(message.chat.id, 'Введите /рег и человека, которого хотите зарегистрировать')

@bot.message_handler(commands=['я', 'Я'])
def i(message):
    flag, full_name = more_one_word(text=message.text)
    if flag:
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT player FROM players WHERE player='{full_name}'")
            if c.fetchone() is None:
                c.execute("INSERT INTO players VALUES (?, ?, ?, ?)", [full_name, 0, 0, 0])
                bot.send_message(message.chat.id, f'Теперь вы {full_name} по умолчанию, но у вас нет рейтинга')
            else:
                bot.send_message(message.chat.id, f'Теперь вы {full_name} по умолчанию')
            c.execute(f"SELECT player FROM default_players WHERE id='{message.from_user.id}'")
            if c.fetchone() is None:
                c.execute("INSERT INTO default_players VALUES (?, ?, ?, ?)", [message.from_user.id, full_name, None, None])
            else:
                c.execute("UPDATE default_players SET player = ? WHERE id = ?", [full_name, message.from_user.id])
    else:
        bot.send_message(message.chat.id, 'Введите /я и человека, которым хотите быть')

@bot.message_handler(commands=['таблица', 'Таблица'])
def table(message):
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute("SELECT * FROM dict_of_registered")
        fetchone = c.fetchone()
    if fetchone is None:
        bot.send_message(message.chat.id, 'Пока никто не записался')
    else:
        list_output(message_id=message.chat.id)

@bot.message_handler(commands=['очистка', 'Очистка'])
def table_clearing(message):
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute("DELETE FROM dict_of_registered")
    bot.send_message(message.chat.id, 'Таблица успешно очищена')

@bot.message_handler(commands=['все', 'Все'])
def all_players(message):
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute("SELECT player, rating FROM players")
        items = c.fetchall()
    if items is None:
        bot.send_message(message.chat.id, "Пока нет зарегистрированных игроков")
    else:
        text = ''
        for player, rating in items:
            text += f'{player}: {rating}\n'
        bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['рейтинг', 'Рейтинг'])
def rating(message):
    flag, full_name = more_one_word(text=message.text)
    word_list = full_name.split()
    if flag and len(word_list) > 1:
        player = ''
        for i in range(len(word_list)-1):
            if i+2 == len(word_list):
                try:
                    player_rating = int(word_list[-1])
                except ValueError:
                    player_rating = 0
                player += word_list[i]
            else:
                player += word_list[i] + ' '
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT player FROM players WHERE player='{player}'")
            fetchone = c.fetchone()
        if fetchone is None:
            bot.send_message(message.chat.id, f'Игрок {player} пока не зарегистрировался')
        else:
            if 1 <= player_rating <= 10:
                add_rating(user_id=message.from_user.id, player=player, player_rating=player_rating)
            else:
                bot.send_message(message.chat.id, 'В конце обязательно должно быть число от 1 до 10')
    else:
        bot.send_message(message.chat.id, 'Введите /рейтинг, человека, которому хотите добавить рейтинг, и сам рейтинг(от 1 до 10)')

@bot.message_handler(commands=['рейтингвсе', 'Рейтингвсе'])
def rating_all(message):
    options = [str(i) for i in range(1, 11)]
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute("SELECT player, rating FROM players")
        players = c.fetchall()
        for player, rating in players:
            poll_message = bot.send_poll(message.chat.id, f"{player} (сейчас рейтинг {rating})", options=options, is_anonymous=False, allows_multiple_answers=False)
            c.execute("INSERT INTO poll_answer VALUES (?, ?)", [poll_message.poll.id, player])
            db.commit()
        flag = True
        while flag:
            c.execute('SELECT COUNT(*) FROM poll_answer')
            if c.fetchone()[0] > line_limit:
                c.execute('DELETE FROM poll_answer WHERE rowid = (SELECT MIN(rowid) FROM poll_answer)')
            else:
                flag = False

@bot.poll_answer_handler()
def rating_all_answer(poll_answer):
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute(f"SELECT player FROM poll_answer WHERE poll_id = {poll_answer.poll_id}")
        fetchone = c.fetchone()
    if fetchone:
        add_rating(user_id=poll_answer.user.id, player=fetchone[0], player_rating=poll_answer.option_ids[0]+1)

@bot.message_handler(commands=['рейтингмои', 'Рейтингмои'])
def rating_my(message):
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute(f"SELECT name, rating_name FROM default_players WHERE id={message.from_user.id}")
        fetchone = c.fetchone()
    if fetchone:
        fetchone0 = fetchone[0]
        fetchone1 = fetchone[1]
        if fetchone0:
            fetchone0 = fetchone0.split('\n')
            fetchone1 = fetchone1.split('\n')
            text = ''
            for i in range(len(fetchone0)):
                list_all_players.append(f"{fetchone0[i]}: {fetchone1[i]}\n")
            list_all_players.sort()
            for i in range(len(list_all_players)):
                text += list_all_players[i]
            list_all_players.clear()
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, 'Вы пока никому не ставили рейтинги')

@bot.message_handler(commands=['помощь', 'Помощь'])
def help(message):
    output_help(message_id=message.chat.id)

def list_output(*, message_id: int, initial_text: str = '') -> None:
    final_text = initial_text
    n = 1
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        items = c.execute("SELECT * FROM dict_of_registered")
    for player, rating in items:
        final_text += f'{n}) {player}: {rating}\n'
        n += 1
    bot.send_message(message_id, final_text)

def fullness_check(*, message_id: int) -> None:
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        ratings = c.execute("SELECT rating FROM dict_of_registered")
    if len(ratings) == total_players:
        list_output(message_id=message_id, initial_text='Все игроки записались\n')
        if all(1 <= x[0] <= 10 for x in ratings):
            possible_commands()
            output_possible_commands(message_id=message_id)
            output_voting(message_id=message_id)
        else:
            bot.send_message(message_id, 'Чтобы бот предлагал возможные команды у каждого игрока должен быть рейтинг от 1 до 10')
    elif len(ratings) > total_players:
        bot.send_message(message_id, f'Уже слишком много человек ({len(ratings)})')
    else:
        bot.send_message(message_id, f'Осталось {total_players - len(ratings)} свободных мест')

def possible_commands() -> None:
    squads.clear()
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        ratings = c.execute("SELECT rating FROM dict_of_registered")
        sum_of_ratings = sum(x[0] for x in ratings)
        average_team_rating = sum_of_ratings/2
        currents_difference = [sum_of_ratings for i in range(number_of_possible_commands)]
        items = c.execute("SELECT * FROM dict_of_registered")
    for key1, value1 in items:
        for key2, value2 in items:
            for key3, value3 in items:
                for key4, value4 in items:
                    for key5, value5 in items:
                        list_of_first_team_players = {key1: value1, key2: value2, key3: value3, key4: value4, key5: value5}
                        if len(list_of_first_team_players) == players_in_one_team:
                            sum_ratings_first_team_result = sum([value for value in list_of_first_team_players.values()])
                            difference_from_team_average = abs(sum_ratings_first_team_result - average_team_rating)
                            if difference_from_team_average <= currents_difference[0]:
                                flag = True
                                for i in range(len(squads)):
                                    if list_of_first_team_players == squads[i][0] or list_of_first_team_players == squads[i][2]:
                                        flag = False
                                        break
                                if flag:
                                    sum_ratings_second_team_result = sum_of_ratings - sum_ratings_first_team_result
                                    currents_difference.pop(0)
                                    currents_difference.append(difference_from_team_average)
                                    list_of_second_team_players = {}
                                    for key, value in items:
                                        if key not in list_of_first_team_players.keys():
                                            list_of_second_team_players[key] = value
                                    squads.append([list_of_first_team_players, sum_ratings_first_team_result, list_of_second_team_players, sum_ratings_second_team_result])
                                    if len(squads) > number_of_possible_commands:
                                        squads.pop(0)

def output_possible_commands(*, message_id: int) -> None:
    text = 'Возможные команды:\n1) Первая команда: '
    n = 2
    for teams in squads:
        for key, value in teams[0].items():
            text += f'{key} = {value}, '
        text += f'сумма рейтингов = {teams[1]}\nВторая команда: '
        for key, value in teams[2].items():
            text += f'{key} = {value}, '
        text += f'сумма рейтингов = {teams[3]}\n'
        if n <= number_of_possible_commands:
            text += f'{n}) Первая команда: '
            n += 1
    bot.send_message(message_id, text)

def output_voting(*, message_id: int) -> None:
    options = [str(i) for i in range(1, number_of_possible_commands + 1)]
    options.append('Свой вариант')
    bot.send_poll(message_id, 'Какие команды', options=options, is_anonymous=False, allows_multiple_answers=False)

def more_one_word(*, text: str) -> [bool, str]:
    words = text.split()
    flag = len(words) > 1
    if flag:
        full_name = ''
        for i in range(1, len(words)):
            full_name += words[i]
            if i != len(words)-1:
                full_name += ' '
    else:
        full_name = words[0]
    return flag, full_name

def adding_without_duplicates(*, message_id: int, player: str) -> None:
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute(f"SELECT player FROM dict_of_registered WHERE player='{player}'")
        if c.fetchone() is None:
            c.execute(f"SELECT rating FROM players WHERE player='{player}'")
            rating = c.fetchone()[0]
            c.execute("INSERT INTO dict_of_registered VALUES (?, ?)", [player, rating])
            bot.send_message(message_id, f'Игрок {player} успешно записался')
            db.commit()
            fullness_check(message_id=message_id)
        else:
            bot.send_message(message_id, f'Игрок {player} уже записался до этого')

def minus_player(*, message_id: int, player: str) -> None:
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute(f"SELECT player FROM dict_of_registered WHERE player='{player}'")
        if c.fetchone() is None:
            bot.send_message(message_id, f'Игрок {player} поставил -')
        else:
            c.execute("DELETE FROM dict_of_registered WHERE player = ?", [player])
            bot.send_message(message_id, f'Игрок {player} изменил свой + на -')

def add_rating(*, user_id: int, player: str, player_rating: int):
    with sqlite3.connect("main.db") as db:
        c = db.cursor()
        c.execute(f"SELECT name, rating_name FROM default_players WHERE id='{user_id}'")
        fetchone = c.fetchone()
    if fetchone:
        fetchone0 = fetchone[0]
        fetchone1 = fetchone[1]
        flag = True
        if fetchone0:
            fetchone0 = fetchone0.split('\n')
            fetchone1 = fetchone1.split('\n')
            fetchone0_final = ''
            fetchone1_final = ''
            for i in range(len(fetchone0)):
                if fetchone0[i] == player:
                    rate = int(fetchone1[i])
                    fetchone1[i] = player_rating
                    flag = False
                fetchone0_final += f'{fetchone0[i]}'
                fetchone1_final += f'{fetchone1[i]}'
                if i < len(fetchone0) - 1:
                    fetchone0_final += '\n'
                    fetchone1_final += '\n'
        else:
            fetchone0_final = ''
            fetchone1_final = ''
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute(f"SELECT sum_ratings, number_of_ratings FROM players WHERE player='{player}'")
            fetchone = c.fetchone()
        if flag:
            new_sum_ratings = fetchone[0] + player_rating
            new_number_of_ratings = fetchone[1] + 1
            if fetchone0_final == '':
                new_name = player
                new_rating_name = player_rating
            else:
                new_name = f'{fetchone0_final}\n{player}'
                new_rating_name = f'{fetchone1_final}\n{player_rating}'
        else:
            new_sum_ratings = fetchone[0] + player_rating - rate
            new_number_of_ratings = fetchone[1]
            new_name = fetchone0_final
            new_rating_name = fetchone1_final
        new_rating = int(new_sum_ratings / new_number_of_ratings)
        with sqlite3.connect("main.db") as db:
            c = db.cursor()
            c.execute("UPDATE default_players SET name = ?, rating_name = ? WHERE id = ?",[new_name, new_rating_name, user_id])
            c.execute("UPDATE players SET rating = ?, sum_ratings = ?, number_of_ratings = ? WHERE player = ?",[new_rating, new_sum_ratings, new_number_of_ratings, player])
            c.execute("UPDATE dict_of_registered SET rating = ? WHERE player = ?", [new_rating, player])

def output_help(*, message_id: int) -> None:
    bot.send_message(message_id, '''Список команд:
/+: добавляет в список
/-: удаляет из списка
/рег: регистрирует нового игрока
/я: добавить себя по умолчанию
/таблица: показывает кто уже записался
/очистка: очищает таблицу
/все: показывает всех зарегистрированных игроков с их рейтингами
/рейтинг: можно добавить любому игроку рейтинг от 1 до 10, чтобы потом бот предлагал сбалансированные команды
/рейтингвсе: создаёт опросы по рейтингу каждого игрока 
/рейтингмои: выводит все рейтинг которые ты ставил
/помощь: показывает все возможные команды бота и их функционал

Также, чтобы вы смогли добавлять всем рейтинги, необходимо зарегестрироваться по умолчанию, используя команду /я''')

bot.polling(none_stop=True)
