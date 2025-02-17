from netmiko import ConnectHandler

class Device:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.vendor = None
        self.connection = None
        self.last_error = ""  # Store the last error message

    def connect(self):
        try:
            self.connection = ConnectHandler(
                device_type='autodetect',
                host=self.ip,
                username=self.username,
                password=self.password,
                global_delay_factor=2,
                read_timeout_override=100,
                timeout=30,
                fast_cli=False
            )
            return True
        except Exception as e:
            self.last_error = str(e)  # Store error for later checks
            print(f"Не удалось подключиться к {self.ip}: {self.last_error}")
            return False


    def detect_vendor(self):
        commands = ["show version", "show ver | i BCOM", "dis version | i HUAWEI"]
        output = None

        for command in commands:
            output = self.connection.send_command(command)
            if 'Huawei' in output:
                self.vendor = 'Huawei'
                break
            elif 'Cisco' in output:
                self.vendor = 'Cisco'
                break
            elif 'BCOM' in output:
                self.vendor = 'B4COM'
                break
            elif 'B4TECH' in output:
                self.vendor = 'B4TECH'
                break
        else:
            self.vendor = 'Unknown'  # If no match is found after all commands

        print(f"Вендор определен: {self.vendor}")  # Debug print to check the result

    def execute_commands(self, commands):
        if not self.connection:
            raise Exception("Нет активного подключения для выполнения команд.")
        results = {}
        for command in commands:
            results[command] = self.connection.send_command(command)
        return results

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
