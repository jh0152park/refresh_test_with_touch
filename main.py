#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import time
import subprocess
import scenario
from adb import ADB
from device import Device


def get_cur_time():
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(time.time()))


adb = ADB()
device_ids = adb.get_device_ids()
model_names = adb.get_model_names()
product_names = adb.get_product_names()

models = []
for i in range(len(device_ids)):
    models.append(Device(device_ids[i], model_names[i], product_names[i]))
    models[-1].press_home()
    time.sleep(1)
    models[-1].compute_uidump()
    print(models[-1].ui_info)

# compute the position of every test application
for model in models:
    for app in scenario.SCENARIO:
        if app not in model.ui_info.keys():
            print("{app} not ready for {id}/{product}, please check it again...".format(app=app,
                                                                                        id=model.id,
                                                                                        product=model.product))
        else:
            print("{} is ready.".format(app))

# reboot all test devices and unlock, also wait 5 min to be stable
for model in models:
    model.reboot()
time.sleep(10)

while len(ADB().get_device_ids()) != len(models):
    print("waiting every test device to connect...")
    time.sleep(10)
print("done.\nwait 2 min before unlock screen.")
time.sleep(60 * 2)

print("unlock screen.")
for model in models:
    model.unlock()

while True:
    print("waiting every test device to be stable...")
    if models[-1].get_uptime() >= 5:
        print("stable done.")
        break
    time.sleep(20)

# test start!
sequence = 1
scenarios = scenario.SCENARIO
for app in scenarios:
    print("run this app[{}/{}] : {}".format(sequence, len(scenarios), app))
    for model in models:
        position = model.ui_info[app]
        x = position.split(",")[0]
        y = position.split(",")[1]
        cmd = "adb -s " + model.id + " shell input tap " + x + " " + y
        os.popen(cmd)

    time.sleep(10)
    for model in models:
        model.press_home()
    time.sleep(3)
    sequence += 1
