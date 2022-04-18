import paho.mqtt.client as mqtt
import json

CLIENT_ID = "lenalaptopclient"

def on_order(client, userdata, msg):

    order = json.loads(msg.payload)
    print("Recieved order: " + str(order))
    order_id = order['orderID']
    
    response_body = {
        "status": "SUCCESS",
        "order_id": order_id,
    }
    
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
    print(msg.topic+" "+str(msg.payload))

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