import machine, onewire, ds18x20, time
from FESPNOW.fesp_iot import FESPIot


wifi = {'ssid' : 'OLFA_PRODUCTION', 'passw' : '79073028', 'host' : '192.168.0.11'}
device = FESPIot(mqtt_base_topic = "OLFA/ROBOT/CABINES/TEMPERATURES", wifi = wifi, watchdog = 60)
ds_pin = machine.Pin(2) # D4
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

print('Found DS devices: ', ds_sensor.scan())

def read_and_send():
    '''Read and send sensor data
    '''
    ds_sensor.convert_temp()
    time.sleep_ms(750)
    for rom in ds_sensor.scan():
        topic = './%02X:%02X:%02X:%02X:%02X:%02X:%02X:%02X'%tuple(rom)
        device.mqtt.publish(topic, str(ds_sensor.read_temp(rom)))

tim = machine.Timer(-1)
tim.init(period = 10000, mode = machine.Timer.PERIODIC, callback=lambda t:read_and_send())
