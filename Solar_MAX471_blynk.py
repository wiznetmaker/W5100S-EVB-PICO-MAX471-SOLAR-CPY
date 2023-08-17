import board
import digitalio
import time
import busio
import struct
import BlynkLib
import MAX471


import adafruit_requests as requests
from adafruit_wiznet5k.adafruit_wiznet5k import * #active WIZnet chip library
import adafruit_wiznet5k.adafruit_wiznet5k_socket as socket #open socket from WIZnet library

BLYNK_TEMPLATE_ID = "aaaaaaaaaa"
BLYNK_DEVICE_NAME = "bbbbbbbbbbbbbbbbbbb"
BLYNK_AUTH_TOKEN = "cccccccccccccccccccccccccccccc"

# Activate GPIO pins for SPI communication
SPI0_SCK = board.GP18
SPI0_TX = board.GP19
SPI0_RX = board.GP16
SPI0_CSn = board.GP17

# Activate Reset pin for communication with W5500 chip
W5x00_RSTn = board.GP20

# Create the module with MAX471 class
meter = MAX471.MAX471(voltage_pin = board.A0, current_pin = board.A1)

print("Wiznet5k SimpleServer Test (DHCP)")

class Blynk(BlynkLib.BlynkProtocol):
    def __init__(self, auth, **kwargs):
        self.insecure = kwargs.pop('insecure', True)
        self.server = kwargs.pop('server', 'blynk.cloud')
        self.port = kwargs.pop('port', 80 if self.insecure else 443)
        BlynkLib.BlynkProtocol.__init__(self, auth, **kwargs)
        #self.on('redirect', self.redirect)
    
    def _write(self, data):
        #print('<', data)
        client.send(data)
        # TODO: handle disconnect
    
    def run(self):
        data = b''
        try:
            data = client.recv() 
            #print('>', data)
        except KeyboardInterrupt:
            raise
        #except socket.timeout:
            # No data received, call process to send ping messages when needed
            #pass
        except: # TODO: handle disconnect
            return
        self.process(data)


# Setup your network configuration below
# random MAC, later should change this value on your vendor ID
MY_MAC = (0x00, 0x08, 0xDC, 0x11, 0x22, 0x33)
IP_ADDRESS = (192, 168, 0, 111)
SUBNET_MASK = (255, 255, 0, 0)
GATEWAY_ADDRESS = (192, 168, 0, 1)
DNS_SERVER = (8, 8, 8, 8)

# Set LED for checking the network system  working
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

# Set reset function
ethernetRst = digitalio.DigitalInOut(W5x00_RSTn)
ethernetRst.direction = digitalio.Direction.OUTPUT

# Set this SPI for selecting the correct chip
cs = digitalio.DigitalInOut(SPI0_CSn)

# Set the GPIO pins for SPI communication
spi_bus = busio.SPI(SPI0_SCK, MOSI=SPI0_TX, MISO=SPI0_RX)

# Reset WIZnet's chip first
ethernetRst.value = False
time.sleep(1)
ethernetRst.value = True

# Initialize ethernet interface with DHCP
eth = WIZNET5K(spi_bus, cs, is_dhcp=True, mac=MY_MAC, debug=False)

# Show all information
print("Chip Version:", eth.chip)
print("MAC Address:", [hex(i) for i in eth.mac_address])
print("My IP address is:", eth.pretty_ip(eth.ip_address))

# Initialize steps for WIZnet's socket to create TCP server
socket.set_interface(eth)
client = socket.socket()  # Set and name the socket to be a TCP server
client_ip = "128.199.144.129"  #bkynk.cloud
client_port = 80  # HTTP port for Blynk Port
client.connect((client_ip, client_port), None)

# register handler for virtual pin V5 write event
blynk = Blynk(BLYNK_AUTH_TOKEN)

while True:
# Maintain DHCP lease (continue the DHCP setting while TCP is connected)
    eth.maintain_dhcp_lease()

    led.value = not led.value #showing the light is blinking
    time.sleep(0.1) #transmit data speed
    

    #print (client.status)
    if client.status == SNSR_SOCK_ESTABLISHED:
        blynk.run()
        # collect readings from MAX471 and uploaded to Blynk
        voltage = meter.Voltage()
        blynk.virtual_write(0, voltage)
        if round(float(voltage)) < 1:
            #Example of an event: If there is not voltage, push a event for notification
            blynk.log_event("low_voltage")
        current = meter.Current()
        blynk.virtual_write(1, current)
        power = meter.Power()
        blynk.virtual_write(2, power)
        print (("{} V").format(voltage))
        print (("{} mA").format(current))
        print(("{} W").format(power)) 
        time.sleep(1)
    elif client.status == SNSR_SOCK_CLOSE_WAIT:
        client.disconnect() #close the connection
    elif client.status == SNSR_SOCK_CLOSED:
        client.connect((client_ip, client_port), None)


