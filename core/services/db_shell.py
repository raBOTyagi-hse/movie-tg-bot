import datetime
import mysql.connector

__author__ = 'NickVeld'


class DBShell:
    def __init__(self):
        self.db = None
        self.INACT_M = 5


    def get_from_config(self, cfg):
        self.connection = (mysql.connector.connect(
            host=cfg["db_settings"]["host"],
            port=cfg["db_settings"]["port"],
            user=cfg["db_settings"]["user"],
            passwd=cfg["db_settings"]["passwd"],
            database=cfg["db_settings"]["db_name"],
            autocommit=True
        ) if cfg['db_settings']['is_enabled'] == 'True' else None)

        if not self.connection is None:
            self.db = self.connection.cursor()

        self.INACT_M = int(cfg["user_inactivity_time_at_minutes"])

    def is_in_blacklist(self, pers_id):
        return False

    def initialize_user(self, pers_id):
        self.db.execute("INSERT INTO Users VALUES ({}, {})".format(pers_id, datetime.datetime.min))

    def update_last_activity(self, pers_id, after_quit):
        if not self.db is None:
            self.db.execute("UPDATE Users SET uLast_activity = {} WHERE uId = {};".format(
                                datetime.datetime.min if after_quit else datetime.datetime.utcnow(), pers_id))


    def get_ready_for_autoquit(self):
        self.db.execute("SELECT uId FROM Users WHERE uLast_activity > {} AND uLast_activity < {};".format(
                         datetime.datetime.min, datetime.datetime.utcnow() - datetime.timedelta(minutes=(self.INACT_M-1))))
        return list(map(lambda x: x[0], self.db))

    def get_movies_of_character(self, character_name):
        self.db.execute("SELECT mTitle FROM Characters JOIN Movies ON chName = '{}' AND mId = movieId;".format(
                         character_name))
        return list(map(lambda x: x[0], self.db))

    def get_characters_of_movie(self, movie):
        request = "SELECT DISTINCT chName FROM Characters "
        if isinstance(movie, int):
            request += "WHERE movieId = " + str(movie) + ";"
        else:
            request += "JOIN Movies ON mTitle = '{}' AND mId = movieId;".format(movie)
        self.db.execute(request)
        return list(map(lambda x: x[0], self.db))

    def get_most_searched_films(self):
        self.db.execute('''SELECT M.mTitle, COUNT(Q.movie_usedId)
FROM Movies AS M
JOIN Queries AS Q ON M.mId = Q.movie_usedId
GROUP BY M.mTitle, Q.movie_usedId
ORDER BY COUNT(Q.movie_usedId); ''')
        return list(self.db)


