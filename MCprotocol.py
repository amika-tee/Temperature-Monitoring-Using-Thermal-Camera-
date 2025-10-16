from pymcprotocol import Type3E

PLC_IP = "192.168.3.39"  
PLC_PORT = 502        

plc = Type3E()

try:
    plc.connect(PLC_IP, PLC_PORT)
    print("Connected to PLC")
except Exception as e:
    print(f"Failed to connect: {e}")
    exit()


value_to_write = 600
plc.batchwrite_wordunits(headdevice="D100", values=[value_to_write])
print(f"Wrote {value_to_write} to D100")

# read_values = plc.batchread_wordunits(headdevice="D100", readlength=1)
# print(f"Read from D100: {read_values[0]}")

# Close connection
plc.close()
