import re

class SignalOutputCleaner:
    @staticmethod
    def cleanup_signal_output(vendor, raw_output):
        if vendor == "Huawei":
            lines = raw_output.splitlines()
            cleaned_output = []
            hostname = None
            skip_lines = False
            ip_skipped = False  # Flag to track if the IP line was skipped

            for i, line in enumerate(lines):
                line = line.strip()

                # Skip the first line with the IP address
                if not ip_skipped and re.match(r"^\d+\.\d+\.\d+\.\d+", line):
                    ip_skipped = True
                    continue  # Skip the IP address line

                # Remove "transceiver diagnostic information" from relevant lines
                line = re.sub(r"transceiver diagnostic information:", "", line).strip()

                # Capture hostname (first occurrence after the IP address)
                if not hostname and re.match(r"^\d+\.\d+\.\d+\.\d+", line):
                    hostname = line
                    cleaned_output.append(hostname)
                    continue

                # Detect interface lines (100GE1/0/1, 25GE1/0/25, etc.)
                if re.match(r"\d+(GE|FE|XE)\d+/\d+/\d+", line):
                    current_interface = line
                    cleaned_output.append(current_interface)
                    skip_lines = True  # Start skipping lines after finding an interface
                    continue

                # Skip all lines between interface and the first "Current RX Power" line
                if skip_lines:
                    if line.startswith("Current RX Power"):
                        skip_lines = False  # Stop skipping once we reach "Current RX Power"
                    else:
                        continue  # Skip this line and move to the next

                # Extract and format RX/TX Power values correctly (Type 2 merging)
                if "Current RX Power" in line or "Current TX Power" in line:
                    match = re.match(
                        r"(Current (RX|TX) Power \(dBm\))\s*:\s*(-?\d+\.\d+|\-|\|)(\s*\|\s*(-?\d+\.\d+|\-|\|))?", line)
                    if match:
                        label = match.group(1)
                        value1 = match.group(3)
                        value2 = match.group(5) if match.group(5) else ""

                        # Format values as required
                        if value1 == "-|-" and value2 == "":
                            line = f"{label}  :-|-       -|-"
                        elif value2:
                            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                            lane_match = re.match(r"(-?\d+\.\d+|\-|\|)\s*\|\s*(-?\d+\.\d+|\-|\|)", next_line)
                            if lane_match:
                                lane1 = lane_match.group(1)
                                lane2 = lane_match.group(2)
                                line = f"{label} : {value1}, {value2}, {lane1}, {lane2}"
                                lines[i + 1] = ""  # Remove next line as it's merged
                        else:
                            line = f"{label} : {value1}"
                    else:
                        # Additional logic to replace | with , and ensure proper spacing
                        line = re.sub(r"\s*\|\s*", ", ", line)  # Replace | with a comma and space
                        line = re.sub(r"(\d+\.\d+)\s+(\-?\d+\.\d+)", r"\1, \2",
                                      line)  # Ensure spaces are replaced with commas
                        line = re.sub(r",\s+", ", ", line)  # Normalize spacing around commas

                    # Add + to positive values and leave negatives unchanged
                    line = re.sub(r"(?<![-\d])(\d+\.\d+)", r"+\1", line)  # Add + to positive numbers

                    cleaned_output.append(line)
                    continue

                # Otherwise, keep the line as it is
                if line:
                    cleaned_output.append(line)

            # Remove the last line if it's just the separator
            if cleaned_output and re.match(r"^[-]+$", cleaned_output[-1]):
                cleaned_output.pop()

            return "\n".join(cleaned_output).strip()

        elif vendor == "B4COM":
            lines = raw_output.splitlines()
            result = []

            # Extract the hostname from the first line
            hostname = lines[0].strip()
            result.append(f"{hostname}\n")

            current_interface = None
            tx_data = []  # To store TX values
            rx_data = []  # To store RX values

            for line in lines:
                # Remove `*` and `**` from the line
                clean_line = re.sub(r"\*+", "", line).strip()
                match = re.match(r"^(ce\d+|xe\d+)", clean_line)
                if match:
                    # If a new interface starts, process the previous interface's data
                    if current_interface:
                        result.append(f"{current_interface}")
                        result.append(f"        {','.join(tx_data)}")  # Add TX values
                        result.append(f"        {','.join(rx_data)}")  # Add RX values")

                    # Start a new interface and reset TX/RX data
                    current_interface = match.group(0)
                    tx_data = []
                    rx_data = []

                    # Process the first line for TX and RX values
                    columns = re.split(r'\s+', clean_line)
                    if len(columns) >= 2:
                        tx_data.append(columns[-2])  # TX value
                        rx_data.append(columns[-1])  # RX value

                elif current_interface and clean_line.startswith(('2', '3', '4')):
                    # Add TX and RX values for subsequent lines
                    columns = re.split(r'\s+', clean_line)
                    if len(columns) >= 2:
                        tx_data.append(columns[-2])  # TX value
                        rx_data.append(columns[-1])  # RX value

            # Process the last interface's data after the loop
            if current_interface:
                result.append(f"{current_interface}")
                result.append(f"        {','.join(tx_data)}")  # Add TX values
                result.append(f"        {','.join(rx_data)}")  # Add RX values")

            return '\n'.join(result)


        elif vendor == "Cisco":
            result = []
            lines = raw_output.splitlines()
            lane_mode = False

            # Extract the hostname from the first line
            hostname = lines[0].strip()
            result.append(hostname)
            # print(f"Hostname added: {hostname}")  # Debug: Log hostname

            # Process the remaining lines, skipping the first one
            for line in lines[1:]:  # Start from the second line
                line = line.strip()

                if re.match(r"Ethernet\d+/\d+", line):  # Match interface names
                    result.append(line)
                    lane_mode = False

                elif line.startswith("Lane Number:"):
                    lane_mode = True
                    result.append(line)

                elif "Tx Power" in line or "Rx Power" in line:
                    # Match Tx/Rx power and keep only the first two columns, discard the rest
                    cleaned_line = re.sub(r"(Tx Power|Rx Power)\s+(\S+)(.*)", r"\1 \2", line)
                    result.append("  " + cleaned_line if lane_mode else cleaned_line)

            return "\n".join(result)

        elif vendor == "B4TECH":
            result = []
            lines = raw_output.splitlines()

            # Extract the hostname from the first line
            hostname = lines[0].replace('hostname ', '').strip()
            result.append(f"{hostname}\n")


            # Step 2: Loop through the lines to find 'eth-0-x' and process every 4th and 5th line
            eth_port_data = []
            count = 0  # Counter to track lines within a block

            for line in lines[1:]:  # Skip the first line (hostname line)
                if line.startswith("eth-0-"):  # Check if the line starts with 'eth-0-'
                    count += 1
                    if count == 4:  # Add the 4th line
                        result.append(line.strip())
                    elif count == 5:  # Add the 5th line
                        result.append(line.strip())
                        count = 0  # Reset the counter after the 5th line

            # Return the cleaned output as a single string
            return "\n".join(result)

        else:
            return raw_output
