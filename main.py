import sys
import time
import sched
import argparse
import configparser
from datetime import datetime as dt
from datetime import time as dttime
from datetime import timedelta

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
            print(self.timers)
        except configparser.NoSectionError:
            self.logPrint(f'Timers section absent in {cfgFile}')
            self.logPrint('Exiting...')
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

        self.logPrint((f'{timerName} - {"Reminder" if reminder else "Alert"}'
                       ' notification sent'))

    def refactorTimer(self) -> None:
        # Replaces time strings to DateTime Objects

        try:
            for name, timer in self.timers.items():
                time = dt.strptime(timer, '%H:%M')
                timeDtObject = dttime(time.hour, time.minute)
                self.timers[name] = dt.combine(dt.now(), timeDtObject)
            self.logPrint('Read successful')
        except ValueError:
            self.logPrint('Timer section set incorrectly')

    def generateSchedule(self, timers: dict) -> tuple:
        # timer[0] = dtObject, [1] = name: str, [2] = reminder: bool

        # Yield Reminders
        if self.remindBefore > 0:
            for name, timer in timers.items():
                reminderTime = timer - timedelta(minutes=self.remindBefore)
                if reminderTime > dt.now():
                    reminder = (reminderTime, name, True)
                    yield reminder

        # Yield Alerts
        for name, alertTimer in timers.items():
            if alertTimer > dt.now():
                alert = (alertTimer, name, False)
                yield alert

    def run(self) -> None:
        self.refactorTimer()
        schedule = self.generateSchedule(self.timers)

        self.logPrint('Schedule:')

        while True:
            try:
                timer = next(schedule)
                self.scheduler.enterabs(
                    timer[0].timestamp(), 1, self.notify, (timer[1], timer[2]))

                print((
                    ' · '
                    f'{timer[1]} {"reminder" if timer[2] else "alert"} '
                    f'at {timer[0].strftime("%H:%M")}'))

            except StopIteration:
                break

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
