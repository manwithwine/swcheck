import re

class LogParser:
    @staticmethod
    def parse_cisco_logs(lines):
        local_host = None
        parsed_entries = []
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if len(stripped_line.split()) == 1:
                local_host = stripped_line
                continue
            local_int = stripped_line[21:36].strip()
            remote_host = stripped_line[0:18].strip()
            remote_int = stripped_line[60:].strip()
            if local_host and local_int and remote_host and remote_int:
                parsed_entries.append((local_host, local_int, remote_host, remote_int))
        return parsed_entries

    @staticmethod
    def parse_huawei_logs(lines):
        local_host = None
        parsed_entries = []
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if len(stripped_line.split()) == 1:
                local_host = stripped_line
                continue
            local_int = stripped_line[0:24].strip()
            remote_host = stripped_line[65:].strip()
            remote_int = stripped_line[35:65].strip()
            if local_host and local_int and remote_host and remote_int:
                parsed_entries.append((local_host, local_int, remote_host, remote_int))
        return parsed_entries


    @staticmethod
    def parse_b4com_logs(lines):
        local_host = None
        parsed_entries = []
        mac_regex = re.compile(r"[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}")  # MAC format xxxx.xxxx.xxxx

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Handle local host declaration
            if len(stripped_line.split()) == 1:
                if local_host is None:
                    local_host = stripped_line
                continue

            # **Remove MACs from the entire line first**
            cleaned_line = mac_regex.sub("", stripped_line).strip()

            # Split the line into parts
            parts = cleaned_line.split()

            # Ensure at least 3 valid parts (Local Int, Remote Host, Remote Int)
            if len(parts) >= 3:
                local_int = parts[0]
                remote_host = parts[1]
                remote_int = parts[-1]

                # Append parsed entry
                if local_host:
                    parsed_entries.append((local_host, local_int, remote_host, remote_int))
                    # print(
                    #     f"Parsed entry: Local Host: {local_host}, Local Int: {local_int}, Remote Host: {remote_host}, Remote Int: {remote_int}")

        return parsed_entries

    @staticmethod
    def parse_b4tech_logs(lines):
        local_host = None
        parsed_entries = []
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if len(stripped_line.split()) == 1:
                local_host = stripped_line
                continue
            if line.startswith("Local Port"):
                local_int = stripped_line.split(":")[1].strip()
                remote_int = lines[i + 1].split(":")[1].strip()
                remote_host = lines[i + 4].split(":")[1].strip()
                if local_host and local_int and remote_host and remote_int:
                    parsed_entries.append((local_host, local_int, remote_host, remote_int))
        return parsed_entries
