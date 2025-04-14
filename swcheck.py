import os
import shutil
import sys
import dotenv
import threading
import customtkinter as ctk

from tkinter import filedialog, messagebox, scrolledtext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add a global variable to store the subprocess
process = None

# Set appearance mode and color theme
ctk.set_appearance_mode("Dark")  # "System", "Dark", or "Light"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# Create the main GUI window
root = ctk.CTk()
root.title("SWCHECK")
root.geometry("720x550")
root.resizable(False, False)

# Set the icon for the window
icon_path = os.path.join(os.path.dirname(__file__), 'Icon1.ico')  # Ensure the icon is in the same directory
root.iconbitmap(icon_path)


# Function to check for required files and set checkmarks
def check_files():
    if os.path.exists("ip.txt"):
        checkmark_ip.configure(text="✔️")
    if os.path.exists("com_table.xlsx"):
        checkmark_excel.configure(text="✔️")
    if os.path.exists(".env"):
        checkmark_credentials.configure(text="✔️")


# Function to display the result log
def show_result_log(output):
    log_window = ctk.CTkToplevel(root)
    log_window.title("Результат выполнения")
    log_window.geometry("600x400")
    log_window.after(200, lambda: log_window.iconbitmap(icon_path))

    # Lift the log window to make sure it stays on top of the main window
    log_window.grab_set()
    log_window.lift()

    log_text = scrolledtext.ScrolledText(log_window, wrap="word", font=("Arial", 12))
    log_text.pack(padx=10, pady=10, fill="both", expand=True)
    log_text.insert("1.0", output)
    log_text.config(state="disabled")  # Make the text read-only

    close_button = ctk.CTkButton(log_window, text="Закрыть", command=log_window.destroy, width=100)
    close_button.pack(pady=10)


# Add this function to display the guide
def show_guide():
    guide_window = ctk.CTkToplevel(root)
    guide_window.title("Руководство по использованию")
    guide_window.geometry("950x700")
    guide_window.after(200, lambda: guide_window.iconbitmap(icon_path))

    # Ensure the guide window stays on top of the main window
    guide_window.attributes("-top", True)
    guide_window.lift()

    # Add instructions
    instructions = """
    Руководство по использованию SWCHECK:

    1. Укажите IP адреса устройств, с которых необходимо собрать информацию:
        - Нажмите кнопку "Указать"
        - В появившемся окне укажите IP адреса в столбце без запятых и прочих знаков препинания.
        - "Применить"
        Если операция прошла успешна - появится галочка.

    2. Скачайте Excel таблицу, которую потом необходимо заполнить с вашей корректной коммутацией (просьба не изменять название "шапки":
       - Нажмите кнопку "Скачать"
       - Дайте имя файлу и сохраните в удобное для Вас место.

    3. Выберите измененный Вами файл в предыдущем действии:
       - "Выбрать" 

    4. Укажите логин и пароль:
       - Введите логин и пароль в соответствующие поля и нажмите "Сохранить данные".
       Если для какого-то устройства из списка IP адресов указанные данные не подойдут, появится окно с возможностью пропустить, 
       либо указать для этого устройства другой логин или пароль.
       - Нажмите "Сохранить данные"

    5. Нажмите кнопку "Начать проверку" для запуска процесса проверки коммутации.

    6. После завершения проверки, новая таблица будет сохранена в текущей директории.

    Если в папке с swcheck.exe уже присутствуют файлы ip.txt, com_table.xlsx, .env - то можно сразу начать проверку.
    В дальнейшем, если так удобнее, то можно изменять эти файлы в ручную, а не через кнопки.

    Необходимо учесть, что проверка LLDP работает пока что только для 4-х вендоров: Huawei (DC switches), Cisco (Nexus Switches), B4COM 4xxx-2xxx)
    Проверка сигналов TX/RX работает только для Huawei (DC switches) и B4COM 4xxx.

    Сравнивание RX/TX производится следующим образом: берет текущее значение TX/RX с оборудования и сравнивается с диапазоном от -4 до 4.
    Если между этим диапазоном = GOOD, если нет = BAD, если -, --, -40.00 = No Signal

    Удачной Вам проверки!
    v2.4

    Telegram:
    t.me/manwithwine

    Github:
    https://github.com/manwithwine

    """

    guide_label = ctk.CTkLabel(guide_window, text=instructions, justify="left", font=("Arial", 12))
    guide_label.pack(padx=10, pady=1, fill="both", expand=True)


# Add the "?" button to the main window
help_button = ctk.CTkButton(root, text="?", width=30, height=30, command=show_guide)
help_button.place(relx=0.98, rely=0.98, anchor="se")  # Place in the bottom-right corner

# Add checkmark labels next to buttons
checkmark_ip = ctk.CTkLabel(root, text="", font=("Arial", 16))  # For IP upload
checkmark_excel = ctk.CTkLabel(root, text="", font=("Arial", 16))  # For Excel upload
checkmark_credentials = ctk.CTkLabel(root, text="", font=("Arial", 16))  # For credentials


# Function to upload IP text file
def upload_txt():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        shutil.copy(file_path, "ip.txt")  # Copy and rename file
        checkmark_ip.configure(text="✔️")  # Show checkmark


# Function to manually input IP addresses
def manual_ip_input():
    def save_ips():
        ips = ip_text.get("1.0", "end-1c").strip()
        if not ips:
            messagebox.showwarning("Предупреждение", "Пожалуйста, введите IP адреса!")
            return

        with open("ip.txt", "w") as f:
            f.write(ips)

        checkmark_ip.configure(text="✔️")  # Show checkmark
        ip_window.destroy()

    ip_window = ctk.CTkToplevel(root)
    ip_window.title("Указать IP адрес/а")
    ip_window.geometry("750x470")
    ip_window.after(200, lambda: ip_window.iconbitmap(icon_path))

    ip_window.grab_set()
    ip_window.lift()

    instruction_label = ctk.CTkLabel(ip_window,
                                     text="Просьба указать IP адрес или адреса в столбец без указательных знаков, например:\n1.1.1.1\n2.2.2.2\n3.3.3.3\nи т.д.")
    instruction_label.pack(pady=2)

    ip_text = ctk.CTkTextbox(ip_window, wrap="word", height=150)
    ip_text.pack(padx=10, pady=5, fill="both", expand=True)

    save_button = ctk.CTkButton(ip_window, text="Применить", command=save_ips, width=200)
    save_button.pack(pady=10)


def download_sample_excel():
    # Get the path to the bundled sample file
    if getattr(sys, 'frozen', False):
        # If the application is frozen (bundled as an .exe)
        sample_path = os.path.join(sys._MEIPASS, "com_table_sample.xlsx")
    else:
        # If running in a development environment
        sample_path = "com_table_sample.xlsx"

    # Ask the user where to save the file
    save_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "com_table_sample.xlsx")],
        title="Сохранить образец Excel таблицы"
    )

    if save_path:
        try:
            shutil.copy(sample_path, save_path)
            messagebox.showinfo("Успешно", f"Образец Excel таблицы сохранен в:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")


# Function to upload Excel file
def upload_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        try:
            # Ensure the destination file is removed if it already exists
            if os.path.exists("com_table.xlsx"):
                os.remove("com_table.xlsx")

            # Copy the selected file to the destination with the correct name
            shutil.copy(file_path, "com_table.xlsx")
            checkmark_excel.configure(text="✔️")  # Show checkmark
            messagebox.showinfo("Успешно", "Файл успешно загружен и переименован в com_table.xlsx")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл: {str(e)}")


# Function to set login and password in .env file
def set_credentials():
    username = entry_username.get().strip()
    password = entry_password.get().strip()

    if not username or not password:
        messagebox.showwarning("Предупреждение", "Укажите и логин, и пароль!")
        return

    # Manually write to .env without quotes
    with open(".env", "w") as f:
        f.write(f"DEVICE_USERNAME={username}\n")
        f.write(f"DEVICE_PASSWORD={password}\n")

    checkmark_credentials.configure(text="✔️")  # Show checkmark

# Modify the global variables section
checked_devices = 0
skipped_devices = 0
total_devices = 0
last_event_was_skipped = False  # NEW
progress_label = None


def handle_device_checked(event):
    global checked_devices, skipped_devices, last_event_was_skipped

    if last_event_was_skipped:
        skipped_devices += 1
    else:
        checked_devices += 1

    update_progress_label()

root.bind('<<DeviceChecked>>', handle_device_checked)


def update_progress_label():
    if progress_label:
        progress_label.configure(text=f"Проверено: {checked_devices}/{total_devices} устройств")

# Function to start comparing
def start_comparing():
    global total_devices, checked_devices, progress_label

    checked_devices = 0

    # Check required files
    if not os.path.exists("ip.txt") or not os.path.exists("com_table.xlsx"):
        messagebox.showerror("Ошибка", "Просьба загрузить и указать необходимые данные!")
        return

    # Count IPs
    try:
        with open("ip.txt", "r", encoding='utf-8') as f:
            ip_list = [line.strip() for line in f if line.strip()]
        total_devices = len(ip_list)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось прочитать IP адреса: {str(e)}")
        return

    # Check credentials
    dotenv.load_dotenv(override=True)
    username = os.getenv("DEVICE_USERNAME")
    password = os.getenv("DEVICE_PASSWORD")

    if not username or not password:
        messagebox.showerror("Ошибка", "Укажите логин и пароль и сохраните данные!")
        return

    # Setup progress UI
    progress_bar = ctk.CTkProgressBar(root, mode="indeterminate")
    progress_bar.grid(row=13, column=0, columnspan=3, pady=5, sticky="ew")

    progress_label = ctk.CTkLabel(root, text=f"Проверено: 0/{total_devices} устройств", font=("Arial", 12))
    progress_label.grid(row=14, column=0, columnspan=3, pady=5)

    progress_bar.start()

    def run_check():
        global checked_devices
        output = ""

        try:
            # Import main functions directly
            from main import read_ip_addresses, main

            # Redirect stdout to capture output
            from io import StringIO
            import sys

            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            # Run main logic
            result_file, checked_result, skipped_result = main()

            # Restore stdout
            sys.stdout = old_stdout
            output = mystdout.getvalue()

            # Update progress
            checked_devices = total_devices
            root.after(0, update_progress_label)

            def show_summary_popup(log_output, result_file, checked_result, skipped_result):
                result_window = ctk.CTkToplevel(root)
                result_window.title("Результат проверки")
                result_window.geometry("480x180")
                result_window.after(200, lambda: result_window.iconbitmap(icon_path))
                result_window.grab_set()
                result_window.lift()

                message = (
                    f"Успешно проверено: {checked_result} устройств.\n"
                    f"Не удалось подключиться к: {skipped_result} устройству/ам.\n"
                    f"\nРезультат сохранен в файл:\n{result_file}"
                )
                msg_label = ctk.CTkLabel(result_window, text=message, font=("Arial", 14), justify="left")
                msg_label.pack(padx=10, pady=10)

                button_frame = ctk.CTkFrame(result_window)
                button_frame.pack(pady=10)

                def close_summary():
                    result_window.destroy()

                def show_full_log():
                    result_window.destroy()
                    show_result_log(log_output)

                btn_ok = ctk.CTkButton(button_frame, text="ОК", command=close_summary, width=120)
                btn_details = ctk.CTkButton(button_frame, text="Подробнее", command=show_full_log, width=120)
                btn_ok.grid(row=0, column=0, padx=10)
                btn_details.grid(row=0, column=1, padx=10)

            # show summary window instead of simple messagebox
            root.after(0, lambda: show_summary_popup(output, result_file, checked_result, skipped_result))

        except Exception as e:
            output += f"\nОшибка: {str(e)}"
            root.after(0, lambda: messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}"))

        finally:
            progress_bar.stop()
            progress_bar.grid_forget()
            if progress_label:
                progress_label.grid_forget()

            pass

    # Run in thread
    threading.Thread(target=run_check, daemon=True).start()


# UI Elements
label_welcome = ctk.CTkLabel(root, text="Добро пожаловать в SWCHECK!", font=("Arial", 16, "bold"))
label_welcome.grid(row=0, column=0, columnspan=3, pady=30)
label_guide = ctk.CTkLabel(root, text="Заполните необходимые данные по порядку и нажмите на кнопку - Начать проверку",
                           font=("Arial", 16, "bold"))
label_guide.grid(row=1, column=0, columnspan=3, pady=40)

# Manual IP input
label_manual_ip = ctk.CTkLabel(root, text="Укажите IP адреса устройств:")
label_manual_ip.grid(row=2, column=0, columnspan=3, pady=1)
btn_manual_ip = ctk.CTkButton(root, text="Указать", command=manual_ip_input, width=200)
btn_manual_ip.grid(row=3, column=0, columnspan=3, pady=1)
checkmark_ip.grid(row=3, column=1, columnspan=3, pady=1)  # Place checkmark to the right of the button

# Download sample Excel file
label_download_sample = ctk.CTkLabel(root,
                                     text="Скачайте образец Excel файла, заполните данными с корректной коммутацией:")
label_download_sample.grid(row=4, column=0, columnspan=3, pady=1)
btn_download_sample = ctk.CTkButton(root, text="Скачать", command=download_sample_excel, width=200)
btn_download_sample.grid(row=5, column=0, columnspan=3, pady=1)

# Upload Excel file
label_excel = ctk.CTkLabel(root, text="Выберите Вашу Excel таблицу с корректной коммутацией:")
label_excel.grid(row=6, column=0, columnspan=3, pady=2)
btn_upload_excel = ctk.CTkButton(root, text="Выбрать", command=upload_excel, width=200)
btn_upload_excel.grid(row=7, column=0, columnspan=3, pady=1)
checkmark_excel.grid(row=7, column=1, columnspan=3, pady=1)  # Place checkmark to the right of the button

# Login credentials
label_credentials = ctk.CTkLabel(root, text="Укажите логин и пароль:")
label_credentials.grid(row=8, column=0, columnspan=3, pady=1)
entry_username = ctk.CTkEntry(root, width=200)
entry_username.grid(row=9, column=0, columnspan=3, pady=1)
entry_username.insert(0, os.getenv("DEVICE_USERNAME", ""))
entry_password = ctk.CTkEntry(root, width=200, show="*")  # Hide password
entry_password.grid(row=10, column=0, columnspan=3, pady=1)
entry_password.insert(0, os.getenv("DEVICE_PASSWORD", ""))
btn_save_credentials = ctk.CTkButton(root, text="Сохранить данные", command=set_credentials, width=200)
btn_save_credentials.grid(row=11, column=0, columnspan=3, pady=1)
checkmark_credentials.grid(row=11, column=1, columnspan=3, pady=1)  # Place checkmark to the right of the button

# Start button
btn_start_comparing = ctk.CTkButton(root, text="Начать проверку", command=start_comparing, width=200)
btn_start_comparing.grid(row=12, column=0, columnspan=3, pady=30)

# Configure grid weights to make the UI elements dynamically centralize
for i in range(9):
    root.grid_rowconfigure(i, weight=1, minsize=10)  # Adjust minsize for better scaling
for j in range(3):
    root.grid_columnconfigure(j, weight=1, minsize=10)

# Check for required files on startup
check_files()

# Run the GUI
root.mainloop()