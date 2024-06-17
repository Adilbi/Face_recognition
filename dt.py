import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Выполнение запроса для выборки всех пользователей и их логинов
c.execute("SELECT username, password FROM users")

# Получение результатов запроса
rows = c.fetchall()

# Вывод результатов на экран
for row in rows:
    print("Username:", row[0])
    print("Password:", row[1])
    print("")

# Закрытие соединения с базой данных
conn.close()

