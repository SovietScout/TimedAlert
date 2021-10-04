import sys
import time
import sched
import argparse
import configparser
from datetime import timedelta
from datetime import datetime as dt
from datetime import time as dttime

from notifypy import Notify


NAME = 'Timed Alert'
ICON = 'rsc/icon.png'


class TimedAlert:
    def __init__(self):
        self.logPrint('[Press Ctrl+C to exit]')

        self.remindBefore = 5
        self.mtf = '{timerKey}'
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
            self.mtf = config.get('Settings', 'messageTitleFormat')
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
            self.logPrint('Exiting...')
            sys.exit()

        self.scheduler = sched.scheduler(time.time, time.sleep)

        self.notification = Notify(
            default_notification_application_name=NAME,
            default_notification_icon=ICON
        )

    def logPrint(self, value: str) -> None:
        # 2021-08-10 08:30:00 {value}
        # print(f'{dt.now().strftime("%Y-%m-%d %H:%M:%S")} {value}')

        # 08:30:00 {value}
        print(f'{dt.now().strftime("%H:%M:%S")} {value}')

    def notify(self, timerName: str, reminder: bool) -> None:
        self.notification.title = self.mtf.format(timerKey=timerName)

        if reminder:
            self.notification.message = self.mrf.format(
                timerKey=timerName, remindBefore=self.remindBefore)
        else:
            self.notification.message = self.mf.format(timerKey=timerName)

        self.notification.send(block=False)

        self.logPrint((f'{timerName} - {"Reminder" if reminder else "Alert"}'
                       ' notification sent'))

    def generateSchedule(self) -> tuple:
        # timer [0] = dtObject, [1] = (timerName: str, reminder: bool)

        try:
            for name, timer in self.timers.items():
                # Replaces time strings with Time objects
                time = dt.strptime(timer, '%H:%M')
                timeDT = dttime(time.hour, time.minute)

                # Yield Reminders
                if self.remindBefore > 0:
                    timer = dt.combine(dt.now(), timeDT)
                    reminderTime = timer - timedelta(minutes=self.remindBefore)
                    if reminderTime > dt.now():
                        reminder = (reminderTime, (name, True))
                        yield reminder

                # Yield Alert
                timer = dt.combine(dt.now(), timeDT)
                if timer > dt.now():
                    alert = (timer, (name, False))
                    yield alert

        except ValueError:
            self.logPrint('Timer section set incorrectly')

    def run(self) -> None:
        schedule = self.generateSchedule()

        self.logPrint('Schedule:')

        while True:
            try:
                timer = next(schedule)
                self.scheduler.enterabs(
                    timer[0].timestamp(), 1, self.notify, timer[1])

                print((
                    ' | '
                    f'{timer[1][0]} {"reminder" if timer[1][1] else "alert"} '
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
    timedAlert = TimedAlert()
    timedAlert.run()
