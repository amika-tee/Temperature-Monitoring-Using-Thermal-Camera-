import struct
from pymodbus.client import ModbusTcpClient

class ModbusClient:
    def __init__(self, host: str, port: int = 502):
        self.host = host
        self.port = port
        self.client = ModbusTcpClient(host=self.host, port=self.port)

        # Map states to PLC addresses
        self.address_map = {
            "state1": 100,
            "state2": 102,
            "state3": 104
        }

        # Buffer to store received temperatures
        self.avg_temp_received = {state: [] for state in self.address_map}

    def connect(self) -> bool:
        return self.client.connect()

    def close(self):
        self.client.close()

    def write_float(self, address: int, value: float):
        """Write a float to two Modbus registers with word swap"""
        packed = struct.pack(">f", value)
        regs = struct.unpack(">HH", packed)[::-1]  # swap words
        return self.client.write_registers(address=address, values=regs)

    def read_float(self, address: int):
        """Read a float from two Modbus registers"""
        resp = self.client.read_holding_registers(address=address, count=2)
        if resp.isError():
            return None
        regs = resp.registers[::-1]  # swap words back
        raw = struct.pack(">HH", *regs)
        return struct.unpack(">f", raw)[0]

    def receive_temp(self, data: dict):
        """
        Receive temperature data from another script and send to PLC immediately.
        `data` should be like {'state1': 25.3, 'state2': 30.1, 'state3': 28.7}
        """
        for state, temp in data.items():
            # Store in buffer
            if state in self.avg_temp_received:
                self.avg_temp_received[state].append(temp)

                # Send to PLC
                addr = self.address_map[state]
                self.write_float(addr, temp)
                print(f"{state} sent to D{addr}: {temp}")

        print("Received temperatures:", data)


if __name__ == "__main__":
    PLC_IP = "192.168.3.40"
    client = ModbusClient(PLC_IP)

    if client.connect():
        # Example: simulate receiving data from another script
        sample_data = {
            "state1": 25.3,
            "state2": 30.1,
            "state3": 28.7
        }
        client.receive_temp(sample_data)

        client.close()
