# -*- coding: utf-8 -*-

import random
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
                print("There isn't " + str)
        return workers


class BaseWorker(object, metaclass=WorkersList):
    __not_bot__ = True

    HELP = ""
    
    def __init__(self, teleapi):
        self.tAPI = teleapi
        self.MENU_KEYBOARD = [
            [{'text': "Получить фильм(ы), из которого персонаж", 'callback_data': Encyclopedia.COMMAND+'ch'}],
            #[{'text': "Получить список персонажей фильма", 'callback_data': Encyclopedia.COMMAND+'m'}],
            #[{'text': "Найти фильм/персонажей по приблизительной цитате", 'callback_data': Encyclopedia.COMMAND}],
            #[{'text': "Получить список найденных мною фильмов и персонажей по цитате", 'callback_data': Encyclopedia.COMMAND}],
            [{'text': "Помощь/дополнительная информация", 'callback_data': Info.COMMAND}]
        ]



class Blacklist(BaseWorker):
    # HELP = "There is a blacklist for rude users!\n\n"

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
    HELP = COMMAND + " - call encyclopedia menu\n\n"

    waitlist = dict()

    def is_it_for_me(self, tmsg):
        return tmsg.text.startswith(self.COMMAND) or ((tmsg.pers_id, tmsg.chat_id) in self.waitlist)

    def run(self, tmsg):
        if (tmsg.pers_id == tmsg.chat_id):
            self.tAPI.db_shell.modify_last_activity(tmsg.pers_id, False)
        command = tmsg.text.split()
        if command.endswith('ch'):
            if len(command) > 1:
                self.tAPI.db_shell.get_movie_of_character(" ".join(command[1:]))
            else:
                self.waitlist[(tmsg.pers_id, tmsg.chat_id)] = 'ch'
                if tmsg.is_inline:
                    self.tAPI.edit("Type the character name", tmsg.chat_id, None, tmsg.id)
                else:
                    self.tAPI.send("Type the character name", tmsg.chat_id, reply_to_message_id=tmsg.id)
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        #TODO: Feel free to change
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
            self.tAPI.db_shell.initialize_user(tmsg.pers_id)
        if (tmsg.pers_id == tmsg.chat_id):
            self.tAPI.db_shell.modify_last_activity(tmsg.pers_id, False)
        HELP = ""
        for worker in WorkersList.workers:
            HELP += worker[1].HELP
        HELP = HELP[:-2]
        self.tAPI.send_inline_keyboard(HELP, tmsg.chat_id, self.MENU_KEYBOARD)
        return 0

    def quit(self, pers_id, chat_id, additional_info = '', msg_id = 0):
        pass
