import machine, onewire, ds18x20, time, dht
from FESPNOW.fesp_iot import FESPIot


wifi = {'ssid' : 'OLFA_PRODUCTION', 'passw' : '79073028', 'host' : '192.168.0.11'}
device = FESPIot(mqtt_base_topic = "T-HOME/EXTERIEUR/", wifi = wifi, watchdog = 60)

##############
## DS18B20 ##
##############

ds_pin = machine.Pin(0) # D3
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
print('Found DS devices: ', ds_sensor.scan())

def get_ds18b20_temp():
    ds_sensor.convert_temp()
    time.sleep_ms(750)
    roms = ds_sensor.scan()
    if roms:
        return ds_sensor.read_temp(roms[0])

device.add_out_topic(topic = "T-HOME/PISCINE/temperature", callback = get_ds18b20_temp)

##############
## DHT11   ##
##############

dht_pin = machine.Pin(2) #D4
dht_sensor = dht.DHT11(dht_pin)

def get_dht_temperature():
    dht_sensor.mesure()
    return dht_sensor.temperature()

def get_dht_humidity():
    dht_sensor.mesure()
    return dht_sensor.humidity()


device.add_out_topic(topic = "./temperature", callback = get_dht_temperature)
device.add_out_topic(topic = "./humidite", callback = get_dht_humidity)

#############
## POMPE  ##
#############

pompe_pin = machine.Pin(4)

device.add_in_topic(topic="T-HOME/PISCINE/POMPE", payload = "ON", callback = lambda topic, payload : pompe_pin.on())
device.add_in_topic(topic="T-HOME/PISCINE/POMPE", payload = "OFF", callback = lambda topic, payload : pompe_pin.off())


device.run_forever()