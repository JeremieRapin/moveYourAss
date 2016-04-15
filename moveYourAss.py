#!/usr/bin/env python

# This file must be copy into .config/autostart folder
# mv ~/scripts/moveYourAss.py ~/.config/autostart/

import dbus
import dbus.mainloop.glib
import datetime, threading
import gi
import os
import time
import sys
import getopt
gi.require_version('Notify', '0.7')
from gi.repository import Notify
from gi.repository import GObject

LOGIN_VALUE   = 0
LOGOUT_VALUE  = 1
WATCHING_TIME = 2700000 # in ms -- 45 minutes
LOCK_SCREEN   = 1 # if lock screen is set, then after WATCHING_TIME, the screen will be lock

#watcher must be called after callback defintion but before use.
watcher = -1
# set activity time at startup in order to have the right time at the first logout
activityTime = time.time()
# log file
logfile=""

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
  if(watcher != -1):
    # print("stop timer")
    GObject.source_remove(watcher)
    watcher = -1;

# A new login from user is detected start the timer
def login():
  # print("start timer")
  global watcher
  global activityTime
  if (LOCK_SCREEN == 1):
    watcher = GObject.timeout_add(WATCHING_TIME, message)

  activityTime = time.time()

# A new logout from user is detected
def logout():
  global activityTime

  stopTimer()
  activityTime = time.time() - activityTime
  displayTime()

# Signal bus handler
def logHandler(*args, **keywords):
  status = args[0];

  if (status == LOGIN_VALUE):
    print("login")
    login();
  else:
    print("logout")
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

    loop = GObject.MainLoop()
    loop.run()