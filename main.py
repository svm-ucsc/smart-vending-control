import paho.mqtt.client as mqtt
import json
import movement.lane_stepper.build.ItemLaneSystem as ils
from movement.platform_stepper import *
from weight_sensor import *
import time 

CLIENT_ID = "pi1"

NUM_ROWS = 4  # number of rows in machine
NUM_COLS = 3  # number of columns in machine
BASE_WEIGHT = 0  # weight of inner platform on senors
MAX_WEIGHT = 14000  # maximum weight in grams of order that can be handled at one time
MAX_PLAT_VOL = 20    # total volume of available space on the platform
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
LANE_STEP_SPEED = 1  # speed of lane stepper rotations
# TODO (extra functionality): Write function to adjust rotation
# speeds based on current weight on platform and weights of items in lanes

class Item(): 
  def __init__(self, info:dict):
    self.quantity = info['quantity']  # amount to be dispensed
    self.weight = info['weight']      # weight of one unit
    self.volume = info['volume']      # volume of one unit
    self.row = info['row']
    self.column = info['column']
    self.channel = (self.row*3)-(3-self.column)

  def decrement(self):
    """Decrement item quantity and return new value"""
    self.quantity = self.quantity - 1
    return self.quantity

class Order():
  def __init__(self, ID, items:list):
    self.ID = ID
    self.items = schedule_order(items)
  
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
  
  def remove_item(self, item:Item):
    self.items.remove(Item)

class Machine():
  def __init__(self, max_plat_vol=MAX_PLAT_VOL, max_weight=MAX_WEIGHT):
    # Lane initializations
    self.lane_sys = ils.ItemLaneSystem()
    
    # Platform initializations
    self.items_on_plat = []
    self.plat_stepper = PlatformStepper(PLAT_CHANNEL)
    self.plat_vol = max_plat_vol       # maximum item volume capacity of platform
    self.plat_weight = max_weight  # maximum weight capacity of platform
    self.plat_full = False         # indicates whether platform has reached max capacity
    self.plat_location = 0         # current row location of platform

    # weight sensing initializations
    self.sensor = WeightSensor_HX711(HX711_DOUT_PIN, HX711_SDK_PIN, HX711_GAIN)
    self.sensor.calibrate()
  
  def move_platform(self, row) -> bool:
    """Controls motor to move platform to desired row"""
    pos = ROW1_POS if row == 1 else ROW2_POS if row == 2 else ROW3_POS  # desired platform position
    cur = self.plat_stepper.get_position()
    dir = 'cw' if (pos > cur) else 'ccw'
    dif = pos - cur
    num_rotate = dif if dif >= 0 else dif * -1  # number of steps
    try:
      self.plat_stepper.rotate(self, dir, PLAT_STEP_SPEED, num_rotate)
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
    next_items = set() # set of items to dispense on the same row
    while(len(order.items) > 0):
      if len(next_items == 0):
        next_items = [x for x in order.items if x.row == order.items[0].row]
        row = next_items.pop().row
      # Move platform
      if self.plat_location != row:
        try:
          assert self.move_platform(row=row) == True
        except:
          return False
      # Release order
      self.drop_items(next_items)
      # Update order
      for item in next_items:
        if item.quantity == 0:
          order.remove_item(item)

  def drop_items(self, items:list) -> None:
    """Releases an item from its item lane onto the platform"""
    if self.plat_full == True:
      self.deliver
    for item in items:
      w = self.available_weight - item.weight 
      v = self.available_space - item.volume
      if w < 0 or  v < 0:
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
    min_expected_weight = sum([item.weight for item in items]) - (tol * len(items))
    while (added_weight < min_expected_weight):
      self.lane_sys.rotate_n(channels, ['cw' for i in range(len(channels))], 1)  # TODO: Replace number of rotations with experimentally measured value
      time.sleep(1)  # give items time to fall/settle
      added_weight = self.sensor.get_grams
    self.items_on_plat.append(item)

  def deliver(self):
    """Moves platform to center and waits for user to take items"""
    self.platform_stepper.reset_position()
    self.ItemsReceived()
    self.plat_full == False

  def ItemsReceived(self) -> bool:
    """Checks that items have been removed from the platform and the weight has returned to initial"""
    tolerance = 0.1  # acceptable variation from the initial in grams  TODO: Change this to exprimentally determined value
    # TODO: Account for situation where items not received after a long period of time
    while (self.sensor.difference() > tolerance):
      # wait some amount of time and then check weight again
      time.sleep(3)
    self.items_on_plat = []
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
    order.append(Item(item_info['order_list'][i]))
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
    order = Order(parse_payload(msg.payload))
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
client.loop_forever()
