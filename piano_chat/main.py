import neopixel
from machine import Pin, Timer
import random, json, time
from FESPNOW.fesp_iot import FESPIot


class PianoChat(FESPIot):

    def __init__(self):
        super().__init__("T-HOME/PIANO-CHAT", watchdog=5*60)
        p5 = Pin(5,Pin.OUT)
        self.leds = neopixel.NeoPixel(p5, 104)
        self.mqtt.subscribe("./leds2",self.set_leds2)
        self.touches = [
            Pin(15,Pin.IN),
            Pin(13,Pin.IN),
            Pin(12,Pin.IN)
            ]
        self.touches_values = [p.value() for p in self.touches]
        for i, pin in enumerate(self.touches):
            pin.irq(trigger=3,handler = self.handler_touch)
            self.write_touch(i,1)
        self.mqtt.subscribe("./led_run",lambda topic, payload:self.run(payload))


    def set_leds2(self, topic, payload):
        print(payload)
        pos = payload[0]+256*payload[1]
        for i in range(2, len(payload),3):
            self.leds[pos+i//3]=(payload[i], payload[i+1],payload[i+2])
        self.leds.write()

    def write_touch(self,t,v):
        '''t : n° de la zone : 0-1-2
            v : leur de luminosité (1 - 50)
        '''
        color = [0,0,0]
        color[t] = v
        self.leds[t*3] = color
        self.leds[t*3+1] = [2*x for x in color]
        self.leds[t*3+2] = color
        self.leds.write()


    def handler_touch(self, pin):
        for i, _pin in enumerate(self.touches):
            if _pin == pin and pin.value != self.touches_values[i]:
                self.touches_values[i] = pin.value()
                self.mqtt.publish(f"./TOUCH{i+1}",str(pin.value()))
                self.write_touch(i,50)
                time.sleep(1)
                self.write_touch(i,1)
                break

    def run(self, payload):
        '''payload = bytes
        Ecrit sur le ruban les données à partir de la led n° 10
        Puis scroll le motif jusqu'au bout.
        '''
        l = len(payload)//3
        for i in range(10,len(self.leds)-l):
            self.leds[i] = (0,0,0)
            for j in range(l):
                color = [0,0,0]
                for ic in range(3):
                    color[ic]=payload[j*3+ic]
                self.leds[i+j+1]=color
            self.leds.write()
            time.sleep(0.01)
        for j in range(l):
            self.leds[len(self.leds)-j-1]=(0,0,0)
        self.leds.write()

piano_chat = PianoChat()