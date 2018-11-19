from configobj import ConfigObj

config = ConfigObj()
config.filename = "config_example.cfg"
config['APIs'] = {
    'bot_nick': "@coolbot",
    'telegram_chatlink': 'https://api.telegram.org/bot',
    'telegram_api': "000000000:api_key"
}
config['admins_ids'] = [
    "admin_id0",
    "admin_id1"
]
config['included_workers'] = [
    #"Blacklist",
    "Stop",
    "Humanity",
    "Info",
    "Example"
]
config['included_service_workers'] = [
    #"Autoquit"
]
config["user_inactivity_time_at_minutes"] = 5
config.initial_comment = ["Change values which you want, rename file to \"config.cfg\" and delete this string!"]
config.final_comment = [""]
config.write()