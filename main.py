import paho.mqtt.client as mqtt
import json
from movement.lane_stepper import *
from movement.platform_stepper import *
from weight_sensor import *
import time 
import threading

NUM_ROWS = 4  # number of rows in machine
NUM_COLS = 3  # number of columns in machine
BASE_WEIGHT = 0  # weight of inner platform on senors
MAX_WEIGHT = 14000  # maximum weight in grams of order that can be handled at one time
MAX_PLAT_VOL = 20    # total volume of available space on the platform
LANE_LOCATIONS = [(1,1), (1,2), (1,3), (2,1), (2,2), (2,3), (3,1), (3,2), (3,3)]
STEPPER_PINS = []
SENSOR_PINS = []
SUCCESS = True  # indicates if order handled successfully
PLAT_CHANNEL = 0  # motor hat channel of platform stepper motor
HX711_DOUT_PIN = 17  # dout GPIO pin of HX711 
HX711_SDK_PIN = 18  # sdk GPIO pin of HX711 
HX711_GAIN = 128
 # platform stepper motor positions by row
ROW1_POS = 0 
ROW2_POS = 0
ROW3_POS = 0
PLAT_STEP_SPEED = 1  # speed of platform stepper rotations
# TODO: Write function to adjust speed based on current weight on platform

class Item(): 
  def __init__(self, info:dict):
    self.UID = info["UID"]  # indicates order that item is a part of 
    self.name = info["name"]
    self.quantity = info["quantity"]  # amount to be dispensed
    self.weight = info["weight"]      # weight of one unit
    self.volume = info["volume"]      # volume of one unit
    self.row = info["row"]
    self.column = info["column"]

  def decrement(self):
    """Decrement item quantity and return new value"""
    self.quantity = self.quantity - 1
    return self.quantity

class Machine():
  def __init__(self, stepper_pins=STEPPER_PINS, lane_locations=LANE_LOCATIONS, \
               max_plat_vol=MAX_PLAT_VOL, max_weight=MAX_WEIGHT):
    # Lane initializations
    self.lane_locations = lane_locations
    self.lanes = {k:ItemLaneStepper(self.stepper_pins) for k in self.lane_locations}
    
    # Platform initializations
    self.items_on_plat = []
    self.plat_stepper = PlatformStepper(PLAT_CHANNEL)
    self.plat_vol = max_plat_vol       # maximum item volume capacity of platform
    self.plat_weight = max_weight  # maximum weight capacity of platform
    self.plat_full = False         # indicates whether platform has reached max capacity
    self.plat_location = 0         # current row location of platform
    self.lock = threading.Lock()

    # weight sensing initializations
    self.sensor = WeightSensor_HX711(HX711_DOUT_PIN, HX711_SDK_PIN, HX711_GAIN)
    self.sensor.calibrate()
    
    def setup_lane_motors():
      """Helper function to instantiate lane motors."""
      pass 
  
  def move_platform(self, row) -> None:
    """Controls motor to move platform to desired row"""
    pos = ROW1_POS if row == 1 else ROW2_POS if row == 2 else ROW3_POS
    cur = self.plat_stepper.get_position()
    dir = 'cw' if (pos > cur) else 'ccw'
    dif = pos - cur
    num_rotate = dif if dif >= 0 else dif * -1
    self.plat_stepper.rotate(self, dir, PLAT_STEP_SPEED, num_rotate)
    
    
  
  @property
  def available_space(self):
    used_volume = 0
    for i in self.items_on_plat:
      used_volume += i.volume
    return self.plat_vol - used_volume
  
  @property
  def available_weight(self):
    used_weight = 0
    for i in self.items_on_plat:
      used_weight += i.weight
    return self.plat_weight - used_weight

  def dispense(self, sorted_order) -> None:
    """Dispenses all items in order."""
    pos = 0  # position in sorted order
    next_items = set() # set of items to dispense on the same row
    while(pos < len(sorted_order)):
      if len(next_items == 0):
        next_items = {x for x in sorted_order if x.row == sorted_order[pos].row}
        row = list(next_items).pop().row
      if self.plat_location != row:
        self.move_platform(row=row)
      for item in next_items:
        thread = threading.Thread(target=self.drop_item, args=(item))
        thread.start()
        thread.join()
        num = item.decrement()
        # remove item from set if full quantity has been dropped
        if num == 0:
          next_items.remove(item) 
          pos += 1

  def drop_item(self, item) -> None:
    """Releases an item from its item lane onto the platform"""
    self.lock.acquire(blocking=True, timeout=- 1)
    w = self.available_weight - item.weight
    v = self.available_space - item.volume
    if self.plat_full == True or  w < 0 or  v < 0:
      self.deliver()
    elif w == 0 or v == 0:
      self.plat_full = True
    self.lock.release()

    motor = self.lanes[item.location] # motor to control based on item location
    tol = 1 # tolerance of weight difference in grams to confirm successful item drop
    # rotate motors until item registered
    while (self.sensor.detect_change() == False):
      motor.rotate(direction="cw", speed=10, rotations=1)  # NOTE: change rotation to number needed to move belt a distance = space between notches
      time.sleep(1)  # give item time to fall/settle
    self.items_on_plat.append(item)

  def deliver(self):
    """Moves platform to center and waits for user to take items"""
    self.move_platform(row=0)
    self.ItemsReceived()
    self.plat_full == False

  def ItemsReceived(self) -> bool:
    """Checks that items have been removed from the platform and the weight has returned to initial"""
    tolerance = 0.1  # acceptable variation from the initial in grams
    while (self.sensor.difference() > tolerance):
      # wait some amount of time and then check weight again
      time.sleep(3)
    self.items_on_plat = []
    return True
   
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
  machine = Machine()
  order = parse_payload(msg.payload)
  sorted_order = schedule_order(order)
  machine.dispense(sorted_order)
  # publish success or failure message here ***
 
  

client = mqtt.Client()
client.username_pw_set("lenatest", "password")
client.on_connect = on_connect
client.on_message = on_message

client.connect("ec2-3-87-77-241.compute-1.amazonaws.com", 1884, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
client.loop_forever()
