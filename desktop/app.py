import asyncio, time
import threading
from bleak import BleakClient, BleakScanner, discover
import tkinter as tk
from tkinter import messagebox, Label, StringVar, ttk, Listbox
from ttkbootstrap import Style
import datetime

# объявление переменных
client = None 
MAC_ADDRESS = ""
CHARACTERISTIC_UUID = ""
labels = []
devices = []

event_loop = asyncio.new_event_loop()

# Функция для получения доступных устройств
async def get_devices():
    devices = await BleakScanner.discover()
    return devices

# Функция для получения uuid
async def get_device_uuid(address):
    global client
    try:
        # Проверяем, подключены ли мы к устройству
        if client is None or not client.is_connected:
            is_connected = await connect_device(address)
            if not is_connected:
                return None  # Если не удалось подключиться, возвращаем None

        # Получаем характеристики устройства
        characteristics = await client.get_services()  # Обновлено для получения служб
        
        # Выводим UUID характеристик
        uuids = []
        services = await client.get_services()
        for service in services:
            for char in service.characteristics:
                uuids.append(char.uuid)
        return uuids
    except Exception as e:
        print(f"Ошибка при получении UUID: {e}")
        return None

# Функция для обновления выпадающего списка устройств
async def update_device_list(combobox):
    devices = await get_devices()
    combobox['values'] = [device.address for device in devices]  # Обновить значения комбобокса
    if devices:
        combobox.current(0)  # Выбрать первое устройство по умолчанию

# Функция для подключения к устройству
async def connect_device(address):
    global client
    client = BleakClient(address)
    
    try:
        # Подключение к устройству
        await client.connect()
        print(f"Подключено к устройству: {address}")

        # Получаем доступные сервисы
        services = await client.get_services()
        print("Доступные характеристики:")
        for service in services:
            print(f"UUID сервиса: {service.uuid}")
            for char in service.characteristics:
                print(f"  UUID характеристики: {char.uuid}")

    except Exception as e:
        print(f"Ошибка подключения: {e}")

# Функция для выбора устройства
async def select_device(device_combobox):
    global MAC_ADDRESS
    MAC_ADDRESS = device_combobox.get()  # Записать MAC адрес
    if MAC_ADDRESS:
        await connect_device(MAC_ADDRESS)  # Вызвать функцию подключения с await
        uuid_list = await get_device_uuid(MAC_ADDRESS)  # Получить UUID
        if uuid_list:
            print(uuid_list)
            open_uuid_selection_window(uuid_list)
        else:
            messagebox.showwarning("Предупреждение", "Не удалось получить UUID для выбранного устройства.")
    else:
        messagebox.showwarning("Предупреждение", "Выберите устройство из списка.")


# Функция для открытия окна выбора UUID
def open_uuid_selection_window(uuid_list):
    uuid_window = tk.Toplevel(window)  # Создание нового окна
    uuid_window.geometry("300x200")
    uuid_window.title("Выбор UUID")

    # Создание комбобокса для выбора UUID
    uuid_combobox = ttk.Combobox(uuid_window, values=uuid_list)
    uuid_combobox.pack(padx=10, pady=10)

    # Кнопка для подтверждения выбора UUID
    confirm_button = tk.Button(uuid_window, text="Подтвердить", command=lambda: confirm_uuid_selection(uuid_combobox))
    confirm_button.pack(padx=10, pady=10)

    # Установка первого UUID по умолчанию
    if uuid_list:
        uuid_combobox.current(0)

# Функция для подтверждения выбора UUID
def confirm_uuid_selection(uuid_combobox):
    global CHARACTERISTIC_UUID
    CHARACTERISTIC_UUID = uuid_combobox.get()  # Записать выбранный UUID
    messagebox.showinfo("Информация", f"Выбрано устройство: {MAC_ADDRESS}\nUUID: {CHARACTERISTIC_UUID}")
    
    # Закрыть окно выбора UUID
    uuid_combobox.master.destroy()  # Закрыть окно

#######

# Функция для отправки данных
async def send_data(data):
    if client is None or not client.is_connected:
        print("Устройство не подключено!")
        return

    try:
        await client.write_gatt_char(CHARACTERISTIC_UUID, data.encode('utf-8'), True)
        print("Данные успешно отправлены!")
    except Exception as e:
        print(f"Ошибка при отправке данных: {e}")

# ping
async def send_ping(result_var):
    global client
    try:
        if client is None or not client.is_connected:
            client = BleakClient(MAC_ADDRESS)
            await client.connect()

        if client.is_connected:
            result_var.set("Соединение установлено.")
            await client.write_gatt_char(CHARACTERISTIC_UUID, b"PING")
            response = await client.read_gatt_char(CHARACTERISTIC_UUID)
            result_var.set("Связь установлена.")
        else:
            result_var.set("Соединение не удалось.")
    except Exception as e:
        result_var.set(f"Ошибка: {e}")


# Кнопка проверки связи
def start_check():
    result_var.set("Проверка связи...")
    asyncio.run_coroutine_threadsafe(send_ping(result_var), event_loop)

# проверка соответствия даты формату
def validate(date_text):
        try:
            datetime.date.fromisoformat(date_text)
            return True
        except:
            print("Incorrect data format, should be YYYY-MM-DD")

# проверка соответствия времени формату
def valitime(time_text):
        try:
            time_text += ":00"
            datetime.time.fromisoformat(time_text)
            return True
        except:
            print("Incorrect time format, should be HH:MM")

# функция отправки сообщения
def on_send_button_click():
    d = labels[8].get()
    if not(validate(d)):
        return
    t = labels[9].get()
    if not(valitime(t)):
        return
    try:
        x, y = round(float(labels[2].get()), 3), round(float(labels[3].get()), 3)
        if not(x >= 41.2 and x <= 81.9 and y >= 27.3 and y <= 180):
            print("Wrong coordinated")
            return
        x, y = str(x), str(y)
    except:
        print("Wrong delivery coordinates format ")
        return
    data = "{" + f"ID: {labels[0].get()[:128]}, Name: {labels[1].get()[:128]}, Delivery coordinates: ({x},{y}) Fragility: {labels[4].get()[:3]}, Weight (kg): {labels[5].get()[:4]},  Height (cm): {labels[6].get()[:4]}, Width (cm): {labels[7].get()[:4]}, Delivery date: {d}, Delivery time: {t}" + "}"
    print(data)
    # Асинхронный вызов функции отправки данных
    for i in range(len(data) // 20):
        asyncio.run_coroutine_threadsafe(send_data(data[i*20:i*20+20]), event_loop)
        time.sleep(1);
    asyncio.run_coroutine_threadsafe(send_data(data[(len(data) // 20)*20:]), event_loop)

# Настройка окна Tkinter
window = tk.Tk()
window.geometry("700x550")

result_var_dev = StringVar()

# делаем всё красивым
style = Style(theme='superhero')  # Выбираем темную тему
frame = ttk.Frame(window, padding="5")
frame.pack(fill='both', expand=True)


# настройка полей

lbl1 = ttk.Label(frame, text='ID: ')
lbl1.grid(column=1, row=1, pady=5, sticky='w')
entry1 = ttk.Entry(frame)
entry1.grid(column=2, row=1, pady=5, sticky='w')

lbl2 = ttk.Label(frame, text='Name: ')
lbl2.grid(column=1, row=2, pady=5, sticky='w')
entry2 = ttk.Entry(frame)
entry2.grid(column=2, row=2, pady=5, sticky='w')

lbl3 = ttk.Label(frame, text='Delivery coordinates: ')
lbl3.grid(column=1, row=3, pady=5, sticky='w')
entry3_1 = ttk.Entry(frame)
entry3_1.grid(column=2, row=3, pady=5, sticky='w')
entry3_2 = ttk.Entry(frame)
entry3_2.grid(column=3, row=3, pady=5, sticky='w')

lbl4 = ttk.Label(frame, text='Fragility: ')
lbl4.grid(column=1, row=4, pady=5, sticky='w')
entry4 = ttk.Entry(frame)
entry4.grid(column=2, row=4, pady=5, sticky='w')

lbl5 = ttk.Label(frame, text='Weight (kg): ')
lbl5.grid(column=1, row=5, pady=5, sticky='w')
entry5 = ttk.Entry(frame)
entry5.grid(column=2, row=5, pady=5, sticky='w')

lbl6 = ttk.Label(frame, text='Height (cm): ')
lbl6.grid(column=1, row=6, pady=5, sticky='w')
entry6 = ttk.Entry(frame)
entry6.grid(column=2, row=6, pady=5, sticky='w')

lbl7 = ttk.Label(frame, text='Width (cm): ')
lbl7.grid(column=1, row=7, pady=5, sticky='w')
entry7 = ttk.Entry(frame)
entry7.grid(column=2, row=7, pady=5, sticky='w')

lbl8 = ttk.Label(frame, text='Delivery date: ')
lbl8.grid(column=1, row=8, pady=5, sticky='w')
entry8 = ttk.Entry(frame)
entry8.grid(column=2, row=8, pady=5, sticky='w')

lbl9 = ttk.Label(frame, text='Delivery time: ')
lbl9.grid(column=1, row=9, pady=5, sticky='w')
entry9 = ttk.Entry(frame)
entry9.grid(column=2, row=9, pady=5, sticky='w')

labels = [entry1, entry2, entry3_1, entry3_2, entry4, entry5, entry6, entry7, entry8, entry9]

# кнопки
send_button = ttk.Button(frame, text="Отправить", command=on_send_button_click)
send_button.grid(column=1, row=10, pady=5, sticky='w')
check_button = ttk.Button(frame, text="Проверить связь", command=start_check)
check_button.grid(column=1, row=11, pady=5, sticky='w')
result_var = StringVar()
result_var.set("Нажмите для проверки связи")
result_label = ttk.Label(frame, textvariable=result_var)
result_label.grid(column=2, row=11, columnspan=5, pady=5, sticky='w')

# Подключение
# Создание списка устройств
# Создание комбобокса для выбора устройств
device_combobox = ttk.Combobox(frame)
device_combobox.grid(column=1, row=12, columnspan=2, pady=5, sticky='w')

# Кнопка для обновления списка устройств
update_button = tk.Button(frame, text="Обновить устройства", command=lambda: asyncio.run_coroutine_threadsafe(update_device_list(device_combobox), event_loop))
update_button.grid(column=3, row=12, pady=5, sticky='w')

# Кнопка для выбора устройства
select_button = tk.Button(frame, text="Выбрать устройство", command=lambda: asyncio.run_coroutine_threadsafe(select_device(device_combobox), event_loop))
select_button.grid(column=4, row=12, pady=5, sticky='w')

# Начальное обновление списка устройств
def run_loop():
    event_loop.run_forever()

# запуск
window.title('Начальная настройка маячка')
threading.Thread(target=run_loop, daemon=True).start()
window.mainloop()