import neopixel
from machine import Pin
import random, json, time
from FESPNOW.en_client import *

p5 = Pin(5,Pin.OUT)
n = neopixel.NeoPixel(p5, 104)

mqtt = ENClient8266()

def set_leds(topic, payload):
    payload = json.loads(payload)
    print(payload)
    i = payload['pos']
    for led in payload['leds']:
        n[i]=led
        i+=1
    n.write()

mqtt.subscribe("ESP-NOW/leds",set_leds)



def set_leds2(topic, payload):
    print(payload)
    pos = payload[0]+256*payload[1]
    for i in range(2, len(payload),3):
        n[pos+i//3]=(payload[i], payload[i+1],payload[i+2])
    n.write()


mqtt.subscribe("ESP-NOW/leds2",set_leds2)

def write_touch(t,v):
    '''t : n° de la zone : 0-1-2
        v : leur de luminosité (1 - 50)
    '''
    color = [0,0,0]
    color[t] = v
    n[t*3] = color
    n[t*3+1] = [2*x for x in color]
    n[t*3+2] = color
    n.write()

touches = [
    Pin(15,Pin.IN),
    Pin(13,Pin.IN),
    Pin(12,Pin.IN)
    ]

def handler_touch(pin):
    for i, _pin in enumerate(touches):
        if _pin == pin:
            mqtt.publish(f"ESP-NOW/TOUCH{i+1}",str(pin.value()))
            write_touch(i,50)
            time.sleep(1)
            write_touch(i,1)
            break


for i, pin in enumerate(touches):
    pin.irq(trigger=3,handler = handler_touch)
    write_touch(i,1)

mqtt.subscribe("ESP-NOW/led_run",lambda topic, payload:run(payload))

def run(payload):
    '''payload = bytes
    '''
    l = len(payload)//3
    for i in range(10,len(n)-l):
        n[i] = (0,0,0)
        for j in range(l):
            color = [0,0,0]
            for ic in range(3):
                color[ic]=payload[j*3+ic]
            n[i+j+1]=color
        n.write()
        time.sleep(0.01)
    for j in range(l):
        n[len(n)-j-1]=(0,0,0)
    n.write()

#mqtt.loop_forever()