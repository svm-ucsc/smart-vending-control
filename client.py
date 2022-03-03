import paho.mqtt.client as mqtt
import json

# CLIENT_ID will be defined globally, each 
# physical Pi will have its own CLIENT_ID
CLIEND_ID = "testid"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    # [CLIENT_ID]/vend will tell the Pi when to vend an item
    client.subscribe(CLIEND_ID + "/vend")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    # The payload is in JSON
    payload = json.loads(msg.payload)

    # Examples of how to get the data/what it looks like
    order_id = payload['orderID']
    print("order_id: " + order_id)

    order_list = payload['orderList']
    print("order_list: " + str(order_list))

    first_item_id = list(order_list.keys())[0]
    print("first_item_id: " + first_item_id)

    first_item_quantity = list(order_list.values())[0]
    print("first_item_quantity: " + str(first_item_quantity))

    # Once vending is complete, construct the response object
    # itemsDispensed MIGHT now be the original order list,
    # if some items failed to dispense
    response = {
        'orderID': order_id,
        'success': True,
        'itemsDispensed': order_list
    }
    
    # [CLIENT_ID]/confirm is for confirming orders
    client.publish(CLIEND_ID + "/confirm", json.dumps(response))

client = mqtt.Client()
client.username_pw_set("lenatest", "password")
client.on_connect = on_connect
client.on_message = on_message

client.connect("ec2-3-87-77-241.compute-1.amazonaws.com", 1884, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()