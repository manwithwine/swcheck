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

            hostname = lines[0].split('>')[0].strip() if '>' in lines[0] else lines[0].strip()
            result.append(hostname)

            current_interface = None
            tx_data = []  # To store TX values
            rx_data = []  # To store RX values
            processing_first_table = True  # Flag to track which table we're processing

            for line in lines:
                # Check if we've reached the second table header
                if "PreFecBer" in line or "LvlTrans" in line:
                    processing_first_table = False
                    continue

                if not processing_first_table:
                    continue

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

        # elif vendor == "Cisco":
        #     result = []
        #     lines = raw_output.splitlines()
        #
        #     # Extract hostname (first line before #)
        #     hostname = lines[0].split('#')[0].strip()
        #     result.append(hostname)
        #     current_interface = None
        #     lane_data = {}  # {lane_number: {'tx': value, 'rx': value}}
        #
        #     for line in lines:
        #         line = line.strip()
        #         # Find interface lines
        #         if line.startswith("Ethernet"):
        #             # Process previous interface if exists
        #             if current_interface:
        #                 result.append(current_interface)
        #
        #                 # Collect all TX/RX values in order
        #                 tx_values = []
        #                 rx_values = []
        #
        #                 for lane in sorted(lane_data.keys()):
        #                     tx_values.append(lane_data[lane].get('tx', '--'))
        #                     rx_values.append(lane_data[lane].get('rx', '--'))
        #                 result.append(f"  Tx Power: {', '.join(tx_values)}")
        #                 result.append(f"  Rx Power: {', '.join(rx_values)}")
        #
        #             # Start new interface
        #             current_interface = line
        #             lane_data = {}
        #             continue
        #
        #         # Find lane number
        #         if line.startswith("Lane Number:"):
        #             current_lane = int(line.split(':')[1].split()[0])
        #             lane_data[current_lane] = {'tx': '--', 'rx': '--'}  # Initialize with defaults
        #
        #         # Find Tx/Rx power values
        #         elif "Tx Power" in line and current_lane:
        #             parts = line.split()
        #             if len(parts) >= 3 and parts[2] != "N/A":
        #                 lane_data[current_lane]['tx'] = parts[2]
        #
        #         elif "Rx Power" in line and current_lane:
        #             parts = line.split()
        #             if len(parts) >= 3 and parts[2] != "N/A":
        #                 lane_data[current_lane]['rx'] = parts[2]
        #
        #     # Process the last interface
        #     if current_interface and lane_data:
        #         result.append(current_interface)
        #         tx_values = []
        #         rx_values = []
        #
        #         for lane in sorted(lane_data.keys()):
        #             tx_values.append(lane_data[lane].get('tx', '--'))
        #             rx_values.append(lane_data[lane].get('rx', '--'))
        #
        #         result.append(f"  Tx Power: {', '.join(tx_values)}")
        #         result.append(f"  Rx Power: {', '.join(rx_values)}")
        #
        #     return "\n".join(result)

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
