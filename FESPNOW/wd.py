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
        """Enable the watchdog
        """
        self.timer.init(mode = Timer.PERIODIC, period = self.timeout*1000, callback = lambda topic, payload : self.reset())

    def reset(self, tim):
        print("Watchdog timeout : machine reset!")
        machine.reset()
    
    def feed(self):
        print("Watchodg feeded.")
        self.timer.deinit()
        self.enable()

    