import sys
import time
import sched
import argparse
import configparser
from datetime import datetime as dt
from datetime import timedelta
from datetime import time as dttime

from notifypy import Notify


NAME = 'Timed Alert'
ICON = 'rsc/icon.png'


class TimedAlert:
    def __init__(self):
        self.logPrint('[Press Ctrl+C to exit]')

        self.remindBefore = 5
        self.mrf = '{timerKey} starts in {remindBefore} minutes'
        self.mf = '{timerKey} has started'

        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-c', '--config', nargs='?', default='config.ini',
            help='Path to custom config file')

        args = parser.parse_args()
        cfgFile = args.config

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(cfgFile)

        self.logPrint(f'Attempting to read from {cfgFile}')

        # Load settings
        try:
            self.remindBefore = config.getint('Settings', 'remindBefore')
            self.mrf = config.get('Settings', 'messageReminderFormat')
            self.mf = config.get('Settings', 'messageAlertFormat')

        except (configparser.NoSectionError,
                configparser.NoOptionError):
            # Proceeds with default settings
            pass

        # Load Timers
        try:
            self.timers = dict(config.items('Timers'))
        except configparser.NoSectionError:
            self.logPrint(f'Timers section absent in {cfgFile}')
            self.logPrint('Exiting')
            sys.exit()

        self.scheduler = sched.scheduler(time.time, time.sleep)

        self.notification = Notify(
            default_notification_application_name=NAME,
            default_notification_icon=ICON
        )

    def logPrint(self, value: str) -> None:
        # 2021-08-10 19:25:00 {value}
        print(f'{dt.now().strftime("%Y-%m-%d %H:%M:%S")} {value}')

    def notify(self, timerName: str, reminder: bool) -> None:
        self.notification.title = timerName

        if reminder:
            self.notification.message = self.mrf.format(
                timerKey=timerName, remindBefore=self.remindBefore)
        else:
            self.notification.message = self.mf.format(timerKey=timerName)

        self.notification.send(block=False)

        self.timersLeft -= 1
        self.logPrint((f'{timerName} - {"Reminder" if reminder else "Alert"}'
                       ' notification sent'))

    def refactorTimer(self, timers: dict) -> dict:
        # Converts time strings to DateTime Objects
        actionTimeDT = {}

        try:
            for name, timer in timers.items():
                action = dt.strptime(timer, '%H:%M')
                actionTime = dttime(action.hour, action.minute)
                actionTimeDT[name] = dt.combine(dt.now(), actionTime)
            self.logPrint('Read successful')
        except ValueError:
            self.logPrint('Timer section set incorrectly')

        return actionTimeDT

    def generateSchedule(self, timers: dict) -> list:
        # timer[0] = dtObject, [1] = name: str, [2] = reminder: bool
        schedule = []

        # Append Reminders
        if self.remindBefore > 0:
            for name, timer in timers.items():
                actionTime = timer - timedelta(minutes=self.remindBefore)
                if actionTime > dt.now():
                    reminder = (actionTime, name, True)
                    schedule.append(reminder)

        # Append Alerts
        for name, timer in timers.items():
            if timer > dt.now():
                alert = (timer, name, False)
                schedule.append(alert)

        return schedule

    def run(self) -> None:
        rfTimers = self.refactorTimer(self.timers)
        schedule = self.generateSchedule(rfTimers)

        self.timersLeft = len(schedule)

        self.logPrint('Schedule:')

        for timer in schedule:
            self.scheduler.enterabs(
                timer[0].timestamp(), 1, self.notify, timer[1], timer[2]
            )

            # {timerKey} {reminder/alert} at {dtObject timestamp}
            print((
                ' · '
                f'{timer[1]} {"reminder" if timer[2] else "alert"}'
                f' at {timer[0].strftime("%H:%M")}'))

        try:
            self.scheduler.run()
            self.logPrint('No more timers left')
        except KeyboardInterrupt:
            self.logPrint('Ctrl+C pressed')
        finally:
            self.logPrint('Exiting...')
            sys.exit()


if __name__ == "__main__":
    alert = TimedAlert()
    alert.run()
