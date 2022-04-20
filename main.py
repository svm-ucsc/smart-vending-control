import paho.mqtt.client as mqtt
import json

import os.path
from os import path
import RPi.GPIO as GPIO
import pickle

import time 
import movement.lane_stepper.build.ItemLaneSystem as ils
from movement.platform_stepper import *
from weight_sensor import *

CLIENT_ID = "pi1"                   # Identifier for machine

NUM_ROWS = 4                        # Number of rows in machine
NUM_COLS = 3                        # Number of columns in machine

BASE_WEIGHT = 0                     # Weight of inner platform on senors
MAX_WEIGHT = 14000                  # Max weight (grams) of order that can be handled at one time
MAX_PLAT_VOL = 20                   # Total volume of available space on the platform

SUCCESS = True                      # Indicates if order handled successfully

PLAT_CHANNEL = 0                    # Motor hat channel of platform stepper motor

HX711_DOUT_PIN = 17                 # dout GPIO pin of HX711 
HX711_SDK_PIN = 18                  # sdk GPIO pin of HX711 
HX711_GAIN = 128
WEIGHT_FILE = "wsens_state.pickle"  # Filename for storing/loading weight sensor calibration data

# Platform stepper motor positions by row
ROW1_POS = 20 
ROW2_POS = 30
ROW3_POS = 40

PLAT_STEP_SPEED = 1000              # Speed of platform stepper rotations
LANE_STEP_SPEED = 1                 # Speed of lane stepper rotations

# TODO (extra functionality): Write function to adjust rotation
# speeds based on current weight on platform and weights of items in lanes


# Holds all of the information related to an item that is ordered
class Item(): 
  def __init__(self, info:dict):
    self.quantity = info['quantity']  # Amount to be dispensed
    self.weight = info['weight']      # Weight of one unit
    self.volume = info['volume']      # Volume of one unit
    self.row = info['row']
    self.column = info['column']
    self.channel = 1                  #(info['row']*3)-(3-info['column'])

  def decrement(self):
    """Decrement item quantity and return new value"""
    self.quantity = self.quantity - 1
    return self.quantity


# Holds all of the information needed to process an order (i.e. a set of items to dispense)
class Order():
  def __init__(self, ID, items:list):
    
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
    
    self.ID = ID
    self.items = schedule_order(items)
  
  def remove_item(self, item:Item):
    self.items.remove(item)


# Wrapper class that brings together all of the hardware modules (motors, sensors) and is used
# to respond to the orders that are brought in from the backend
class Machine():
  def __init__(self, max_plat_vol=MAX_PLAT_VOL, max_weight=MAX_WEIGHT):
    # Lane initializations
    self.lane_sys = ils.ItemLaneSystem()
    
    # Platform initializations
    self.items_on_plat = []
    self.plat_stepper = PlatformStepper(PLAT_CHANNEL)
    self.plat_vol = max_plat_vol        # Maximum item volume capacity of platform
    self.plat_weight = max_weight       # Maximum weight capacity of platform
    self.plat_full = False              # Indicates whether platform has reached max capacity
    self.plat_location = 0              # Current row location of platform

    # Weight sensor initializations/loads
    self.sensor = None

    # Required setup (can we put this in the object?)
    GPIO.setmode(GPIO.BCM)

    # Create new sensor if we cannot load a file w/ the calibration data
    if not (path.exists(WEIGHT_FILE)):
        print("Generating weight sensor calibration...")
        self.sensor = WeightSensor_HX711(dout=HX711_DOUT_PIN, pd_sck=HX711_SDK_PIN, gain=HX711_GAIN)
        self.sensor.calibrate()
        
        pl_file = open(WEIGHT_FILE, 'ab')
        pickle.dump(self.sensor, pl_file)
        pl_file.close()
    else:
        print("Loading existing weight sensor calibration...")
        pl_file = open(WEIGHT_FILE, 'rb')
        self.sensor = pickle.load(pl_file)

        # In order to make sure that the loaded state is usable, we need to setup the
        # GPIO pins for the sensor before continuing
        GPIO.setup(self.sensor.PD_SCK, GPIO.OUT)
        GPIO.setup(self.sensor.DOUT, GPIO.IN)

        pl_file.close()
 
  
  def move_platform(self, row) -> bool:
    """Controls motor to move platform to desired row"""
    pos = ROW1_POS if row == 1 else ROW2_POS if row == 2 else ROW3_POS  # desired platform position
    cur = self.plat_stepper.get_position()
    dir = 'cw' if (pos > cur) else 'ccw'
    dif = pos - cur
    num_rotate = dif if dif >= 0 else dif * -1  # number of steps
    
    try:
      print("Moving the platform {} steps".format(num_rotate))
      self.plat_stepper.rotate(dir, PLAT_STEP_SPEED, 10)
    except:
      return False
    
    self.plat_location = row
    
    return True
    
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

  def dispense(self, order:Order) -> None:
    next_items = []
    
    while(len(order.items) > 0):
      if len(next_items) == 0:
        row = order.items[0].row
        next_items = [x for x in order.items if x.row == row]
      
      # Move platform
      print("Items to drop: {}".format(next_items))
      if self.plat_location != row:
        print("About to try to move the platform")
        try:
          assert self.move_platform(row=row) == True
        except:
          return False
      
      # Release order
      print("Preparing to drop items")
      self.drop_items(next_items)
      print("Items dropped")
      
      # Update order
      for item in next_items:
        print("Updating order")
        if item.quantity == 0:
          order.remove_item(item)
    
    self.deliver()

  def drop_items(self, items:list) -> None:
    """Releases an item from its item lane onto the platform"""
    print("Dropping items")
    if self.plat_full == True:
      self.deliver
    
    for item in items:
      w = self.available_weight - item.weight 
      v = self.available_space - item.volume
      
      if w < 0 or  v < 0:
        print("Not enough available weight or space. Preparing to deliver")
        self.deliver()
      elif w == 0 or v == 0:
        self.plat_full = True
    
    channels = [item.channel for item in items]  # get motor channels
    
    tol = 1 # tolerance of weight difference in grams to confirm successful item drop
    #TODO adjust tolerance to be relative to the item's weight i.e. use percentage. 
    # Perhaps it should be relative only to the weight of the smallest item

    #TODO use weight sensors to determine which of the items has fallen to properly account for stuck items. *******************
    #TODO choose a number of iterations before giving up if dispensing unsuccessful
    self.sensor.set_prev_read(self.sensor.get_grams())
    added_weight = 0  # grams of weight added onto the platform
    min_expected_weight = 100000#sum([item.weight for item in items]) - (tol * len(items))
    
    print("Checking weight sensor")
    print("Number of channels: ", len(channels))
    print("Added weight: {}, min_expected_weight: {}".format(added_weight, min_expected_weight))
    
    while (added_weight < min_expected_weight):
      print("About to rotate: {}".format(channels))
      dir = ['cw' for i in range(len(channels))]
      speeds = [LANE_STEP_SPEED for i in range(len(channels))]
      num_steps = [20 for i in range(len(channels))]
      self.lane_sys.rotate_n(channels, dir , speeds, num_steps)  # TODO: Replace number of rotations with experimentally measured value
      time.sleep(1)  # give items time to fall/settle
      #added_weight = self.sensor.get_grams
    
    print("Weight successfully registered")
    
    for item in items:
      self.items_on_plat.append(item)

  def deliver(self):
    """Moves platform to center and waits for user to take items"""
    print("Resetting platform to deliver items")
    self.platform_stepper.reset_position()
    self.ItemsReceived()
    self.plat_full == False

  def ItemsReceived(self) -> bool:
    """Checks that items have been removed from the platform and the weight has returned to initial"""
    tolerance = 0.1  # acceptable variation from the initial in grams  TODO: Change this to exprimentally determined value
    # TODO: Account for situation where items not received after a long period of time
    print("Waiting for items to be received")
    
    while (self.sensor.difference() > tolerance):
      # wait some amount of time and then check weight again
      time.sleep(3)
    
    self.items_on_plat = []
    
    print("Items received")
    return True
  
  def item_stuck(item, channel):
    """Handles stuck item situation"""
    pass


def parse_payload(payload):
  """Reads JSON payload and organizes information in Item dataclass.
  Returns a list of item objects.
  """
  order = []
  item_info = json.loads(payload)
  order_ID = item_info['orderID']
  
  for i in item_info['orderList']:
    order.append(Item(item_info['orderList'][i]))
  
  return order  

def on_order(client, userdata, msg):

    order = json.loads(msg.payload)
    print("Recieved order: " + str(order))
    order_id = order['orderID']
    
    response_body = {
        "status": "SUCCESS",
        "order_id": order_id,
    }
    
    machine = Machine()
    order = Order(order_id, parse_payload(msg.payload))
    print("Items in order: {}".format(order.items))
    machine.dispense(order)

    vend_successful = True
    if(vend_successful): 
        client.publish(CLIENT_ID+"/order/status", payload=json.dumps(response_body), qos=1)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(CLIENT_ID+"/order/vend")
    connectStatus = "READY"
    client.publish(CLIENT_ID+"/status", payload=json.dumps({"status": connectStatus}), qos=2)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
  """Processes and dispenses order. Returns success or failure message upon completion
  Published message consists of UUID for order and indication of success or failure
  """
  print(msg.topic+" "+str(msg.payload))
  
  # publish success or failure message here ***
 
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    """Processes and dispenses order. Returns success or failure message upon completion
    Published message consists of UUID for order and indication of success or failure
    """
    print(msg.topic+" "+str(msg.payload))
    machine = Machine()
    order = Order(parse_payload(msg.payload))
    machine.dispense(order)
    # publish success or failure message here ***


client = mqtt.Client(client_id=CLIENT_ID,clean_session=False)
client.username_pw_set("lenatest", "password")
client.on_connect = on_connect
client.on_message = on_message

client.will_set(CLIENT_ID+"/status", payload=json.dumps({"status": "LWT"}), qos=2)

client.connect("ec2-3-87-77-241.compute-1.amazonaws.com", 1884, 60)

client.message_callback_add(CLIENT_ID+"/order/vend", on_order)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
try:
  client.loop_forever()
except KeyboardInterrupt:
  GPIO.cleanup()
