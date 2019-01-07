#!/usr/bin/env python

# This file must be copy into .config/autostart folder
# mv ~/scripts/moveYourAss.py ~/.config/autostart/
# sudo dnf install dbus-python-devel
#
# In a file named as you want with extension .desktop in  ~/.local/share/applications
#
#[Desktop Entry]
# Encoding=UTF-8
# Name=Move Your Ass
# Exec=python /home/jeremie/scripts/moveYourAss/moveYourAss.py --logfile /home/jeremie/logAll.txt
# Icon=/usr/share/icons/Adwaita/32x32/emotes/face-laugh.png
# Type=Application
# Categories=Wellness;

import dbus
import dbus.mainloop.glib
import datetime, threading
import gi
import os
import time
import sys
import getopt
# import logging
# import logging.handlers
import syslog

gi.require_version('Notify', '0.7')
from gi.repository import Notify
from gi.repository import GObject

LOGIN_VALUE   = 0
LOGOUT_VALUE  = 1
WATCHING_TIME = 2400000 # in ms -- 40 minutes
LOCK_SCREEN   = 1 # if lock screen is set, then after WATCHING_TIME, the screen will be lock

#watcher must be called after callback defintion but before use.
watcher = -1
#coffeeWatcher is used to lock on coffee request
coffeeWatcher = -1
#homeWatcher is used to lock on home request
homeWatcher = -1
# set activity time at startup in order to have the right time at the first logout
activityTime = time.time()
# log file
logfile=""
#A syslog logger
logger = -1


#log activityTime in file
def log():
  global activityTime
  global logfile

  if(logfile != ""):
    try:
      f = open(logfile, 'a')
      f.write("%s --> %s\n" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), str(datetime.timedelta(seconds=activityTime))))
      f.close()
    except IOError:
      print "Could not use file: %s" % logfile

# message displaying.
def message():
  global watcher
  watcher = -1

  stopSitting=Notify.Notification.new("Stop sitting", "Move your ass", "dialog-information")
  stopSitting.show()

  # lock screen
  os.system('gnome-screensaver-command -l')

def coffeeMessage():
  global coffeeWatcher
  coffeeWatcher = -1

  coffeeNotif=Notify.Notification.new("Coffee Time", "Go take a coffee", "dialog-information")
  coffeeNotif.show()

  # lock screen after 10 seconds
  time.sleep(10)
  os.system('gnome-screensaver-command -l')

def homeMessage():
  global homeWatcher
  homeWatcher = -1

  homeNotif=Notify.Notification.new("End of the day", "Go take a ride", "dialog-information")
  homeNotif.show()

  # lock screen after 30 seconds
  time.sleep(30)
  os.system('gnome-screensaver-command -l')

# message displaying.
def displayTime():
  global activityTime

  actNotification=Notify.Notification.new("Previous activity time", "%s"% str(datetime.timedelta(seconds=activityTime)), "dialog-information")
  actNotification.show()

  #log
  log()

  activityTime = 0

# Stop the timer, if user is logout
def stopTimer():
  global watcher
  global coffeeWatcher
  global homeWatcher

  if(watcher != -1):
    syslog.syslog(syslog.LOG_INFO, "[stopTimer] remove periodic timer")
    GObject.source_remove(watcher)
    watcher = -1;

  if(coffeeWatcher != -1):
    syslog.syslog(syslog.LOG_INFO, "[stopTimer] remove coffee timer")
    GObject.source_remove(coffeeWatcher)
    coffeeWatcher = -1;

  if(homeWatcher != -1):
    syslog.syslog(syslog.LOG_INFO, "[stopTimer] remove home timer")
    GObject.source_remove(homeWatcher)
    homeWatcher = -1;

# A new login from user is detected start the timer
def login():
  syslog.syslog(syslog.LOG_INFO, "[login] enter")
  global watcher
  global coffeeWatcher
  global homeWatcher
  global activityTime
  if (LOCK_SCREEN == 1):
    syslog.syslog(syslog.LOG_INFO, "[login] add periodic timer: " + str(int(WATCHING_TIME / 1000)) + " s")
    watcher = GObject.timeout_add(WATCHING_TIME, message)

  activityTime = time.time()

  if (coffeeWatcher == -1):
    # Set next logout to quit for coffee
    coffee = ((datetime.datetime.today().replace(hour=9, minute=0, second=0, microsecond=0) - datetime.datetime.today()).total_seconds() * 1000)
    if (coffee > 0):
      syslog.syslog(syslog.LOG_INFO, "[login] add coffee timer: " + str(int(coffee / 1000)) + " s")
      coffeeWatcher = GObject.timeout_add(coffee, coffeeMessage)

  if (homeWatcher == -1):
    # Set next logout to quit for going home
    home = ((datetime.datetime.today().replace(hour=16, minute=28, second=30, microsecond=0) - datetime.datetime.today()).total_seconds() * 1000)
    if (home > 0):
      syslog.syslog(syslog.LOG_INFO, "[login] add home timer: " + str(int(home / 1000)) + " s")
      homeWatcher = GObject.timeout_add(home, homeMessage)

# A new logout from user is detected
def logout():
  global activityTime
  syslog.syslog(syslog.LOG_INFO, "[logout]")

  stopTimer()
  activityTime = time.time() - activityTime
  displayTime()

# Signal bus handler
def logHandler(*args, **keywords):
  status = args[0];

  if (status == LOGIN_VALUE):
    login();
  else:
    logout();

# Get parameters arguments
def main(argv):
  global logfile
  try:
    opts, args = getopt.getopt(argv,"hles",["logfile=","seconds=","enabled="])
  except getopt.GetoptError:
    print 'test.py -l <logfile>'
    sys.exit(2)

  for opt, arg in opts:
    if opt == '-h':
      print 'test.py -l <logfile> -s <secondsBeforeLock> -e <lockenabled>'
      sys.exit()
    elif opt in ("-l", "--logfile"):
      logfile = arg
    elif opt in ("-e", "--enabled"):
      print("todo")
    elif opt in ("-s", "--seconds"):
      print("todo")

if __name__ == '__main__':
    main(sys.argv[1:])

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    Notify.init("MoveYourAss")

    bus = dbus.SessionBus()

    bus.add_signal_receiver(logHandler, dbus_interface="org.gnome.ScreenSaver", signal_name="ActiveChanged")

    syslog.syslog(syslog.LOG_NOTICE, "[Start]")

    loop = GObject.MainLoop()
    GObject.timeout_add(1000, login)

    try:
      loop.run()
    except:
      syslog.syslog(syslog.LOG_ERR, "[Stop]")
