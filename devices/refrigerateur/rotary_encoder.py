#
# Auteur : fredthx
#
# Class for rotary Encoder
#
# Notes :
# L'ESP8266 a tendance à executer plusieurs intéruption quand le front tombe ou monte si la pente est trop élevée
# Comme il faut mettre des capacités pour supprimer les parasites et rebond, la pente est forcement existante
# Pente mesurée avec les filtres RC préconisés (10 kOhlms + 10nF) : 0.6ms
# On doit donc faire un soft debounce!
#

from machine import Pin

class RotaryEncoder:
    ''' A rotary encoder (ie : Bourns PEC11R)
    '''
    def __init__(self, pin_A:machine.Pin, pin_B:machine.Pin, pin_12:machine.Pin=None, step = 1, min_value = None, max_value = None, init_value = 0):
        '''
        - pin_A   :   machine.Pin output A of the rotary encoder
        - pin_B   :   machine.Pin output B of the rotary encoder
        - pin_12   :   machine.Pin output of the switch. Must be pull-up.
        '''
        self.pin_A = pin_A
        self.pin_A.init(Pin.IN)
        self.pin_B = pin_B
        self.pin_B.init(Pin.IN)
        self.pin_12 = pin_12
        self.pin_12.init(Pin.IN)
        self.step = step
        self.max_value = max_value
        self.min_value = min_value
        self.counter = init_value
        self.callback = None
        self.button_callback = None
        self.pin_A.irq(handler = self.interupt_A, trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING)
        self.last_A_value = 1
        self.last_12_value = 1

    def interupt_A(self, pin):
        '''When pin_A is falling
        '''
        if pin.value()!=self.last_A_value: #Debounce
            self.last_A_value = pin.value()
            if pin.value()==0:
                if self.pin_B.value(): # counterclockwise
                    self.counter -= self.step
                    if self.min_value is not None and self.counter < self.min_value:
                        self.counter = self.min_value
                    if self.callback:
                        self.callback(-self.step)
                else: #Clockwise
                    self.counter += self.step
                    if self.max_value is not None and self.counter > self.max_value:
                        self.counter = self.max_value
                    if self.callback:
                        self.callback(self.step)

    def set_rotaty_callback(self, callback):
        '''handle callback (one argument : -1 | 1)
        Set None to unsubscribe
        '''
        self.callback = callback

    def interupt_12(self, pin):
        '''When button is pressed
        '''
        if pin.value()!=self.last_12_value: #debounce
            self.last_12_value = pin.value()
            if pin.value() == 0:
                if self.button_callback:
                    self.button_callback()

    def set_button_callback(self, callback):
        '''handle callback (None arguments)
        Set Non to unsubscribe
        '''
        self.button_callback = callback
        if callback:
            self.pin_12.irq(handler = self.interupt_12, trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING)
        else:
            self.pin_12.irq(handler = None)
    
#if __name__ == '__main__':
#    rot = RotaryEncoder(Pin(14), Pin(12), Pin(13))
#    rot.set_rotaty_callback(lambda direction:print(f"Tourne : {direction}, counter = {rot.counter}"))
