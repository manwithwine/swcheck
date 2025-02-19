import re

class OutputCleaner:
    @staticmethod
    def cleanup_output(vendor, raw_output):
        cleaned_output = raw_output
        if vendor == "Huawei":
            lines = cleaned_output.splitlines()
            filtered_lines = []
            for line in lines:
                if not (line.strip().startswith("Local") or "--" in line):
                    filtered_lines.append(line)
            cleaned_output = "\n".join(filtered_lines)
            cleaned_output = cleaned_output.replace('Command: display sysname', '')
            cleaned_output = cleaned_output.replace('Command: display lldp neighbor brief', '')
            cleaned_output = cleaned_output.replace(
                'Info: The configuration takes effect on the current user terminal interface only.', '')
            cleaned_output = cleaned_output.strip()

        elif vendor == "Cisco":
            cleaned_output = re.sub(r'Hostname\n\n', 'Hostname', cleaned_output)
            cleaned_output = cleaned_output.replace('Command: show hostname', '')
            cleaned_output = cleaned_output.replace('Command: show lldp neighbors', '')
            cleaned_output = cleaned_output.replace(
                'Capability codes:\n  (R) Router, (B) Bridge, (T) Telephone, (C) DOCSIS Cable Device\n  (W) WLAN Access Point, (P) Repeater, (S) Station, (O) Other\nDevice ID            Local Intf      Hold-time  Capability  Port ID  ',
                '')
            cleaned_output = re.sub(r'  \d+  \d+\n', '', cleaned_output)
            cleaned_output = re.sub(r'Total entries displayed:.*', '',
                                    cleaned_output)
            cleaned_output = cleaned_output.strip()

        elif vendor == "B4COM":
            # Remove unnecessary patterns
            cleaned_output = cleaned_output.replace('Nearest bridge', '')
            cleaned_output = cleaned_output.replace('Command: show hostname', '')
            cleaned_output = cleaned_output.replace('Command: show lldp neighbors brief | include bridge', '')
            # Remove chassis ID patterns
            cleaned_output = re.sub(r'([a-f0-9]{4}\.[a-f0-9]{4}\.[a-f0-9]{4})(?=\s+[a-f0-9]{4}\.[a-f0-9]{4}\.[a-f0-9]{4})', '', cleaned_output)
            # Remove lines starting with "---" or "Loc PortID"
            cleaned_output = "\n".join(
                line for line in cleaned_output.splitlines()
                if not (line.strip().startswith('---') or line.strip().startswith('Loc PortID'))
            )
            # Strip unnecessary leading/trailing whitespace and empty lines
            cleaned_output = "\n".join(line.strip() for line in cleaned_output.splitlines() if line.strip())

        elif vendor == "B4TECH":
            cleaned_output = cleaned_output.replace('Command: show run | i hostname', '')
            cleaned_output = cleaned_output.replace('Command: show lldp neigh br', '')
            cleaned_output = cleaned_output.replace('------------------------------------------------------------', '')
            cleaned_output = cleaned_output.strip()
        return cleaned_output