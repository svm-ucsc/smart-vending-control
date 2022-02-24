import paho.mqtt.client as mqtt
import json
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_StepperM

# MOTOR SETUP
# One hat can control 2 motors
### To define hat: 
# need unique address for each hat. default is 0x60
# mhat1 = Adafruit_MotorHAT(addr = ???)
### Item Lane motors:
# name corresponding to item lane in row X column Y
# laneXY = mhat1.getStepper(*insert step number here*, *insert port number here*)
### Platform:
# plat = mhat2.getStepper(*insert step number here*, *insert port number here*)

class Item(): 
  def __init__(self, info:dict):
    self.UUID = info["UUID"]  # indicates order which item is part of 
    self.name = info["name"]
    self.quantity = info["quantity"]  # number to be dispensed
    self.weight = info["weight"]
    self.density = info["density"]
    self.row = info["row"]
    self.column = info["column"]
  
def parse_payload(payload):
  """Reads JSON file and organizes information in Item dataclass.
  Returns a list of item objects.
  """
  order = []
  item_info = json.loads(payload)
  for i in item_info:
    order.append(Item(i))
  return order

def schedule_order(order):
  """Determines the order in which items should be dispensed based on location
  Returns sorted list of item objects.
  """
  print("sorting:")
  row_num = 1
  sorted_order = []
  def get_row(row_num):
    for i in order:
      if i.row == row_num:
        sorted_order.append(i)
  while len(sorted_order) < len(order):
    get_row(row_num)
    row_num += 1
  print(sorted_order)
  return sorted_order
           
def dispense(sorted_order):
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
  # publish success or failure message here ***
 
  

client = mqtt.Client()
client.username_pw_set("lenatest", "password")
client.on_connect = on_connect
client.on_message = on_message

client.connect("ec2-3-87-77-241.compute-1.amazonaws.com", 1884, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()
