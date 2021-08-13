import sched
import time
from datetime import datetime as dt


class TimerScheduler:
    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        pass

    def schedule(self, dtObject: dt, func, *args):
        self.scheduler.enterabs(
            dtObject.timestamp(), 1, func, args)

    def start(self) -> None:
        self.scheduler.run()

    def cancel(self) -> None:
        self.scheduler.cancel()

    def getQueue(self) -> list:
        return self.scheduler.queue
