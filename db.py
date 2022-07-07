import psycopg2

class BotDB:
    def __init__(self, dbname, user, password,host,port):
        self.conn = psycopg2.connect(dbname=dbname,user=user,password=password,host=host,port=port)
        self.cursor = self.conn.cursor()

    def check_exist_user(self,id):
        self.cursor.execute(f"SELECT user_id FROM users WHERE user_id = {id}")
        return bool(len(self.cursor.fetchall()))

    def update_lastvisit(self,id,date):
        try:
            self.cursor.execute("UPDATE users SET lastvisit = %s WHERE user_id = %s ",(date,id))
            self.conn.commit()
        except: return "[PostgreSQL error]"

    def add_user(self,user_id,date):
        try:
            if (self.check_exist_user(user_id) == False):
                self.cursor.execute("INSERT INTO users (user_id, join_date,lastvisit) VALUES (%s,%s,%s)",(user_id,date,date))
            self.conn.commit()
        except: return "[PostgreSQL error]"

    def user_exists(self, user_id):
        self.cursor.execute(f"SELECT user_id FROM mailings WHERE user_id = {user_id}")
        return bool(len(self.cursor.fetchall()))

    def add_record(self, user_id, place,date):
        try:
            if (self.user_exists(user_id) == False):
                self.cursor.execute("INSERT INTO mailings (user_id, place,connect_date) VALUES (%s, %s,%s)",(user_id,place,date))
            else:
                self.cursor.execute("UPDATE mailings SET place = %s WHERE user_id = %s ",(place,user_id))
            self.conn.commit()
        except: return "[PostgreSQL error]"

    def get_records(self):
        self.cursor.execute("SELECT * FROM mailings")
        return self.cursor.fetchall()

    def get_record(self,user_id):
        self.cursor.execute(f"SELECT place FROM mailings WHERE user_id = {user_id}")
        return self.cursor.fetchall()

    def detete_record(self,user_id):
        self.cursor.execute("DELETE FROM mailings WHERE user_id = %s",(user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()



'''
print(BotDB.add_record(1239532162,'Tyumen'))
print(BotDB.detete_record(1239532162))
print(BotDB.get_records())

recs = BotDB.get_records()
for i in recs:
    print(f'Id {i[0]} Place {i[1]}')

print(BotDB.user_exists(id))
'''