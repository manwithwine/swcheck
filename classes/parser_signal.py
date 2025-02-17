class SignalLogParser:

    @staticmethod
    def parse_huawei_signal_logs(lines):
        parsed_entries = []
        local_host = None
        local_int = None
        tx_data = None
        rx_data = None
        index = 0

        while index < len(lines):
            stripped_line = lines[index].strip()

            if not stripped_line or stripped_line.startswith('---'):
                index += 1
                continue

            # Debugging output for raw line
            # print(f"Line: {stripped_line}")

            if local_host is None or (not stripped_line.startswith("100GE") and not stripped_line.startswith("25GE")):
                # If it's a new hostname or the line doesn't start with "100GE" or "25GE" (i.e., not an interface)
                if local_host and local_int and tx_data and rx_data:
                    # Append previous entry
                    parsed_entries.append({
                        "local_host": local_host,
                        "local_int": local_int,
                        "TX": tx_data,
                        "RX": rx_data,
                    })
                local_host = stripped_line  # New hostname
                index += 1
                continue

            # Otherwise, it's an interface line
            if stripped_line.startswith("100GE") or stripped_line.startswith("25GE"):
                local_int = stripped_line  # Get interface
                try:
                    rx_data = lines[index + 1].strip().replace('Current RX Power (dBm) :', '').strip()  # RX data
                    tx_data = lines[index + 2].strip().replace('Current TX Power (dBm) :', '').strip()  # TX data
                except IndexError:
                    # print(f"Error processing lines at index {index}. Check log formatting.")
                    break  # In case of unexpected formatting

                parsed_entries.append({
                    "local_host": local_host,
                    "local_int": local_int,
                    "TX": tx_data,
                    "RX": rx_data,
                })
                index += 4  # Move past the current interface block
            else:
                index += 1

        # print("Huawei Parsed Entries:")
        # for entry in parsed_entries:
        #     print(entry)  # Print each parsed entry for Huawei

        return parsed_entries

    @staticmethod
    def parse_b4com_signal_logs(lines):
        parsed_entries = []
        local_host = None
        local_int = None
        tx_data = None
        rx_data = None
        index = 0

        while index < len(lines):
            stripped_line = lines[index].strip()

            if not stripped_line or stripped_line.startswith('---'):
                index += 1
                continue

            # # Debugging output for raw line
            # print(f"Line: {stripped_line}")

            if local_host is None or not (stripped_line.startswith("ce") or stripped_line.startswith("xe")):
                # If it's a new hostname or the line doesn't start with "ce" or "xe" (i.e., not an interface)
                if local_host and local_int and tx_data and rx_data:
                    # Append previous entry
                    parsed_entries.append({
                        "local_host": local_host,
                        "local_int": local_int,
                        "TX": tx_data,
                        "RX": rx_data,
                    })
                local_host = stripped_line  # New hostname
                index += 1
                continue

            # Otherwise, it's an interface line
            if stripped_line.startswith("ce") or stripped_line.startswith("xe"):
                local_int = stripped_line  # Get interface
                tx_data = lines[index + 1].strip()  # TX data (next line)
                rx_data = lines[index + 2].strip()  # RX data (line after next)
                parsed_entries.append({
                    "local_host": local_host,
                    "local_int": local_int,
                    "TX": tx_data,
                    "RX": rx_data,
                })
                index += 3  # Move past the current interface block
            else:
                index += 1

        # print("B4COM Parsed Entries:")
        # for entry in parsed_entries:
        #     print(entry)  # Print each parsed entry for B4COM

        return parsed_entries

