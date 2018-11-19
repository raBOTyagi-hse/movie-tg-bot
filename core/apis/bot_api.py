# -*- coding: utf-8 -*-

import requests
import json
from core.workers.service_workers import WorkersList as ServiceWorkersList

from telegram.ext import Updater

__author__ = 'NickVeld'


class API:
    def __init__(self):
        self.telegram = Tg_api()
        self.additional = Additional()
        self.offset = 0

        self.admin_ids = list()
        self.BOT_NICK = ""

        self.workers_list = None

    def get_from_config(self, cfg):
        self.admin_ids = list(cfg['admins_ids'])

        self.BOT_NICK = cfg['APIs']['bot_nick']

        self.telegram.get_from_config(cfg['APIs'])
        self.additional.get_from_config(cfg['APIs'])

        self.service_workers_list = ServiceWorkersList.get_workers(ServiceWorkersList
                                                                   , cfg["included_service_workers"], self)

    def get(self, toffset=0):
        return self.telegram.get(toffset)

    def get_msg(self):
        while True:
            for worker in self.service_workers_list:
                if worker.is_it_for_me():
                    cmd = worker.run()
                    if cmd != 1:
                        break
            new_msgs = self.get(self.offset)
            if new_msgs is None:
                continue

            for msg in new_msgs['result']:
                self.offset = msg['update_id']
                yield msg

    def send(self, message, chat_id, reply_to_message_id=0, keyboard=None):
        self.telegram.send(message, chat_id, reply_to_message_id)
        return message

    def send_with_id(self, message, chat_id, reply_to_message_id=0, keyboard=None):
        return self.telegram.send(message, chat_id, reply_to_message_id)

    def send_inline_keyboard(self, message, chat_id, inline_keyboard, reply_to_message_id=0, image_url = ""):
        self.telegram.send_inline_keyboard(message, chat_id, inline_keyboard, reply_to_message_id, image_url)
        return message

    def send_inline_keyboard_with_id(self, message, chat_id, inline_keyboard, reply_to_message_id=0):
        return self.telegram.send_inline_keyboard(message, chat_id, inline_keyboard, reply_to_message_id)

    def edit(self, message, chat_id, inline_keyboard, message_id):
        return self.telegram.edit(message, chat_id, inline_keyboard, message_id)

    def get_inline_text_keyboard(self, source):
        return self.telegram.get_inline_text_keyboard(source)


class Tg_api:

    def __init__(self):
        pass

    def get_from_config(self, cfg):
        self.CHAT_LINK = cfg['telegram_chatlink']
        self.API_KEY = cfg['telegram_api']

    def get(self, toffset=0, timeout=29):
        method = 'getUpdates'
        params = {
            'offset': toffset + 1,
            'timeout': timeout
        }
        try:
            req = requests.request(
                'POST',
                '{link}{api_key}/{method}'.format(
                    link=self.CHAT_LINK,
                    api_key=self.API_KEY,
                    method=method
                ),
                params=params,
                timeout=timeout+1
            )
            if req.text is "":
                return None

            new_msgs = json.loads(req.text)
            if new_msgs['ok'] and (len(new_msgs['result']) != 0):
                return new_msgs
        except requests.exceptions.Timeout:
            print("Timeout in get()!")
        except Exception as ex:
            print("Error in get()!")
            print(type(ex), ex.__str__())
        return None

    def send(self, message, chat_id, reply_to_message_id=0):
        method = 'sendMessage'
        params = {
            'chat_id': chat_id,
            'disable_web_page_preview': True,
            'text': message
        }
        if reply_to_message_id:
            params['reply_to_message_id'] = reply_to_message_id
        try:
            req = requests.request(
                'POST',
                '{link}{api_key}/{method}'.format(
                    link = self.CHAT_LINK,
                    api_key=self.API_KEY,
                    method=method
                ),
                params=params,
                timeout=30
            )
            sended = json.loads(req.text)
            if sended['ok']:
                return sended['result']['message_id']
        except requests.exceptions.Timeout:
            print("Timeout in send()!")
        except Exception as ex:
            print("Error in send()!")
            print(type(ex), ex.__str__())
        return 0

    def get_reply_keyboard(self, source):
        return [["/{}".format(c) for c in s_in.split('\t')] for s_in in source.split('\n')]

    def send_reply_keyboard(self, message, chat_id, keyboard, reply_to_message_id=0):
        method = 'sendMessage'
        params = {
            'chat_id': chat_id,
            'disable_web_page_preview': True,
            'text': message
        }
        if reply_to_message_id:
            params['reply_to_message_id'] = reply_to_message_id
        if keyboard != None:
            params["reply_markup"] = json.dumps({
                "keyboard": keyboard,
                "resize_keyboard": True,
                "one_time_keyboard": True,
                "selective": True
            })
        try:
            req = requests.request(
                'POST',
                '{link}{api_key}/{method}'.format(
                    link=self.CHAT_LINK,
                    api_key=self.API_KEY,
                    method=method
                ),
                params=params,
                timeout=30
            )
            sended = json.loads(req.text)
            if sended['ok']:
                return sended['result']['message_id']
        except requests.exceptions.Timeout:
            print("Timeout in send_reply_keyboard(...)!")
        except Exception as ex:
            print("Error in send_reply_keyboard(...)!")
            print(type(ex), ex.__str__())
        return 0

    def get_inline_text_keyboard(self, source):
        return list([[{'text': c,
                       'callback_data': "/{}".format(c)} for c in s_in.split('\t')] for s_in in source.split('\n')])

    def send_inline_keyboard(self, message, chat_id, inline_keyboard, reply_to_message_id=0, image_url = ""):
        params = {'chat_id': chat_id}
        if (image_url == ""):
            method = 'sendMessage'
            params['disable_web_page_preview'] = True
            params['text'] = message
        else:
            method = 'sendPhoto'
            params['caption'] = message
            params['photo'] = image_url

        if reply_to_message_id:
            params['reply_to_message_id'] = reply_to_message_id
        if inline_keyboard != None:
            params["reply_markup"] = json.dumps({
                "inline_keyboard": inline_keyboard
            })
        try:
            req = requests.request(
                'POST',
                '{link}{api_key}/{method}'.format(
                    link=self.CHAT_LINK,
                    api_key=self.API_KEY,
                    method=method
                ),
                params=params,
                timeout=30
            )
            sended = json.loads(req.text)
            if sended['ok']:
                return sended['result']['message_id']
        except requests.exceptions.Timeout:
            print("Timeout in send_inline_keyboard(...)!")
        except Exception as ex:
            print("Error in send_inline_keyboard(...)!")
            print(type(ex), ex.__str__())
        return 0

    def edit(self, message, chat_id, inline_keyboard, message_id):
        method = 'editMessageText'
        params = {
            'chat_id': chat_id,
            'message_id': message_id,
            'disable_web_page_preview': True,
            'text': message
        }
        if inline_keyboard != None:
            params["reply_markup"] = json.dumps({
                "inline_keyboard": inline_keyboard
            })
        try:
            req = requests.request(
                'POST',
                '{link}{api_key}/{method}'.format(
                    link=self.CHAT_LINK,
                    api_key=self.API_KEY,
                    method=method
                ),
                params=params,
                timeout=30
            )
        except requests.exceptions.Timeout:
            print("Timeout in edit(...)!")
        except Exception as ex:
            print("Error in edit(...)!")
            print(type(ex), ex.__str__())
        return message

#TODO: Use it if you need more APIs
class Additional:
    def __init__(self):
        pass

    def get_from_config(self, cfg):
        pass
