import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import simpledialog

from classes.device import Device
from classes.parser import LogParser
from classes.excel_handler import ExcelHandler
from classes.cleanup_output import OutputCleaner
from classes.cleanup_signal_output import SignalOutputCleaner
from classes.parser_signal import SignalLogParser

load_dotenv()  # Load environment variables from a .env file


def read_ip_addresses(file_path):
    with open(file_path, "r") as file:
        return file.readlines()


def main():
    # Read IP addresses from the file
    ip_addresses = read_ip_addresses("ip.txt")
    if not ip_addresses:
        print("Отсутствуют ip адреса в ip.txt")
        return

    # Initialize the Excel handler
    excel_handler = ExcelHandler("com_table.xlsx")
    all_logs = {}
    signal_logs = {}

    # Retrieve credentials from environment variables
    default_username = os.getenv("DEVICE_USERNAME", "login")
    default_password = os.getenv("DEVICE_PASSWORD", "password")

    root = tk.Tk()
    root.withdraw()  # Hide the main window
    root.iconbitmap()
    root.attributes('-toolwindow', True)

    # Collect and clean logs for each device
    for ip in ip_addresses:
        ip = ip.strip()  # Strip newline and spaces
        if not ip:
            continue

        print(f"Подключение к устройству с IP: {ip}")
        device = Device(ip, username=default_username, password=default_password)

        while True:
            # Establish connection and detect vendor
            if device.connect():
                print(f"Успешное подключение к {ip}. Определение вендора...")

                device.detect_vendor()

                # Define commands for each vendor
                commands = {
                    "Huawei": ["screen-length 0 temporary", "display sysname", "display lldp neighbor brief",
                               "display interface transceiver brief"],
                    "Cisco": ["terminal length 0", "show hostname", "show lldp neighbors",
                              "sh int transceiver det | exclude present"],
                    "B4COM": ["terminal length 0", "show hostname", "show lldp neighbors brief | include bridge",
                              "sh int transceiver | exclude Codes"],
                    "B4TECH": ["terminal length 0", "show run | i hostname", "show lldp neigh br",
                               "sh transceiver detail"],
                }

                # Execute the commands for the detected vendor
                if device.vendor in commands:
                    print(f"Выполнение команд для {device.vendor}...")
                    raw_logs = device.execute_commands(commands[device.vendor])

                    cleaned_logs = {}
                    signal_log_parts = []

                    # Process each command's output
                    for idx, (command, output) in enumerate(raw_logs.items()):
                        cleaned_output = OutputCleaner.cleanup_output(device.vendor, output)

                        # Cleaned logs: Add cleaned output of the 2nd and 3rd commands
                        if idx in {1, 2}:  # Commands 2nd and 3rd
                            cleaned_logs[command] = cleaned_output

                        # Signal logs: Add raw output of the 2nd and 4th commands
                        if idx in {1, 3}:  # Commands 2nd and 4th
                            raw_signal_log = f"{output}"
                            cleaned_signal_log = SignalOutputCleaner.cleanup_signal_output(device.vendor,
                                                                                           raw_signal_log)
                            signal_log_parts.append(cleaned_signal_log)

                    # Store cleaned logs and signal logs separately per device and vendor
                    if device.vendor not in all_logs:
                        all_logs[device.vendor] = {}
                    all_logs[device.vendor][ip] = "\n".join(cleaned_logs.values())

                    signal_logs[ip] = "\n".join(signal_log_parts)

                # Disconnect the device after processing
                device.disconnect()
                print(f"Разъединение от {ip}")
                break

            else:  # Connection failed
                print(f"Не удалось подключиться к устройству: {ip}.")

                # Skip device if the failure is not due to authentication
                if "Authentication failed" not in device.last_error:
                    print(f"Пропускаем устройство {ip}.")
                    break

                    # If authentication failed, ask for new credentials
                choice = simpledialog.askstring(
                    "Аутентификация не прошла",
                    f"Указать новые данные (y) или пропустить (s) для устройства - {ip}:", parent=root
                )
                if not choice or choice.lower() == "s":
                    break  # Skip this device
                elif choice.lower() == "y":
                    device.username = simpledialog.askstring("Логин", "Введите логин:", parent=root)
                    device.password = simpledialog.askstring("Пароль", "Введите пароль:", show="*", parent=root)

    if not all_logs:
        print("Логи не собраны.")
        return

    # Parse logs and prepare data for Excel
    parsed_data = []
    for vendor, logs in all_logs.items():
        for ip, log_content in logs.items():
            lines = log_content.splitlines()
            if vendor == "Cisco":
                parsed_data.extend(LogParser.parse_cisco_logs(lines))
            elif vendor == "Huawei":
                parsed_data.extend(LogParser.parse_huawei_logs(lines))
            elif vendor == "B4COM":
                parsed_data.extend(LogParser.parse_b4com_logs(lines))
            elif vendor == "B4TECH":
                parsed_data.extend(LogParser.parse_b4tech_logs(lines))

    if not parsed_data:
        print("Отсутствуют данные для парсинга.")
        return

    # Parse signal logs
    parsed_signal_data = []
    for ip, log_content in signal_logs.items():
        vendor = next((v for v, d in all_logs.items() if ip in d), None)

        if not vendor:
            print(f"Вендор не определен для: {ip}. Устройство пропущено.")
            continue

        lines = log_content.splitlines()
        if vendor == "Huawei":
            parsed_signal_data.extend(SignalLogParser.parse_huawei_signal_logs(lines))
        elif vendor == "B4COM":
            parsed_signal_data.extend(SignalLogParser.parse_b4com_signal_logs(lines))

    # Populate Excel
    result_file = excel_handler.populate_and_compare(parsed_data, parsed_signal_data)
    print(f"Результат сохранен в файл {result_file}")


if __name__ == "__main__":
    main()
