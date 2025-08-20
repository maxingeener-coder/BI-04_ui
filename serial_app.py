import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
from threading import Thread
import time

class SerialApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление стендом БИ04 через COM-порт")
        self.root.geometry("800x500")
        
        self.serial_port = None
        self.is_connected = False
        
        self.create_widgets()
        self.refresh_ports()
        
    def create_widgets(self):
        # Основной фрейм для разделения на левую и правую части
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Левая часть - управление
        left_frame = ttk.Frame(main_frame, padding="5")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Правая часть - справка
        right_frame = ttk.Frame(main_frame, padding="5")
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Левая часть: управление COM-портом
        port_frame = ttk.Frame(left_frame, padding="10")
        port_frame.grid(row=0, column=0, sticky="ew", pady=5)
        
        ttk.Label(port_frame, text="COM-порт:").grid(row=0, column=0, sticky="w")
        
        self.port_var = tk.StringVar()
        self.port_combobox = ttk.Combobox(port_frame, textvariable=self.port_var, width=15)
        self.port_combobox.grid(row=0, column=1, padx=5)
        
        self.refresh_btn = ttk.Button(port_frame, text="Обновить", command=self.refresh_ports)
        self.refresh_btn.grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(port_frame, text="Подключиться", 
                                    command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        # Фрейм для выбора параметров
        params_frame = ttk.Frame(left_frame, padding="10")
        params_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Label(params_frame, text="Тип сигнала:").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(params_frame, text="Номер пина:").grid(row=0, column=1, sticky="w", padx=5)
        
        self.signal_var = tk.StringVar()
        self.signal_combobox = ttk.Combobox(params_frame, textvariable=self.signal_var, 
                                          values=["PLS", "IPR", "CLS"], width=10)
        self.signal_combobox.grid(row=1, column=0, padx=5, pady=5)
        self.signal_combobox.current(0)
        
        self.pin_var = tk.StringVar()
        self.pin_combobox = ttk.Combobox(params_frame, textvariable=self.pin_var, 
                                       values=["1", "2", "3"], width=10)
        self.pin_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.pin_combobox.current(0)
        
        # Фрейм для кнопок
        buttons_frame = ttk.Frame(left_frame, padding="10")
        buttons_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        self.clear_btn = ttk.Button(buttons_frame, text="Очистить", 
                                  command=self.send_clear, state="disabled")
        self.clear_btn.grid(row=0, column=0, padx=5)
        
        self.send_btn = ttk.Button(buttons_frame, text="Отправить", 
                                 command=self.send_command, state="disabled")
        self.send_btn.grid(row=0, column=1, padx=5)
        
        # Лог
        log_frame = ttk.Frame(left_frame, padding="10")
        log_frame.grid(row=3, column=0, sticky="nsew", pady=5)
        
        ttk.Label(log_frame, text="Лог сообщений:").grid(row=0, column=0, sticky="w")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=15, state="disabled")
        self.log_text.grid(row=1, column=0, pady=5)
        
        # Настройка весов для левой части
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(3, weight=1)
        
        # Правая часть: справка
        help_frame = ttk.LabelFrame(right_frame, text="Справка", padding="10")
        help_frame.grid(row=0, column=0, sticky="nsew")
        
        help_text = """
В выпадающих списках можно выбрать 
конфигурацию пина и вида сигнала.
PLS = ПЛС
IPR = НАГРУЗКА
CLS = КЗ

Кнопка "очистить" обнуляет ВСЕ выходы.
Кнопка "отправить" коммутирует определенный 
сигнал на определенный номер пинов

Определенный вид сигнала можно 
скоммутировать только на 1 пин. 
Нельзя скоммутировать PLS на 2 и 3 
пины одновременно.

При проверке каскадов, пожалуйста 
проверяй и выводы сдвигового 
регистра. Я мог ошибиться тоже.
        """
        
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, 
                             font=("Arial", 9), wraplength=200)
        help_label.grid(row=0, column=0, sticky="w")
        
        # Настройка весов для правой части
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        help_frame.columnconfigure(0, weight=1)
        help_frame.rowconfigure(0, weight=1)
        
    def refresh_ports(self):
        """Обновить список доступных COM-портов"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox['values'] = ports
        if ports:
            self.port_combobox.current(0)
            
    def toggle_connection(self):
        """Подключиться/отключиться от COM-порта"""
        if not self.is_connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        """Подключиться к выбранному COM-порту"""
        port = self.port_var.get()
        if not port:
            self.log_message("Ошибка: не выбран COM-порт!")
            return
            
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            
            self.is_connected = True
            self.connect_btn.config(text="Отключиться", style="Red.TButton")
            self.connect_btn.config(text="Отключиться")
            self.clear_btn.config(state="normal")
            self.send_btn.config(state="normal")
            
            # Запуск потока для чтения данных
            self.read_thread = Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()
            
            self.log_message(f"Подключено к {port}")
            
        except serial.SerialException as e:
            self.log_message(f"Ошибка подключения: {e}")
            
    def disconnect(self):
        """Отключиться от COM-порта"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
        self.is_connected = False
        self.connect_btn.config(text="Подключиться")
        self.clear_btn.config(state="disabled")
        self.send_btn.config(state="disabled")
        
        self.log_message("Отключено от COM-порта")
        
    def send_clear(self):
        """Отправить команду CLEAR_ALL"""
        if self.is_connected and self.serial_port:
            try:
                self.serial_port.write("CLEAR_ALL\r\n".encode('ascii'))
                self.log_message("Отправлено: CLEAR_ALL")
            except serial.SerialException as e:
                self.log_message(f"Ошибка отправки: {e}")
                
    def send_command(self):
        """Отправить сконфигурированную команду"""
        if not self.is_connected or not self.serial_port:
            return
            
        signal = self.signal_var.get()
        pin = self.pin_var.get()
        
        if not signal or not pin:
            self.log_message("Ошибка: не выбраны параметры!")
            return
            
        command = f"INP_{pin}_{signal}\r\n"
        
        try:
            self.serial_port.write(command.encode('ascii'))
            self.log_message(f"Отправлено: {command.strip()}")
        except serial.SerialException as e:
            self.log_message(f"Ошибка отправки: {e}")
            
    def read_serial(self):
        """Чтение данных из COM-порта в отдельном потоке"""
        while self.is_connected and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('ascii', errors='ignore').strip()
                    if data:
                        self.root.after(0, self.log_message, f"Получено: {data}")
            except (serial.SerialException, UnicodeDecodeError):
                break
            time.sleep(0.1)
            
    def log_message(self, message):
        """Добавить сообщение в лог"""
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        
    def on_closing(self):
        """Обработчик закрытия окна"""
        if self.is_connected:
            self.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()

    style = ttk.Style()
    style.configure("Red.TButton", background="green")
    app = SerialApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()