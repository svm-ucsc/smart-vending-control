import paho.mqtt.client as mqtt
import json
from movement.lane_stepper import *
import time 

BASE_WEIGHT = 0  # weight of inner platform on senors
MAX_WEIGHT = 14000  # maximum weight in grams of order that can be handled at one time
PLAT_VOL = 20    # total volume of available space on the platform
LANE_LOCATIONS = [(1,1), (1,2), (1,3), (2,1), (2,2), (2,3), (3,1), (3,2), (3,3)]
SUCCESS = True  # indicates if order handled successfully

class Item(): 
  def __init__(self, info:dict):
    self.UID = info["UID"]  # indicates order which item is part of 
    self.name = info["name"]
    self.quantity = info["quantity"]  # number to be dispensed
    self.weight = info["weight"]
    self.volume = info["volume"]
    self.row = info["row"]
    self.column = info["column"]

class Machine():
  def __init__(self, lane_locations=LANE_LOCATIONS):
    self.lane_locations = lane_locations
    self.lanes = {k:ItemLaneStepper(pins) for k in self.lane_locations}
    def setup_lane_motors():
      """Helper function to instantiate lane motors."""
      pass
    def setup_platform_motors():
      """Helper function to instantiate plaform motors"""
      pass
  
  def move_platform(self, row) -> None:
    """Controls motors to move platform to desired row"""
    pass

  def release_item(self, item) -> None:
    """Controls motor to drop item"""
    motor = self.lanes[item.location]
    # select motor to control based on item location
    initial_weight = 0  # weight read from sensors prior to item drop
    # keep rotating motors until item registered
    weight = 0  # weight read from sensors
    while (weight == initial_weight):
      motor.rotate(direction="cw", speed=10, rotations=1)  # NOTE: change rotation to number needed to move belt a distance = space between notches
      time.sleep(2)  # give item time to fall/settle
  
def parse_payload(payload):
  """Reads JSON payload and organizes information in Item dataclass.
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
  row_num = 1
  sorted_order = []
  while len(sorted_order) < len(order):
    for i in order:
      if i.row == row_num:
        sorted_order.append(i)
    row_num += 1
  return sorted_order
           
def dispense(sorted_order) -> None:
  """Dispenses all items in order. Returns success or failure"""
  # check weight and volume as you go
  weight = 0  # current weight on platform
  volume = 0  # total volume of items on platform
  # do dispensing and update weight and volume
  pos = 0  # position in order
  tol = 0 # tolerance of weight difference to confirm successful item drop
  while(pos < len(sorted_order)):
    item = sorted_order[pos]
    # move platform to correct row
    while(item.quantity > 0):
      # dispense item
      # check that platform weight changed
      weight_change = 0 # platform_weight - weight
      if weight_change == 0:
        # try dispensing again
        # if fail second time:
          SUCCESS = False   
      # check if platform weight or volume exceeded
      if weight >= MAX_WEIGHT or volume >= PLAT_VOL:
        # pause addition of items and move platform to center to give items to user
        # check that items removed
        ItemsReceived()
        # reset variables
        weight = 0
        volume = 0
      item.quantity -= 1
    pos += 1


def ItemsReceived() -> bool:
  """Checks that items have been removed from the platform and the weight has returned to initial"""
  tolerance = 0.1  # acceptable variation from the initial in grams
  weight = 1 # get weight from sensors here
  while (weight > BASE_WEIGHT + tolerance):
    # wait some amount of time and then check weight again
    time.sleep(3)
    weight =  1 # get weight from sensors
  return True
  
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
  # dispense(sorted_order)
  # publish success or failure message here ***
 
  

client = mqtt.Client()
client.username_pw_set("lenatest", "password")
client.on_connect = on_connect
client.on_message = on_message

client.connect("ec2-3-87-77-241.compute-1.amazonaws.com", 1884, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()
