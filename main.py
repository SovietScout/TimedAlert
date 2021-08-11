import sys
import time
import argparse
import configparser
from datetime import datetime as dt
from datetime import timedelta
from datetime import time as dttime

from notifypy import Notify
from scheduler import Scheduler


NAME = 'Timed Alert'
ICON = 'rsc/icon.png'


class TimedAlert:
    def __init__(self):
        self.logPrint('[Press Ctrl+C to exit.]')

        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-c', '--config', nargs='?', default='config.ini',
            help='Name of config file to read from')

        args = parser.parse_args()
        cfgFile = args.config

        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(cfgFile)

        self.logPrint(f'Attempting to read from {cfgFile}.')

        try:
            self.remindBefore = config.getint('Settings', 'remindBefore')
            self.mrf = config.get('Settings', 'messageReminderFormat')
            self.mf = config.get('Settings', 'messageAlertFormat')

            self.timers = dict(config.items('Timers'))
        except configparser.NoSectionError:
            self.logPrint(
                f'{cfgFile} is either missing or has been set incorrectly.')

        self.scheduler = Scheduler()

        self.notification = Notify(
            default_notification_application_name=NAME,
            default_notification_icon=ICON
        )

    def notify(self, timerName: str, reminder: bool) -> None:
        self.notification.title = timerName

        if reminder:
            self.notification.message = self.mrf.format(
                timerKey=timerName, remindBefore=self.remindBefore)
        else:
            self.notification.message = self.mf.format(timerKey=timerName)

        self.notification.send(block=False)
        self.timersLeft -= 1
        self.logPrint((
            f'{timerName} - {"Reminder" if reminder else "Alert"}'
            ' notification sent.'))

    def logPrint(self, value: str) -> None:
        # 2021-08-10 19:25:00 {value}
        print(f'{dt.now().strftime("%Y-%m-%d %H:%M:%S")} {value}')

    def refactorTimer(self, timers: dict) -> dict:
        # Converts time strings to DateTime Objects
        actionTimeDT = {}

        try:
            for name, timer in timers.items():
                action = dt.strptime(timer, '%H:%M')
                actionTime = dttime(action.hour, action.minute)
                actionTimeDT[name] = dt.combine(dt.now(), actionTime)
            self.logPrint('Read successful.')
        except ValueError:
            self.logPrint('Timer section set incorrectly.')

        return actionTimeDT

    def generateSchedule(self, timers: dict) -> list:
        schedule = []

        # Append Reminders
        if self.remindBefore > 0:
            for name, timer in timers.items():
                actionTime = timer - timedelta(minutes=self.remindBefore)
                if actionTime > dt.now():
                    reminder = (name, actionTime, True)
                    schedule.append(reminder)

        # Append Alerts
        for name, timer in timers.items():
            if timer > dt.now():
                alert = (name, timer, False)
                schedule.append(alert)

        return schedule

    def run(self):
        rfTimers = self.refactorTimer(self.timers)
        schedule = self.generateSchedule(rfTimers)

        self.timersLeft = len(schedule)

        for timer in schedule:
            self.scheduler.once(
                timer[1], self.notify,
                kwargs={'timerName': timer[0], 'reminder': timer[2]})

        try:
            while True:
                if self.timersLeft > 0:
                    self.scheduler.exec_jobs()
                    time.sleep(1)
                else:
                    self.logPrint('No more jobs left.')
                    break
        except KeyboardInterrupt:
            self.logPrint('Ctrl+C pressed.')
        finally:
            self.logPrint('Exiting.')
            sys.exit()


if __name__ == "__main__":
    alert = TimedAlert()
    alert.run()
    # TODO change app icon [Notify-py does not support it]
    # TODO add QoL features like time until next notification, etc.
