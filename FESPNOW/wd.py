from machine import Timer
import machine


class WDT:
    """A soft Watchdog
    """

    def __init__(self, timeout = 10):
        """timeout      :   secondes
        """
        self.timeout = timeout
        self.timer = Timer(-1)

    def enable(self):
        """Enablme the watchdog
        """
        self.timer.init(mode = Timer.PERIODIC, period = self.timeout*1000, callback = self.reset)

    def reset(self, tim):
        machine.reset()
    
    def feed(self):
        self.timer.deinit()
        self.enable()

    