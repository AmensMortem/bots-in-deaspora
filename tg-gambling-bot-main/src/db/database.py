import sqlite3
import os


class DataBase:
    def __init__(self):
        self.db = sqlite3.connect("gambling_base_main.db", check_same_thread=False)
        self.cur = self.db.cursor()

    def append_lottery(self, draw_text, date, num_winners, participant_number, name, creator, subscriptions):
        try:
            self.cur.execute(
                """INSERT INTO draw(draw_text, date, participant_number, creator_id, draw_name, subscriptions, winners) 
                VALUES (?,?,?,?,?,?,?)""",
                (draw_text, date, participant_number, creator, name, subscriptions, num_winners))

            self.db.commit()
            return 'Lottery created successfully!'
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def append_participant(self, tg_id, draw_name):
        try:
            draw_id = self.cur.execute("""SELECT draw_id FROM draw WHERE draw_name = ?""", (draw_name,)).fetchone()
            self.cur.execute("""INSERT OR IGNORE INTO user(tg_id) VALUES (?)""", (tg_id,))
            self.cur.execute("""INSERT INTO user_to_draw(draw_id, user_id) VALUES(?,?)""",
                             (draw_id[0], tg_id))
            self.db.commit()
            return 'Вы участник!'
        except sqlite3.Error as e:
            return f'Database error: {e}'

    def view_draw(self, user_id=None, draw_name=None, check_channels=None, participant_number=None):
        try:
            if participant_number is not None:
                participant_number_bd = self.cur.execute("""SELECT participant_number FROM draw WHERE draw_name = ?""",
                                                         (draw_name,)).fetchone()
                return participant_number_bd[0]
            if check_channels is not None:
                subscriptions = self.cur.execute("""SELECT subscriptions FROM draw WHERE draw_name = ?""",
                                                 (draw_name,)).fetchone()
                return subscriptions
            if user_id is not None:
                draws = self.cur.execute("""SELECT draw_name FROM draw WHERE creator_id = ?""", (user_id,)).fetchall()
                return draws
            if draw_name is not None:
                text = self.cur.execute("""SELECT draw_text FROM draw WHERE draw_name = ?""", (draw_name,)).fetchone()
                return text
        except Exception as e:
            return f"Error {e}"

    def view_participants(self, draw_name):
        draw_id = self.cur.execute("""SELECT draw_id FROM draw WHERE draw_name = ?""", (draw_name,)).fetchone()
        if draw_id is None:
            return 'ended'
        else:
            participants = self.cur.execute("""SELECT user_id FROM user_to_draw WHERE draw_id = ?""",
                                            (draw_id[0],)).fetchall()
            return [p[0] for p in participants]

    def delete_draw(self, draw_name):
        try:
            draw_id = self.cur.execute("""SELECT draw_id FROM draw WHERE draw_name = ?""", (draw_name,)).fetchone()
            if not draw_id:
                return
            draw_id = draw_id[0]
            self.cur.execute("""DELETE FROM user_to_draw WHERE draw_id = ?""", (draw_id,))
            self.cur.execute("""DELETE FROM draw WHERE draw_id = ?""", (draw_id,))
            self.db.commit()
        except sqlite3.Error as e:
            return f"Database error during deletion: {e}"

    def view_dates(self):
        dates_db = self.cur.execute("""SELECT date FROM draw""").fetchall()
        dates = []
        for i in dates_db:
            dates.append(i[0])
        return dates.sort()


def create_database(db_name="./gambling_base_main.db"):
    try:
        if os.path.exists(db_name):
            os.remove(db_name)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS draw (
                draw_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                participant_number INTEGER,
                draw_text TEXT,
                creator_id INTEGER NOT NULL,
                draw_name TEXT NOT NULL,
                subscriptions TEXT,
                winners INTEGER NOT NULL,
                FOREIGN KEY (creator_id) REFERENCES user(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_to_draw (
                draw_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (draw_id) REFERENCES draw(draw_id),
                FOREIGN KEY (user_id) REFERENCES user(id),
                PRIMARY KEY (draw_id, user_id)
            )
        ''')

        conn.commit()
        conn.close()
        return 'success'
    except Exception as e:
        return e
