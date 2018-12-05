import datetime
import mysql.connector

__author__ = 'NickVeld'


class DBShell:
    def __init__(self):
        self.db = None
        self.INACT_M = 5


    def get_from_config(self, cfg):
        self.db = (mysql.connector.connect(
            host=cfg["db_settings"]["host"],
            port=cfg["db_settings"]["port"],
            user=cfg["db_settings"]["user"],
            passwd=cfg["db_settings"]["passwd"]
        ) if cfg['db_settings']['isEnabled'] == 'True' else None).cursor()

        self.INACT_M = int(cfg["user_inactivity_time_at_minutes"])

    def is_in_blacklist(self, pers_id):
        return False

    def initialize_user(self, pers_id):
        self.db.execute("INSERT INTO Users VALUES ({}, {})".format(pers_id, datetime.datetime.min))

    def update_last_activity(self, pers_id, after_quit):
        if not self.db is None:
            self.db.execute("UPDATE Users SET last_activity = {} WHERE userId = {};".format(
                                datetime.datetime.min if after_quit else datetime.datetime.utcnow(), pers_id))


    def get_ready_for_autoquit(self):
        return self.db.execute("SELECT userId FROM Users WHERE last_activity > {} AND last_activity < {};".format(
                                datetime.datetime.min, datetime.datetime.utcnow() - datetime.timedelta(minutes=(self.INACT_M-1))))

    def get_characters_of_movie(self, movie):
        request = "SELECT DISTINCT chName FROM Characters"
        if isinstance(movie, int):
            request += "WHERE mId = " + str(movie)
        else:
            request += "JOIN Movies ON mName = {} AND mId = movieId".format(movie)
        return self.db.execute(request)

    def get_movie_of_character(self, character_name):
        return self.db.execute("SELECT mName FROM Characters JOIN Movies ON chName = {} AND mId = movieId".format(
                                character_name))