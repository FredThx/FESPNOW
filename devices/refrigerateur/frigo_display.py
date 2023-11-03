import ssd1306
from pyoled import writer
from pyoled import courier20
from machine import Timer
import math

class Display:
    '''Le display du refrigerateur. C'est un OLED en i2c
    '''
    def __init__(self, i2c, screensaver = 30):
        '''i2c     :  machine.I2C object
        '''
        self.screensaver = screensaver
        self.i2c = i2c
        self.display = None
        self.writer = None
        self.crt_display()
        self.saver_timer = Timer(-1)
        self.show()
    
    def crt_display(self):
        if self.display:
            return self.display
        else:
            try:
                self.display = ssd1306.SSD1306_I2C(128,64,self.i2c)
                self.writer = writer.Writer(self.display, courier20)
                self.display.fill(0)
                self.display.show()
                return self.display
            except Exception as e:
                print(f"Error with display : {e}")
                self.display = None
                self.writer = None

    def show(self):
        '''Turn on display
        '''
        if self.crt_display():
            self.display.poweron()
            self.saver_timer.init(period = self.screensaver * 1000, mode = Timer.ONE_SHOT, callback=lambda t:self.display.poweroff())
 
    def show_temp(self, title, temperature, x, y):
        '''Display a temperature at position
        '''
        if self.crt_display():
            self.writer.set_textpos(y,x)
            if temperature>=100 or temperature <=-10:
                self.writer.printstring(" --  C")
            else:
                self.writer.printstring(f"{temperature:4.1f} C")
            self.display.text('o',x+56,y,1)
            self.display.text(title[:4], x-40, y+8)
            self.display.show()
        else:
            print(f"{title} : {temperature}")
 
    def set_temperature(self, temperature):
        '''Display the temperature
        '''
        self.show_temp("Temp", temperature, 40,20)
        
    def set_consigne(self, temperature):
        self.show_temp("Cons", temperature, 40,40)
        
    def draw_flocon(self, x, y, color = 1, l=6, angle0=0, angle1=360):
        ''' Draw a flocon
        '''
        if self.crt_display():
            for angle in range(angle0,angle1,60):
                angle = math.pi*angle/180
                point = (int(x+l*math.cos(angle)), int(y+l*math.sin(angle)))
                self.display.line(x,y,*(point+(color,)))
            self.display.show()
                