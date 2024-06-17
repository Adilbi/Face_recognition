import os
import sqlite3
import cv2
import face_recognition
import numpy as np
from tkinter import *
from tkinter import simpledialog, messagebox
from tkinter import ttk
from datetime import datetime

# Путь к папке с изображениями для распознавания лиц
path = 'C:\\FACE-RECOGNITION-AND-ATTENDENCE-main\\ImagesAttendance'
images = []  # Список для хранения изображений
classNames = {}  # Словарь для хранения имен пользователей
userIds = {}  # Словарь для хранения ID пользователей
myList = os.listdir(path)  # Получаем список файлов в директории
print(myList)

# Подключение к базе данных и создание таблицы пользователей
conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, 
        username TEXT, 
        password TEXT
    )
''')
conn.commit()

# Загрузка изображений и имен из директории
for cl in myList:
    curImg = cv2.imread(f'{path}/{cl}')  # Чтение изображения
    images.append(curImg)  # Добавление изображения в список
    name = os.path.splitext(cl)[0].lower()  # Получение имени файла без расширения
    userId = str(len(classNames) + 1).zfill(5)  # Создание уникального ID пользователя
    classNames[name] = userId  # Сохранение ID в словарь по имени
    userIds[userId] = name  # Сохранение имени в словарь по ID
print(classNames)

# Функция для нахождения кодировок лиц в списке изображений
def findEncodings(images):
    encodeList = []
    for idx, img in enumerate(images):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Конвертация изображения в RGB
        encodes = face_recognition.face_encodings(img)  # Кодирование лица
        if encodes:
            encode = encodes[0]  # Получение первого кодирования
            encodeList.append(encode)  # Добавление кодирования в список
        else:
            print(f"No faces found in image {myList[idx]}")
    return encodeList

encodeListKnown = findEncodings(images)  # Получение кодировок для всех изображений
print('Encoding Complete')

# Функция для отметки присутствия
def markAttendance(name):
    with open('Att.csv', 'r+') as f:
        myDataList = f.readlines()  # Чтение всех строк файла
        nameList = [entry.split(',')[0] for entry in myDataList]  # Создание списка имен из файла
        if name not in nameList:
            now = datetime.now()  # Получение текущего времени
            dtString = now.strftime('%H:%M:%S')  # Форматирование времени
            f.writelines(f'\n{name},{dtString}')  # Запись имени и времени в файл

# Функция для регистрации нового пользователя
def registerUser(name, img, password):
    userId = str(len(classNames) + 1).zfill(5)  # Создание уникального ID пользователя
    classNames[name.lower()] = userId  # Сохранение ID в словарь по имени
    userIds[userId] = name.lower()  # Сохранение имени в словарь по ID
    cv2.imwrite(f'{path}/{name}.jpg', img)  # Сохранение изображения пользователя
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Конвертация изображения в RGB
    encodes = face_recognition.face_encodings(img_rgb)  # Кодирование лица
    if encodes:
        encodeListKnown.append(encodes[0])  # Добавление кодирования в список
    else:
        print(f"No faces found for {name}")
        return
    with conn:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (name.lower(), password))  # Добавление пользователя в базу данных
    print(f"User {name} registered successfully!")

# Функция для запуска регистрации нового пользователя
def startUserRegistration():
    cap = cv2.VideoCapture(0)  # Открытие видеопотока с веб-камеры
    while True:
        success, img = cap.read()  # Захват изображения с веб-камеры
        cv2.imshow('Register User', img)  # Отображение изображения в окне
        b = cv2.waitKey(1)  # Ожидание нажатия клавиши
        if b == 32:  # Если нажата пробел
            name = simpledialog.askstring("Input", "Enter your name:")  # Запрос имени пользователя
            password = simpledialog.askstring("Input", "Enter your password:", show='*')  # Запрос пароля
            if name and password:
                registerUser(name, img, password)  # Регистрация пользователя
                print(f"User {name} registered successfully!")
            break
        elif b == 31 or b == 113:  # Если нажаты клавиши Esc или q
            print("User registration cancelled")
            break
    cap.release()  # Освобождение видеопотока
    cv2.destroyAllWindows()  # Закрытие всех окон OpenCV

# Функция для входа пользователя
def login():
    username = simpledialog.askstring("Login", "Enter your username:")  # Запрос имени пользователя
    password = simpledialog.askstring("Password", "Enter your password:", show='*')  # Запрос пароля
    with conn:
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username.lower(), password))  # Проверка пользователя в базе данных
        user = c.fetchone()  # Получение записи пользователя
    if user:
        print(f"Welcome {username}!")
        startFaceRecognition()  # Запуск распознавания лиц
    else:
        print("Invalid username or password")
        messagebox.showerror("Error", "Invalid username or password")

# Функция для запуска распознавания лиц
def startFaceRecognition():
    cap = cv2.VideoCapture(0)  # Открытие видеопотока с веб-камеры
    while True:
        success, img = cap.read()  # Захват изображения с веб-камеры
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Изменение размера изображения
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)  # Конвертация изображения в RGB
        facesCurFrame = face_recognition.face_locations(imgS)  # Обнаружение лиц в текущем кадре
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)  # Кодирование лиц в текущем кадре

        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)  # Сравнение лиц с известными кодировками
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)  # Расчет расстояний до известных лиц
            matchIndex = np.argmin(faceDis)  # Поиск наименьшего расстояния

            if matches[matchIndex]:  # Если найдено совпадение
                name = list(classNames.keys())[matchIndex]  # Получение имени пользователя
                userId = classNames.get(name.lower(), "00000")  # Получение ID пользователя
                label = f'{name.upper()} ({userId})'  # Формирование метки для отображения
                color = (0, 255, 0)  # Зеленый цвет для рамки
                text = "correct"
                markAttendance(name)  # Отметка присутствия
            else:
                name = "unknown"  # Если лицо не распознано
                label = name
                userId = "00000"
                color = (0, 0, 255)  # Красный цвет для рамки
                text = "incorrect"

            y1, x2, y2, x1 = faceLoc  # Координаты лица
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # Масштабирование координат до исходного размера изображения

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)  # Отрисовка рамки вокруг лица
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)  # Отрисовка подложки для текста
            cv2.putText(img, label, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)  # Отображение метки
            cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)  # Отображение текста

        cv2.imshow('Webcam', img)  # Отображение изображения в окне
        b = cv2.waitKey(1)  # Ожидание нажатия клавиши
        if b == 31 or b == 113:  # Если нажаты клавиши Esc или q
            print("End Face Detection")
            break
    cap.release()  # Освобождение видеопотока
    cv2.destroyAllWindows()  # Закрытие всех окон OpenCV

# Функция для просмотра всех пользователей
def viewUsers():
    with conn:
        c.execute("SELECT username FROM users")  # Запрос всех пользователей из базы данных
        users = c.fetchall()  # Получение списка пользователей
    for user in users:
        print(f"Username: {user[0]}")

# Функция для удаления пользователя
def deleteUser():
    username = simpledialog.askstring("Delete User", "Enter the username of the user to delete:")  # Запрос имени пользователя
    with conn:
        c.execute("DELETE FROM users WHERE username=?", (username.lower(),))  # Удаление пользователя из базы данных
        conn.commit()
    print(f"User {username} deleted successfully!")
    # Удаление изображения пользователя
    img_path = f'{path}/{username.lower()}.jpg'
    if os.path.exists(img_path):
        os.remove(img_path)  # Удаление изображения пользователя
        print(f"Image for user {username} deleted successfully!")
    else:
        print(f"No image found for user {username}")

# Функция для сброса пароля
def resetPassword():
    username = simpledialog.askstring("Reset Password", "Enter your username:")  # Запрос имени пользователя
    new_password = simpledialog.askstring("Reset Password", "Enter your new password:", show='*')  # Запрос нового пароля
    with conn:
        c.execute("UPDATE users SET password=? WHERE username=?", (new_password, username.lower()))  # Обновление пароля в базе данных
        conn.commit()
    print(f"Password for user {username} reset successfully!")

# Создание графического интерфейса
root = Tk()  # Создание главного окна
root.title("Face Recognition System")  # Установка заголовка окна

# Настройка стилей
style = ttk.Style()
style.configure('TFrame', background='#e0f7fa')
style.configure('TButton', font=('Helvetica', 14), padding=10)
style.configure('TLabel', font=('Helvetica', 16), background='#e0f7fa')

frame = ttk.Frame(root, padding=20, style='TFrame')  # Создание рамки для элементов интерфейса
frame.pack(fill=BOTH, expand=True)

label = ttk.Label(frame, text="Face Recognition System", style='TLabel')  # Создание метки с заголовком
label.pack(pady=20)

loginButton = ttk.Button(frame, text="Логин", command=login, style='TButton')  # Кнопка для входа
loginButton.pack(pady=10)

registerButton = ttk.Button(frame, text="Зарегистрировать нового пользователя", command=startUserRegistration, style='TButton')  # Кнопка для регистрации нового пользователя
registerButton.pack(pady=10)

viewUsersButton = ttk.Button(frame, text="Все пользователи", command=viewUsers, style='TButton')  # Кнопка для просмотра всех пользователей
viewUsersButton.pack(pady=10)

deleteUserButton = ttk.Button(frame, text="Удалить пользователя", command=deleteUser, style='TButton')  # Кнопка для удаления пользователя
deleteUserButton.pack(pady=10)

resetPasswordButton = ttk.Button(frame, text="Сбросить пароль", command=resetPassword, style='TButton')  # Кнопка для сброса пароля
resetPasswordButton.pack(pady=10)

root.geometry('400x600')  # Установка размера окна
root.mainloop()  # Запуск главного цикла обработки событий






































