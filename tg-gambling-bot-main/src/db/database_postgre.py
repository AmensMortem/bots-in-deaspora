import psycopg2
from os import environ

DB_HOST = environ["DB_HOST"]
DB_NAME = environ["DB_NAME"]
DB_USER = environ["DB_USER"]
DB_PASSWORD = environ["DB_PASSWORD"]
DB_PORT = environ["DB_PORT"]


class DataBase:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        self.conn.set_client_encoding('UTF8')
        self.cur = self.conn.cursor()

    def db_connect(self):
        return self.conn

    def append_lottery(self, draw_text, date, num_winners, participant_number, name, creator_tg_id, subscriptions):
        try:
            self.cur.execute("INSERT INTO user_table(tg_id) VALUES (%s) ON CONFLICT (tg_id) DO NOTHING",
                             (creator_tg_id,))
            self.conn.commit()
            self.cur.execute("SELECT id FROM user_table WHERE tg_id = %s", (creator_tg_id,))
            table_id = self.cur.fetchone()

            if table_id:
                creator_id = table_id[0]
                self.cur.execute(
                    """INSERT INTO draw(draw_text, date, participant_number, creator_id, draw_name, subscriptions, winners) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (draw_text, date, participant_number, creator_id, name, subscriptions, num_winners)
                )
                self.conn.commit()
                self.cur.execute("SELECT draw_text FROM draw WHERE creator_id = %s", (creator_id,))
                return 'Lottery created successfully!'
            else:
                return 'Creator not found after insert!'
        except psycopg2.Error as e:
            return f'Database error: {e}'

    def append_participant(self, tg_id, draw_name):
        try:
            self.cur.execute("SELECT draw_id FROM draw WHERE draw_name = %s", (draw_name,))
            draw_id_result = self.cur.fetchone()
            if not draw_id_result:
                return 'Draw not found.'
            draw_id = draw_id_result[0]
            self.cur.execute("INSERT INTO user_table(tg_id) VALUES (%s) ON CONFLICT (tg_id) DO NOTHING", (tg_id,))
            self.cur.execute("SELECT id FROM user_table WHERE tg_id = %s", (tg_id,))
            user_id = self.cur.fetchone()
            if not user_id:
                return 'User not found.'
            user_id = user_id[0]
            self.cur.execute("SELECT 1 FROM user_to_draw WHERE draw_id = %s AND user_id = %s", (draw_id, user_id))
            already_participant = self.cur.fetchone()
            if already_participant:
                return 'Вы уже участвуете в этом розыгрыше!'
            self.cur.execute("INSERT INTO user_to_draw(draw_id, user_id) VALUES(%s, %s)", (draw_id, user_id))
            self.conn.commit()
            return 'Вы успешно присоединились к розыгрышу!'
        except psycopg2.Error as e:
            return f'Database error: {e}'

    def view_draw(self, creator_tg_id=None, draw_name=None, check_channels=False, participant_number=False,
                  num_winners=False):
        try:
            if participant_number:
                self.cur.execute("SELECT participant_number FROM draw WHERE draw_name = %s", (draw_name,))
                participant_number_bd = self.cur.fetchone()
                return participant_number_bd[0]
            if num_winners:
                self.cur.execute("SELECT winners FROM draw WHERE draw_name = %s", (draw_name,))
                winners = self.cur.fetchone()
                if winners:
                    return winners[0]
                else:
                    return 1

            if check_channels:
                self.cur.execute("SELECT subscriptions FROM draw WHERE draw_name = %s", (draw_name,))
                subscriptions = self.cur.fetchone()
                if subscriptions:
                    return subscriptions
                return None

            if creator_tg_id is not None:
                self.cur.execute("INSERT INTO user_table(tg_id) VALUES (%s) ON CONFLICT (tg_id) DO NOTHING",
                                 (creator_tg_id,))
                self.conn.commit()
                self.cur.execute("SELECT id FROM user_table WHERE tg_id = %s", (creator_tg_id,))
                table_id = self.cur.fetchone()
                self.cur.execute("SELECT draw_name FROM draw WHERE creator_id = %s", (table_id,))
                draws = self.cur.fetchall()
                return draws

            if draw_name is not None:
                self.cur.execute("SELECT draw_text FROM draw WHERE draw_name = %s", (draw_name,))
                text = self.cur.fetchone()
                return text
        except psycopg2.Error as e:
            return f"Error {e}"

    def view_participants(self, draw_name=None, user_id=None, get_tg=False):
        try:
            if get_tg:
                self.cur.execute("SELECT tg_id FROM user_table WHERE id = %s", (user_id,))
                return self.cur.fetchone()

            else:
                self.cur.execute("SELECT draw_id FROM draw WHERE draw_name = %s", (draw_name,))
                draw_id = self.cur.fetchone()
                if draw_id is None:
                    return 'ended'
                else:
                    self.cur.execute("SELECT user_id FROM user_to_draw WHERE draw_id = %s", (draw_id[0],))
                    participants = self.cur.fetchall()
                    return [p[0] for p in participants]
        except Exception as e:
            return f'{e}'

    def delete_draw(self, draw_name):
        try:
            self.cur.execute("SELECT draw_id FROM draw WHERE draw_name = %s", (draw_name,))
            draw_id = self.cur.fetchone()

            if not draw_id:
                return 'Draw not found'

            draw_id = draw_id[0]
            self.cur.execute("DELETE FROM user_to_draw WHERE draw_id = %s", (draw_id,))
            self.cur.execute("DELETE FROM draw WHERE draw_id = %s", (draw_id,))
            self.conn.commit()
        except psycopg2.Error as e:
            return f"Database error during deletion: {e}"

    def view_dates(self):
        self.cur.execute("SELECT date FROM draw")
        dates_db = self.cur.fetchall()
        dates = [i[0] for i in dates_db]
        return sorted(dates)

    def inspect_draw(self, draw_name):
        try:
            inspect_text = f'Название: {(str(draw_name).split("_"))[0]}\n'
            self.cur.execute("SELECT draw_text FROM draw WHERE draw_name = %s", (draw_name,))
            result = self.cur.fetchone()
            inspect_text += 'Описание: ' + (str(result[0]) if result else 'нет данных') + '\n'
            self.cur.execute("SELECT winners FROM draw WHERE draw_name = %s", (draw_name,))
            result = self.cur.fetchone()
            inspect_text += 'Кол-во победителей: ' + (str(result[0]) if result else 'нет данных') + '\n'
            self.cur.execute("SELECT subscriptions FROM draw WHERE draw_name = %s", (draw_name,))
            result = self.cur.fetchone()
            inspect_text += 'Обязательные подписки: ' + (str(result[0]) if result and result[0] else 'нет') + '\n'
            self.cur.execute("SELECT date FROM draw WHERE draw_name = %s", (draw_name,))
            date_result = self.cur.fetchone()
            if date_result and date_result[0] is not None:
                inspect_text += 'Дата окончания: ' + date_result[0] + '\n'
            else:
                participants = self.view_participants(draw_name)
                if participants == 'ended':
                    inspect_text += 'Конкурс уже закончился\n'
                else:
                    self.cur.execute("SELECT participant_number FROM draw WHERE draw_name = %s", (draw_name,))
                    result = self.cur.fetchone()
                    participant_limit = result[0] if result else '?'
                    inspect_text += f'Участники: {len(participants)}/{participant_limit}\n'

            return inspect_text
        except Exception as e:
            return f'Ex: {e}'

    def edit_draw(self, draw_name, new_text=None, new_date=None, new_num_participants=None, new_num_winners=None,
                  new_sub=None):
        try:
            if new_text is not None:
                self.cur.execute("""UPDATE draw SET draw_text = %s WHERE draw_name = %s;""", (new_text, draw_name))
            if new_date is not None:
                self.cur.execute("""UPDATE draw SET date = %s WHERE draw_name = %s;""", (new_date, draw_name))
            if new_num_participants is not None:
                self.cur.execute("""UPDATE draw SET participant_number = %s WHERE draw_name = %s;""",
                                 (new_num_participants, draw_name))
            if new_num_winners is not None:
                self.cur.execute("""UPDATE draw SET winners = %s WHERE draw_name = %s;""", (new_num_winners, draw_name))
            if new_sub is not None:
                self.cur.execute("""UPDATE draw SET subscriptions = %s WHERE draw_name = %s;""", (new_sub, draw_name))
            self.conn.commit()
            return 'Успех'
        except Exception as e:
            return f'Error db: {e}'

    def check(self):
        try:
            self.cur.execute("SELECT * FROM user_table;")
            return str(self.cur.fetchall())
        except psycopg2.Error as e:
            return e


def create_database():
    conn = DataBase().db_connect()
    conn.set_client_encoding('UTF8')
    cursor = conn.cursor()
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_table (
                id SERIAL PRIMARY KEY,
                tg_id BIGINT UNIQUE NOT NULL
            )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS draw (
                draw_id SERIAL PRIMARY KEY,
                date TEXT,
                participant_number INTEGER,
                draw_text TEXT,
                creator_id INTEGER NOT NULL,
                draw_name TEXT NOT NULL,
                subscriptions TEXT,
                winners INTEGER NOT NULL,
                FOREIGN KEY (creator_id) REFERENCES user_table(id) ON DELETE CASCADE
            )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_to_draw (
                draw_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (draw_id) REFERENCES draw(draw_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES user_table(id) ON DELETE CASCADE,
                PRIMARY KEY (draw_id, user_id)
            )
        ''')

    conn.commit()
    cursor.close()
    conn.close()
    return "success"
