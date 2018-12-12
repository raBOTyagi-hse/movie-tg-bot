# -*- coding: utf-8 -*-

import sys

class WorkersList(type):
    workers = []

    def __new__(mcs, name, bases, attrs, **kwargs):
        worker_class = super(WorkersList, mcs).__new__(mcs, name, bases, attrs)
        if '__not_bot__' not in attrs:
            WorkersList.workers.append((name, worker_class))
        return worker_class

    def get_workers(cls, list, tapi):
        workers = []
        # available = cls.workers
        for worker in cls.workers:
            exist = False
            for str in list:
                if str == worker[0]:
                    exist = True
                    break
            if not exist:
                cls.workers.remove(worker)

        for str in list:
            try:
                workers.append(getattr(sys.modules[__name__], str)(tapi))
                print(str)
            except:
                print("There is no " + str)
        return workers


class BaseWorker(object, metaclass=WorkersList):
    __not_bot__ = True

    HELP = ""
    
    def __init__(self, teleapi):
        self.tAPI = teleapi
        self.MENU_KEYBOARD = [
            [{'callback_data': Encyclopedia.COMMAND + '1',
              #'text': "Get movies with the entered character",
              'text': "Получить фильм(ы), из которого(ых) введенный персонаж", }],
            [{'callback_data': Encyclopedia.COMMAND + '2',
              #'text': "Get all characters of the entered movie",
              'text': "Получить список персонажей введенного фильма", }],
            [{'callback_data': Encyclopedia.COMMAND + '3',
              'text': "Получить самые популярные для поиска фильмы"}],
            [{'callback_data': Encyclopedia.COMMAND + '4',
              'text': "Получить информацию о распределении по годам производства фильмов"}],
            [{'callback_data': Encyclopedia.COMMAND + '5',
              'text': "Получить информацию о количестве фильмов произведенных в один год с похожим рейтингом"}],
            [{'callback_data': Encyclopedia.COMMAND + '6',
              'text': "Получить мою историю запросов"}],
            [{'callback_data': Encyclopedia.COMMAND + '7',
              'text': "Найти фильм / персонажей по приблизительной цитате"}],
            [{'callback_data': Changer.COMMAND + '1',
              'text': "Сделать запрос на удаление персональных данных!", }],
            [{'callback_data': Changer.COMMAND + '2',
              'text': "Удалить фильм, так как я являюсь владельцев авторских прав!", }],
            [{'callback_data': Changer.COMMAND + '3',
              'text': "Удалить персонажа, так как он террорист или того хуже притесняет меньшинства!"}],
            [{'callback_data': Info.COMMAND,
              'text': "Помощь / дополнительная информация"}]
        ]

    def MENU_KEYBOARDsub(self, mask):
        res = []
        if False:
            curr_maski = 0
            for x in enumerate(self.MENU_KEYBOARD):
                if x[0] == mask[curr_maski]:
                    res.append(x[1])
                    curr_maski += 1
                    if curr_maski == len(mask):
                        break
        else:
            for curr_mask in mask:
                res.append(self.MENU_KEYBOARD[curr_mask])
        return res


class Blacklist(BaseWorker):
    HELP = ""  # "There is a blacklist for rude users!\n\n"

    def is_it_for_me(self, tmsg):
        if self.tAPI.DB_IS_ENABLED:
            return ((tmsg.text.startswith("/addbl")) or (tmsg.text.startswith("/delbl")) or
                    (self.tAPI.db_shell.is_in_blacklist(tmsg.pers_id)))
        return False

    def run(self, tmsg):
        # TODO adding and deleting from blacklist.
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id=None):
        pass


class Humanity(BaseWorker):
    HELP = "Поддерживается понимание некоторых свободных фраз\n\n"

    def __init__(self, teleapi):
        super(Humanity, self).__init__(teleapi)
        self.waitlist = set()
        import re
        self.re_ex = re.compile('[^A-Za-z]+')
        from core.services.сitation_search import CitationSearch
        self.csearch = CitationSearch([(x[0]['callback_data'], x[0]['text']) for x in self.MENU_KEYBOARD],
                                      mode='ru', stopwords_flag=False)
        self.csearch.tfidf_docs()

    def is_it_for_me(self, tmsg):
        return not (tmsg.text.startswith('/') or tmsg.is_inline)

    def run(self, tmsg):
        potential_command = self.re_ex.match(tmsg.text)
        if potential_command is None:
            return 1
        else:
            potential_command = potential_command.group(0)
        command, score = self.csearch.query_relevance(potential_command)
        if score > 0.6:
            tmsg.text_replace(potential_command, command + (' ' if potential_command[-1] == ' ' else ''))
        return 1

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        pass

class Stop(BaseWorker):
    COMMAND = "/StopPls"

    def is_it_for_me(self, tmsg):
        return (tmsg.text == self.COMMAND) and (str(tmsg.pers_id) == self.tAPI.admin_ids[0])

    def run(self, tmsg):
        print(self.tAPI.send("I'll be back, " + tmsg.name + "!", tmsg.chat_id))
        return 2

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        pass


class Encyclopedia(BaseWorker):
    COMMAND = "/encyc"
    HELP = COMMAND + " - вызывает меню энциклопедии\n\n"

    def __init__(self, teleapi):
        super(Encyclopedia, self).__init__(teleapi)
        self.waitlist = dict()
        from core.services.сitation_search import CitationSearch
        lines = self.tAPI.db_shell.get_all_lines()
        print(lines)
        self.csearch = CitationSearch(lines, mode='eng', stopwords_flag=False)
        self.csearch.tfidf_docs()

    def is_it_for_me(self, tmsg):
        return tmsg.text.startswith(self.COMMAND) or ((tmsg.pers_id, tmsg.chat_id) in self.waitlist)

    def run(self, tmsg):
        if (tmsg.pers_id == tmsg.chat_id):
            self.tAPI.db_shell.update_last_activity(tmsg.pers_id, False)
        if (tmsg.pers_id, tmsg.chat_id) in self.waitlist:
            query = tmsg.text
            command = self.waitlist[(tmsg.pers_id, tmsg.chat_id)]
        else:
            command = tmsg.text.split()
            query = " ".join(command[1:])
            command = command[0]
        if command.endswith(self.COMMAND):
            self.tAPI.send_inline_keyboard("Меню энциклопедии", tmsg.chat_id,
                                           [x for x in self.MENU_KEYBOARD if x[0]['callback_data'].startswith(self.COMMAND)],
                                           tmsg.id)
        elif command.endswith('1'):
            if len(query) > 1:
                ms = "Персонаж играет в:\n"  # "The character plays in:\n"
                self.tAPI.send_inline_keyboard(ms + ("\n".join(self.tAPI.db_shell.get_movies_of_character(query.upper()))),
                               tmsg.chat_id, self.MENU_KEYBOARDsub([1, 0, 6, 5]), tmsg.id)
                self.tAPI.db_shell.add_user_history(tmsg.pers_id, command + " " + query, 'NULL')
                self.quit(tmsg.pers_id, tmsg.chat_id)
            else:
                self.waitlist[(tmsg.pers_id, tmsg.chat_id)] = self.COMMAND + '1'
                ms = "Введите имя персонажа"  # "Type the character name"
                if tmsg.is_inline:
                    self.tAPI.edit(ms, tmsg.chat_id, None, tmsg.id)
                else:
                    self.tAPI.send(ms, tmsg.chat_id, reply_to_message_id=tmsg.id)
        elif command.endswith('2'):
            if len(query) > 1:
                ms = "Этот персонаж(и) играет в {}:\n{}"  # "This(ese) character(s) play in {}:\n{}"
                self.tAPI.send_inline_keyboard(ms.format(query,"\n".join(self.tAPI.db_shell.get_characters_of_movie(query.lower()))),
                               tmsg.chat_id, self.MENU_KEYBOARDsub([0, 1, 6, 5]), tmsg.id)
                self.tAPI.db_shell.add_user_history(tmsg.pers_id, command + " " + query, 'NULL')
                self.quit(tmsg.pers_id, tmsg.chat_id)
            else:
                self.waitlist[(tmsg.pers_id, tmsg.chat_id)] = self.COMMAND + '2'
                ms = "Введите название фильма" # "Type the movie title"
                if tmsg.is_inline:
                    self.tAPI.edit(ms, tmsg.chat_id, None, tmsg.id)
                else:
                    self.tAPI.send(ms, tmsg.chat_id, reply_to_message_id=tmsg.id)
        elif command.endswith('3'):
            print(command)
            self.tAPI.db_shell.add_user_history(tmsg.pers_id, command, 'NULL')
            ms = "Самые разыскиваемые фильмы:\n"  # "The most searched movies:\n"
            self.tAPI.send_inline_keyboard(ms + ("\n".join(map(lambda x: " ".join(x), self.tAPI.db_shell.get_most_searched_films()))),
                           tmsg.chat_id, self.MENU_KEYBOARDsub([3, 4, 0, 6]), tmsg.id)
        elif command.endswith('4'):
            self.tAPI.db_shell.add_user_history(tmsg.pers_id, command, 'NULL')
            ms = "Ссылка на гистограмму годов производства фильмов"  # "Link to movies production years histogram:
            self.tAPI.send_inline_keyboard(ms + "\nhttp://nminec.ddns.net/years_hist",
                tmsg.chat_id, self.MENU_KEYBOARDsub([4, 2, 0, 6]), tmsg.id)
        elif command.endswith('5'):
            self.tAPI.db_shell.add_user_history(tmsg.pers_id, command, 'NULL')
            ms = "Ссылка на кросстаблицу, которая содержит количество фильмов с одним годом производства и похожим рейтином"
                # "Link to crosstable that contains the amount of movies with equal production year and similiar rating"
            self.tAPI.send_inline_keyboard(ms + ":\nhttp://nminec.ddns.net/crosstable",
                tmsg.chat_id, self.MENU_KEYBOARDsub([3, 2, 0, 6]), tmsg.id)
        elif command.endswith('6'):
            self.tAPI.db_shell.add_user_history(tmsg.pers_id, command, 'NULL')
            ms = "Ваша история запросов:"
            self.tAPI.send_inline_keyboard(ms + ("\n".join(self.tAPI.db_shell.get_user_history(tmsg.pers_id))),
                tmsg.chat_id, self.MENU_KEYBOARDsub([2, 0, 1, 6]), tmsg.id)
        elif command.endswith('7'):
            if len(query) > 1:
                lineId, score = self.csearch.query_relevance(query)
                if score > 0.6:
                    lineText, movieId, movieTitle, characterName = self.tAPI.db_shell.get_line_movie_title_and_speaker(lineId)
                    if lineText == query:
                        ms = 'Вы ввели точную цитату!\n'
                    else:
                        ms = 'Может быть, вы эту цитату ниже имели в виду?\n{}'.format(lineText)
                    ms += '\n Она из фильма "{}", сказана персонажем {}'
                    self.tAPI.send_inline_keyboard(ms.format(movieTitle, characterName),
                                   tmsg.chat_id, self.MENU_KEYBOARDsub([7, 0, 1, 6]), tmsg.id)
                else:
                    movieId = 'NULL'
                    self.tAPI.send_inline_keyboard("Не было найдено ничего похожего",
                                   tmsg.chat_id, self.MENU_KEYBOARDsub([7, 0, 1, 6]), tmsg.id)
                self.tAPI.db_shell.add_user_history(tmsg.pers_id, command + " " + query, movieId)
                self.quit(tmsg.pers_id, tmsg.chat_id)
            else:
                self.waitlist[(tmsg.pers_id, tmsg.chat_id)] = self.COMMAND + '7'
                ms = "Введите предполагаемую цитату"
                if tmsg.is_inline:
                    self.tAPI.edit(ms, tmsg.chat_id, None, tmsg.id)
                else:
                    self.tAPI.send(ms, tmsg.chat_id, reply_to_message_id=tmsg.id)
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        if (pers_id, chat_id) in self.waitlist:
            self.waitlist.pop((pers_id, chat_id))
            if additional_info != '':
                self.tAPI.send_inline_keyboard(additional_info, chat_id, self.MENU_KEYBOARD, msg_id)

class Changer(BaseWorker):
    COMMAND = "/change"
    HELP = COMMAND + " - вызывает меню изменений\n\n"

    waitlist = dict()

    def is_it_for_me(self, tmsg):
        return tmsg.text.startswith(self.COMMAND) or ((tmsg.pers_id, tmsg.chat_id) in self.waitlist)

    def run(self, tmsg):
        if (tmsg.pers_id == tmsg.chat_id):
            self.tAPI.db_shell.update_last_activity(tmsg.pers_id, False)
        if (tmsg.pers_id, tmsg.chat_id) in self.waitlist:
            query = tmsg.text
            command = self.waitlist[(tmsg.pers_id, tmsg.chat_id)]
        else:
            command = tmsg.text.split()
            query = " ".join(command[1:])
            command = command[0]
        if command.endswith(self.COMMAND):
            self.tAPI.send_inline_keyboard("Меню изменений", tmsg.chat_id,
                                           [x for x in self.MENU_KEYBOARD if x[0]['callback_data'].startswith(self.COMMAND)],
                                           tmsg.id)
        elif command.endswith('1'):
            self.tAPI.db_shell.delete_user_history(tmsg.pers_id, tmsg.username)
            self.tAPI.send("Ваш запрос на удаление своих персональных данных удовлетоврен ",
                tmsg.chat_id, self.MENU_KEYBOARDsub([6, 0, 1, 7]), tmsg.id)

        elif command.endswith('2'):
            if len(query) > 1:
                self.tAPI.db_shell.delete_movie(query.lower())
                self.tAPI.db_shell.add_user_history(tmsg.pers_id, command + " " + query, 'NULL')
                self.tAPI.send_inline_keyboard("Несмотря на негодование пиратского сообщества фильм был удален",
                               tmsg.chat_id, self.MENU_KEYBOARDsub([8, 0, 1, 9]), tmsg.id)
                self.quit(tmsg.pers_id, tmsg.chat_id)
            else:
                self.waitlist[(tmsg.pers_id, tmsg.chat_id)] = self.COMMAND + '2'
                ms = "Введите название фильма"  # "Type the movie title"
                if tmsg.is_inline:
                    self.tAPI.edit(ms, tmsg.chat_id, None, tmsg.id)
                else:
                    self.tAPI.send(ms, tmsg.chat_id, reply_to_message_id=tmsg.id)
        elif command.endswith('3'):
            if len(query) > 1:
                self.tAPI.db_shell.delete_character(query.upper())
                self.tAPI.db_shell.add_user_history(tmsg.pers_id, command+" "+query, 'NULL')
                self.tAPI.send("Персонаж был наказан в суде и исключен из фильма",
                               tmsg.chat_id, self.MENU_KEYBOARDsub([9, 1, 0, 8]), tmsg.id)
                self.quit(tmsg.pers_id, tmsg.chat_id)
            else:
                self.waitlist[(tmsg.pers_id, tmsg.chat_id)] = self.COMMAND + '3'
                ms = "Введите имя персонажа"  # "Type the character name"
                if tmsg.is_inline:
                    self.tAPI.edit(ms, tmsg.chat_id, None, tmsg.id)
                else:
                    self.tAPI.send(ms, tmsg.chat_id, reply_to_message_id=tmsg.id)
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        if (pers_id, chat_id) in self.waitlist:
            self.waitlist.pop((pers_id, chat_id))
            if additional_info != '':
                self.tAPI.send_inline_keyboard(additional_info, chat_id, self.MENU_KEYBOARD, msg_id)


class Info(BaseWorker):
    COMMAND = "/help"

    def is_it_for_me(self, tmsg):
        return tmsg.text.startswith(self.COMMAND) or tmsg.text.startswith("/start")

    def run(self, tmsg):
        if tmsg.text.startswith("/start"):
            self.tAPI.db_shell.initialize_user(tmsg.pers_id, tmsg.username)
        if (tmsg.pers_id == tmsg.chat_id):
            self.tAPI.db_shell.update_last_activity(tmsg.pers_id, False)
        HELP = ""
        for worker in WorkersList.workers:
            HELP += worker[1].HELP
        HELP = HELP[:-2]
        self.tAPI.send_inline_keyboard(HELP, tmsg.chat_id, self.MENU_KEYBOARD)
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        pass


class Catcher(BaseWorker):
    HELP = "Если вы напишите неподдерживаемую команду, бот предупредит об этом.\n\n"
            # "If you write unsupported command, the bot will warn about it.\n\n"

    def is_it_for_me(self, tmsg):
        return True

    def run(self, tmsg):
        self.tAPI.send_inline_keyboard("Вы ввели неподдерживаемую или нераспозанную команду"
                                        # "You type unsupported or not recognized command"
                                       , tmsg.chat_id, self.MENU_KEYBOARD)
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        pass