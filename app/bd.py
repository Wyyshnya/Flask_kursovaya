import os
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Data:
    def __init__(self):
        try:
            self.conn = psycopg2.connect('postgres://wyshnya:1337@localhost:5432/kursach')
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)

    def filter_auth(self, username):
        self.cursor.execute('SELECT id FROM users where username LIKE %s', (username,))
        return self.cursor.fetchone()

    def filter_email(self, username):
        self.cursor.execute('SELECT email FROM users where email LIKE %s', (username,))
        return self.cursor.fetchone()

    def __exit__(self):
        if self.conn:
            self.cursor.close()
            self.conn.close()
            print("Соединение с PostgreSQL закрыто")

    def create_users(self):

        from werkzeug.security import generate_password_hash
        passwd = generate_password_hash('admin')
        self.cursor.execute("CREATE TABLE users (id serial PRIMARY KEY, "
                            "username VARCHAR(255) unique, password VARCHAR(255), email VARCHAR(255) unique,"
                            "last_seen timestamp, about_me TEXT);")
        self.cursor.execute("Insert into users (username, password, email) VALUES (%s, %s, %s)",
                            ('admin', passwd, 'jija'))
        self.conn.commit()

    def create_roles(self):
        self.cursor.execute("CREATE TABLE roles (id serial PRIMARY KEY, "
                            "title varchar(255));")
        self.cursor.execute("Insert into roles (title) VALUES ('admin')")
        self.cursor.execute("Insert into roles (title) VALUES ('expert')")
        self.cursor.execute("Insert into roles (title) VALUES ('default')")
        self.conn.commit()

    def create_users_roles(self):
        self.cursor.execute("CREATE TABLE users_roles (user_id int REFERENCES users(id), "
                            "role_id int REFERENCES roles(id), "
                            "PRIMARY KEY(user_id, role_id));")
        self.conn.commit()

    def create_category(self):
        self.cursor.execute("CREATE TABLE category (id serial Primary Key, "
                            "title VARCHAR(255));")
        self.cursor.execute("Insert into category (title) VALUES ('Телефоны')")
        self.cursor.execute("Insert into category (title) VALUES ('Пылесосы')")
        self.conn.commit()

    def create_models(self):
        self.cursor.execute("CREATE TABLE models (id serial Primary Key, "
                            "title VARCHAR(255), category_id int REFERENCES category(id));")
        self.conn.commit()

    def create_video(self):
        self.cursor.execute("CREATE TABLE video (id serial Primary Key, video_path TEXT, description TEXT,"
                            "title VARCHAR(255), author_id int REFERENCES users(id), rating real, "
                            "models int REFERENCES models(id));")
        self.conn.commit()

    def create_rating(self):
        self.cursor.execute("CREATE TABLE rating (user_id int REFERENCES users(id), "
                            "content_id int REFERENCES video(id), "
                            "rate int, PRIMARY KEY (user_id, content_id));")
        self.conn.commit()

    def create_comments(self):
        self.cursor.execute("CREATE TABLE comment (id serial Primary Key, "
                            "video_id int REFERENCES video(id), user_id int REFERENCES users(id),"
                            "content TEXT, reply_to int REFERENCES comment(id));")
        self.conn.commit()

    def create_helpers(self):
        self.cursor.execute("CREATE TABLE helpers (id serial Primary Key, "
                            "message TEXT, user_id int REFERENCES users(id), expert_id int REFERENCES users(id),"
                            "when_sent timestamp);")
        self.conn.commit()

    def create_wanaexp(self):
        self.cursor.execute("CREATE TABLE wanaexp (id serial Primary Key, "
                            "user_id int REFERENCES users(id), email text, phone text, about text, agree boolean,"
                            "date_sent timestamp);")
        self.conn.commit()

    def drop_users_roles(self):
        self.cursor.execute("DROP TABLE users_roles;")
        self.conn.commit()

    def drop_roles(self):
        self.cursor.execute("DROP TABLE roles;")
        self.conn.commit()

    def drop_users(self):
        self.cursor.execute("DROP TABLE users;")
        self.conn.commit()

    def drop_category(self):
        self.cursor.execute("DROP TABLE category;")
        self.conn.commit()

    def drop_models(self):
        self.cursor.execute("DROP TABLE models;")
        self.conn.commit()

    def drop_video(self):
        self.cursor.execute("DROP TABLE video;")
        self.conn.commit()

    def drop_rating(self):
        self.cursor.execute("DROP TABLE rating")
        self.conn.commit()

    def drop_comments(self):
        self.cursor.execute("DROP TABLE comment")
        self.conn.commit()

    def drop_helpers(self):
        self.cursor.execute("DROP TABLE helpers")
        self.conn.commit()

    def drop_wanaexp(self):
        self.cursor.execute("DROP TABLE wanaexp;")
        self.conn.commit()

    def trigger_rating(self):
        self.cursor.execute('''CREATE OR REPLACE FUNCTION f_update_rate() RETURNS TRIGGER AS $$
                            BEGIN
                            UPDATE video
                            SET rating=(SELECT AVG(rate) FROM rating where content_id=NEW.content_id)
                            WHERE id = NEW.content_id;
                            REturn NUll;
                            END
                            $$ LANGUAGE 'plpgsql';

                            CREATE TRIGGER t_update_rate AFTER UPDATE or INSERT
                            on rating
                            FOR EACH ROW EXECUTE PROCEDURE f_update_rate();''')
        # self.cursor.execute('DROP trigger t_update_rate on rating;')
        self.conn.commit()


a = Data()
# a.trigger_rating()
# a.drop_comments()
# a.drop_rating()
# a.drop_video()
# a.drop_models()
# a.drop_category()
# a.drop_users_roles()
# a.drop_helpers()
# a.drop_users()
# a.drop_roles()

# a.cursor.execute("insert into users_roles (user_id, role_id) values (2, 3);")

# a.create_users()
# a.create_roles()
# a.create_users_roles()
# a.create_helpers()
# a.create_category()
# a.create_models()
# a.create_video()
# a.create_rating()
# a.create_comments()
