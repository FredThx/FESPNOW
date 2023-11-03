# main.py -- put your code here!
print("Le PY-réfrigérateur!")
print("by fredthx")
print()
from machine import Pin, I2C, Timer, WDT
import onewire, ds18x20, time
from rotary_encoder import RotaryEncoder
from frigo_display import Display
from json_config import JsonConfig

#Config
config = JsonConfig()
consigne = config.read('consigne') or 5.0

#Rotary encoder
rot = RotaryEncoder(Pin(21), Pin(20), Pin(22), init_value = consigne, min_value = 0, max_value = 15, step = 0.5) # D5, D6, D7

#Display
i2c = I2C(1, sda = Pin(26), scl=Pin(27)) 
display = Display(i2c)
display.set_consigne(rot.counter)

#Capteur temperature
ds_sensor = ds18x20.DS18X20(onewire.OneWire(Pin(19)))
print('Found DS devices: ', ds_sensor.scan())

def get_temp():
    ds_sensor.convert_temp()
    time.sleep_ms(750)
    roms = ds_sensor.scan()
    #gc.collect()
    if roms:
        return ds_sensor.read_temp(roms[0])
# relay
relay = Pin(5)
relay.init(Pin.OUT)
relay.off()


#Callbacks
def rot_change(direction):
    display.show()
    display.set_consigne(rot.counter)
rot.set_rotaty_callback(rot_change)
rot.set_button_callback(display.show)



#main loop
def main_loop(tim = None):
    try:
        temperature = get_temp()
    except Exception as e:
        print(f"Error with temperature sensor : {e}")
    else:
        if temperature:
            display.set_temperature(temperature)
            if temperature > rot.counter + 2:
                relay.on()
                display.draw_flocon(100,10)
            elif temperature < rot.counter - 2:
                relay.off()
                display.draw_flocon(100,10, 0)
    if rot.counter != config.get('consigne'):
        config.set('consigne', rot.counter)
        config.save()

#Watchdog (pour avoir le temps de breaker : on attends 30 secondes )
wdt = None

print("Run main loop")
start_counter = 0
while True:
    main_loop()
    if wdt:
        wdt.feed()
    time.sleep(1) # 1 seconde
    if wdt:
        wdt.feed()
    if not wdt:
        start_counter += 1
        if start_counter == 30:
            print("wdt start...")
            wdt = WDT(timeout = 5000)