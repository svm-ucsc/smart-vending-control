import paho.mqtt.client as mqtt
import json
 
@dataclass
class Item(): 
  def __init__(self, info:dict):
    self.UUID = info["UUID"]  # indicates order which item is part of 
    self.name = info["name"]
    self.quantity = info["quantity"]
    self.weight = info["weight"]
    self.density = info["density"]
    self.location = info["location"]  # tuple (row, column)
  
def parse_payload(payload) -> List:
  """Reads JSON file and organizes information in Item dataclass.
  Returns a list of item objects.
  """
  order = []
  with open(payload) as payload:
    item_info = json.load(payload)
    for i in item_info:
      order.append(Item(i))
  return order

def schedule_order(order:List(Item)) -> List:
  """Determines the order in which items should be dispensed based on location
  Returns sorted list of item objects.
  """
  row_num = 1
  sorted_order = []
  def get_row(row_num):
    for i in order:
      if i.location[0] == row_num:
        sorted_order.append(i)
  while len(sorted_order) < len(order):
    get_row(row_num)
    row_num += 1
  return sorted_order
           
def dispense(sorted_order:List(Item) -> str):
  """Dispenses all items in order. Returns success or failure"""
  pass
  
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("topic")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
  """Processes and dispenses order. Returns success or failure message upon completion
  Published message consists of UUID for order and indication of success or failure
  """
  print(msg.topic+" "+str(msg.payload))
  order = parse_payload(msg.payload)
  sorted_order = schedule_order(order)
  dispense(sorted_order)
 
  

client = mqtt.Client()
client.username_pw_set("lenatest", "password")
client.on_connect = on_connect
client.on_message = on_message

client.connect("ec2-3-87-77-241.compute-1.amazonaws.com", 1884, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()