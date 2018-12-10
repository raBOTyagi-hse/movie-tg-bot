class Msg():
    def __init__(self, msg, bot_nick):
        self.BOT_NICK = bot_nick
        is_dict = isinstance(msg, dict)
        if ('callback_query' in msg) if is_dict else not msg['callback_query'] is None:
            self.msg = msg['callback_query']['message']
            self.from_data = msg['callback_query']['from' if is_dict else 'from_user']
            self.inline_data = msg['callback_query']['data']

        elif ('message' in msg) if is_dict else not msg['message'] is None:
            self.msg = msg['message']
            self.from_data = msg['message']['from' if is_dict else 'from_user']
            self.inline_data = None

        if ('first_name' in self.msg) if is_dict else False:
            self.name = self.msg['first_name']
        else:
            self.name = 'Anonymous'

        if ('last_name' in self.msg) if is_dict else False:
            self.surname = self.msg['last_name']
        else:
            self.surname = 'Anonymous'

        if ('username' in self.msg) if is_dict else False:
            self.username = self.msg['username']
        else:
            self.username = 'Anonymous'

        if ('text' in self.msg) if is_dict else not self.msg['text'] is None:
            self.text = self.msg['text']
        else:
            self.text = ''

        if not self.inline_data is None:
            self.text_of_inline_root = self.text
            self.text = self.inline_data



    @property
    def id(self):
        return self.msg['message_id']

    @property
    def chat_id(self):
        return self.msg['chat']['id']

    @property
    def pers_id(self):
        return self.from_data['id']

    # @property
    # def name(self):
    #    return self.from_data.get('first_name', 'Anonymous')

    # @property
    # def surname(self):
    #    return self.from_data.get('last_name', 'Anonymous')

    # @property
    # def text(self):
    #    if self.inline_data == None:
    #        return self.msg.get('text', '')
    #    else:
    #        return self.inline_data

    # @property
    # def text_of_inline_root(self):
    #    return self.msg.get('text', '')

    @property
    def is_inline(self):
        return self.inline_data != None

    def text_change_to(self, new_value):
        if self.inline_data == None:
            self.msg['text'] = new_value
        else:
            self.inline_data = new_value

    def text_replace(self, template, new_value, func=None):
        if self.inline_data == None:
            strk = self.msg['text']
            self.msg['text'] = func(template, new_value, strk)

    def textmod(self):
        if self.inline_data == None:
            # self.msg['text'] = self.msg['text'].strip().replace(self.BOT_NICK, "")
            self.text = self.text.strip().replace(self.BOT_NICK, "")
