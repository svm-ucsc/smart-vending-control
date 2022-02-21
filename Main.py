import paho.mqtt.client as mqtt

@dataclass
class Vending(): 
  def __init__(self, order:dict): 
    self.order = order
 
@dataclass
class Item(): 
  def __init__(self, price, host = Vending object, initial_stock, packet = barcode packet): 
    self.host = host  “Host machine” 
    self.name = “”  
    self.packet = packet 
    self.nutrition = numpy array 
    self.stock = stock 
    self.image = ? 
  
def parse_payload(payload):
  """Reads JSON file and organizes information in data classes"""
  pass
           
def dispense():
  """Dispenses all items in order"""
  pass
  
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
  parse_payload(msg)
  

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("mqtt.eclipseprojects.io", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()