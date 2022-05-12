import paho.mqtt.client as mqtt
import json

from os import path
import RPi.GPIO as GPIO
import pickle

import time 
import movement.lane_stepper.build.ItemLaneSystem as ils
from movement.platform_stepper import *
from weight_sensor import *
from weight_sensing_test import basic_tests

CLIENT_ID = "pi1"                   # Identifier for machine

NUM_ROWS = 4                        # Number of rows in machine
NUM_COLS = 3                        # Number of columns in machine

BASE_WEIGHT = 0                     # Weight of inner platform on senors
MAX_WEIGHT = 14000                  # Max weight (grams) of order that can be handled at one time
MAX_PLAT_VOL = 2000000              # Total volume of available space on the platform

SUCCESS = True                      # Indicates if order handled successfully
FAILURE = False                     # Indicates if an order fails

PLAT_CHANNEL = 0                    # Motor hat channel of platform stepper motor

HX711_DOUT_PIN = 17                 # dout GPIO pin of HX711 
HX711_SDK_PIN = 18                  # sdk GPIO pin of HX711 
HX711_GAIN = 128
WEIGHT_FILE = "wsens_state.pickle"  # Filename for storing/loading weight sensor calibration data

# Platform stepper motor positions by row
ROW1_POS = 11.8
ROW2_POS = 5.9
ZERO_POS = 0
ROW3_POS = -6

WEIGHT_VAR_TOL = 0.2                # Fraction of weight variation tolerated

PLAT_STEP_SPEED = 35                # Speed of platform stepper rotations
LANE_STEP_SPEED = 1                 # Speed of lane stepper rotations

LANE_ROTATIONS = 6                  # Number of rotations needed to dispense one item (will change)

NUM_ATTEMPTS = 2                    # Number of attempts to drop an item before giving up

MOTOR_CHANNELS = [[0, 3],
                  [1, 4],
                  [2, 5]]


# Holds all of the information related to an item that is ordered
class Item(): 
  def __init__(self, info:dict):
    self.quantity = info['quantity']  # Amount to be dispensed
    self.weight = info['weight']      # Weight of one unit
    self.volume = info['volume']      # Volume of one unit
    self.row = info['row']
    self.column = info['column']
    self.channel = MOTOR_CHANNELS[self.row-1][self.column-1]

  def decrement(self):
    """Decrement item quantity and return new value"""
    self.quantity = self.quantity - 1
    return self.quantity

  def get_lane_speed(self):
    """
    Determines the rotation speed of the item lane stepper motors based on the weight of the items
    held.
    """
    pass
  
  def get_lane_rotations(self):
    """
    Determines the expected number of rotations to drop one item given the volume of the item.
    """
    pass


class Order():
  """Holds the information associated with an order (i.e. the list of items to dispense)"""
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
    self.items = schedule_order(items)  # list of sorted items to dispense
  
  def remove_item(self, item:Item):
    """Removes an item from the list of items"""
    self.items.remove(item)

class Machine():
  """
  Wrapper class that brings together all of the hardware modules (motors, sensors) and is used
  to respond to the orders that are brought in from the backend
  """
  def __init__(self, max_plat_vol=MAX_PLAT_VOL, max_weight=MAX_WEIGHT):
    # Lane initializations
    self.lane_sys = ils.ItemLaneSystem()
    
    # Platform initializations
    self.items_on_plat = []
    self.plat_stepper = PlatformStepper(PLAT_CHANNEL)
    self.plat_vol = max_plat_vol        # Maximum item volume capacity of platform
    self.plat_weight = max_weight       # Maximum weight capacity of platform
    self.plat_full = False              # Indicates whether platform has reached max capacity
    self.plat_location = ZERO_POS              # Current row location of platform

    # move platform to zero position
    self.plat_stepper.rotate('ccw', 750, 6)
    self.plat_stepper.zero_position()

    # Weight sensor initializations/loads
    self.sensor = None

    # Required setup for pins
    GPIO.setmode(GPIO.BCM)

    # Create new sensor if we cannot load a file w/ the calibration data
    if not (path.exists(WEIGHT_FILE)):
        print("Generating weight sensor calibration...")
        self.sensor = WeightSensor_HX711(dout=HX711_DOUT_PIN, pd_sck=HX711_SDK_PIN, gain=HX711_GAIN)
        self.sensor.calibrate()
        basic_tests(3, self.sensor)
        calib_good = input("Satisfied with calibration? y/n? ")
        while (calib_good != 'y'):
          self.sensor.calibrate()
          calib_good = input("Satisfied with calibration? y/n? ")
        
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

    print("Resetting platform position...")
    self.plat_stepper.reset_position()
 
  
  def move_platform(self, row) -> bool:
    """Controls motor to move platform to desired row"""
    pos = ROW1_POS if row == 1 else ROW2_POS if row == 2 else ROW3_POS  # desired platform position
    cur = self.plat_location
    dir = 'ccw' if (pos > cur) else 'cw'
    dif = pos - cur
    num_rotate = abs(dif)  # number of rotations
    
    try:
      print("Moving the platform {} steps".format(num_rotate))
      self.plat_stepper.rotate(dir, PLAT_STEP_SPEED, num_rotate)
    except:
      print("Failed call to move platform")
      return FAILURE
    
    self.plat_location = pos
    
    return SUCCESS
    
  @property
  def available_space(self):
    """Returns the available volume of the platform"""
    used_volume = 0
    for i in self.items_on_plat:
      used_volume += i.volume
    
    return self.plat_vol - used_volume
  
  @property
  def available_weight(self):
    """Returns the available weight of the platform"""
    used_weight = 0
    for i in self.items_on_plat:
      used_weight += i.weight
    
    return self.plat_weight - used_weight
  
  def adjust_platform_speed(self):
    """
    Adjusts the speed of rotation of the platform stepper motor based on the weight on the platform.
    """
    pass

  def dispense(self, order:Order) -> bool:
    """Controls the main dispensing workflow. Given an order, rotate the platform and item lane motors to
    dispense the items according to the sorted order. Updates the order object progressively. Delivers
    the items when dispensing is complete.
    """
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
          print("Failed to move platform")
          return FAILURE
      
      # Release order
      print("Preparing to drop items")
      items_dropped = self.drop_items(next_items)
      print("Items dropped")
      
      # Update order
      for item in next_items:
        print("Updating order")
        item.decrement()
        if item.quantity == 0:
          order.remove_item(item)
        next_items = []
    
    self.deliver()
    return SUCCESS

  def drop_items(self, items:list):
    """Releases an item from its item lane onto the platform"""
    if self.plat_full == True:
      self.deliver()
    
    print("Dropping items")
    
    tol = 0 # percent tolerance of weight difference to confirm successful item drop
    #TODO adjust tolerance to be relative to the item's weight i.e. use percentage. 

    min_expected_weight = 0  
    w = self.available_weight
    v = self.available_space
    items_to_drop = []
    for item in items:
      w -= item.weight
      v -= item.volume
      if w < 0 or v < 0:
        break
      min_expected_weight += item.weight - (item.weight * WEIGHT_VAR_TOL)
      items_to_drop.append(item)
        
    added_weight = 0                    # grams of weight added onto the platform
    
    print("Checking weight sensor")
    print("Added weight: {}, min_expected_weight: {}".format(added_weight, min_expected_weight))
    
    items_dropped = []
    print("Dropping {} items".format(len(items_to_drop)))
    if (len(items_to_drop) == 1):
      if (self.single_item_drop(items_to_drop[0], NUM_ATTEMPTS) == True):
        print("Item dropped successfully")
        items_dropped.append(items_to_drop[0])

    # If items are very close in weight, don't drop them at the same time
    elif (len(items_to_drop) == 2 and abs(items_to_drop[0].weight - items_to_drop[1].weight) < 10):
      print("Dropping two items with similar weights")
      if (self.single_item_drop(items_to_drop[0], NUM_ATTEMPTS) == True):
        print("Successfully dropped first item")
        items_dropped.append(items_to_drop[0])
      if (self.single_item_drop(items_to_drop[1], NUM_ATTEMPTS) == True):
        print("Successfully dropped second item")
        items_dropped.append(items_to_drop[1])
    
    # If items have sufficient difference in weights, drop at same time
    else:      
      print("Dropping two items with different weights")
      while (added_weight < min_expected_weight):
        channels = [item.channel for item in items_to_drop]  # get motor channels
        print("About to rotate: {}".format(channels))
        dirs = ['cw' for i in range(len(channels))]
        speeds = [LANE_STEP_SPEED for i in range(len(channels))]
        num_steps = [LANE_ROTATIONS for i in range(len(channels))]
      
        self.sensor.set_prev_read(self.sensor.get_grams())
        change = 0
        while (change == 0):
          self.lane_sys.rotate_n(channels, dirs, speeds, num_steps)
          time.sleep(1)  # give items time to fall/settle
          change = self.sensor.detect_change(5)
          
        added_weight += change
        print("Initial added weight: {}".format(added_weight))
        
        # Handle scenario where only 1/2 items dropped successfully
        if (added_weight > 0 and added_weight < min_expected_weight):
          # Determine which item is stuck
          if abs(added_weight - items_to_drop[0].weight) < abs(added_weight - items_to_drop[1].weight):
            stuck_item = items_to_drop[1]
            items_dropped.append(items_to_drop[0])
            items_to_drop.remove(items_to_drop[0])
          else:
            stuck_item = items_to_drop[0]
            items_dropped.append(items_to_drop[1])
            items_to_drop.remove(items_to_drop[1])

          # Attempt to drop the stuck item
          if (self.single_item_drop(stuck_item, NUM_ATTEMPTS-1) == True):
            items_dropped.append(stuck_item)
            items_to_drop.remove(stuck_item)
    
    print("Finished dropping items")
    
    for item in items_dropped:
      self.items_on_plat.append(item)
      if (self.available_weight <= 0 or self.available_space <= 0):
        self.plat_full = True
    
    return items_dropped
  
  def single_item_drop(self, item:Item, num_tries:int)->bool:
    """Rotates a motor to drop a single item. Returns success or failure"""
    attempts = 0
    self.sensor.set_prev_read(self.sensor.get_grams())
    print("Now attempting to drop one item. Channel: {}".format(item.channel))
    while (attempts < num_tries):
      self.lane_sys.rotate(item.channel, 'cw', LANE_STEP_SPEED, LANE_ROTATIONS)
      time.sleep(1)  # settling time
      if (self.sensor.get_grams() >= item.weight - (item.weight*WEIGHT_VAR_TOL)):
        print("Item detected")
        return SUCCESS
      attempts += 1
      print("Item not detected")
    return FAILURE


  def deliver(self):
    """Moves platform to center and waits for user to take items"""
    print("Resetting platform to deliver items")
    self.plat_stepper.reset_position()
    self.ItemsReceived()
    self.plat_full = False
    return

  def ItemsReceived(self) -> bool:
    """Checks that items have been removed from the platform and the weight has returned to initial"""
    weight_on_plat = sum([item.weight - (item.weight*WEIGHT_VAR_TOL) for item in self.items_on_plat]) 
    # TODO: Account for situation where items not received after a long period of time
    print("Waiting for items to be received")
    self.sensor.set_prev_read(self.sensor.get_grams())
    while (self.sensor.detect_change(0.1) < weight_on_plat):
      # wait some amount of time and then check weight again
      print("Grams on plat: {}".format(self.sensor.get_grams()))
    
    self.items_on_plat = []
    
    print("Items received")
    return SUCCESS
  

# Define global machine object
MACHINE = Machine()

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
    try:
      order = json.loads(msg.payload)
      print("Recieved order: " + str(order))
      order_id = order['orderID']
    
      response_body = {
          "status": "SUCCESS",
          "order_id": order_id,
      }
    
      order = Order(order_id, parse_payload(msg.payload))
      print("Items in order: {}".format(order.items))
      vend_successful = MACHINE.dispense(order)
    
      # publish success message
      if(vend_successful): 
          print("Vend successful")
          client.publish(CLIENT_ID+"/order/status", payload=json.dumps(response_body), qos=1)
      else:
        print("Vend unsuccessful")
    except KeyboardInterrupt:
      GPIO.cleanup()

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


client = mqtt.Client(client_id=CLIENT_ID, clean_session=False)
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
