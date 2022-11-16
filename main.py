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


# result log files list
event_logs = []
logcat_logs = []
proc_meminfo_logs = []
dumpsys_meminfo_logs = []

# get connected device information
adb = ADB()
device_ids = adb.get_device_ids()
model_names = adb.get_model_names()
product_names = adb.get_product_names()

# make result folder
RESULT_FOLDER = get_cur_time()
if RESULT_FOLDER not in os.listdir(os.getcwd()):
    os.mkdir(RESULT_FOLDER)
os.chdir(RESULT_FOLDER)

# main home screen check
models = []
for i in range(len(device_ids)):
    models.append(Device(device_ids[i], model_names[i], product_names[i]))
    models[-1].press_home()
    time.sleep(1)
    models[-1].compute_uidump()

# compute the position of every test application
for model in models:
    for app in scenario.SCENARIO:
        if app not in model.ui_info.keys():
            print("{app} not ready for test {id}/{product},please check it again...".format(app=app,
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


# create result log files
for model in models:
    logcat_logs.append(
        open(model.id + "_" + model.product + "_full_time_logcat.txt", "a"))
    event_logs.append(
        open(model.id + "_" + model.product + "_full_time_eventlog.txt", "a"))
    proc_meminfo_logs.append(
        open(model.id + "_" + model.product + "_full_time_proc_meminfo.txt", "a"))
    dumpsys_meminfo_logs.append(
        open(model.id + "_" + model.product + "_full_time_dumpsys_meminfo.txt", "a"))

# start gathering full time logcat / event logs
logcat_pars = []
event_log_pars = []
for i in range(len(models)):
    model = models[i]
    logcat_pars.append(subprocess.Popen(model.logcat_log, stdout=logcat_logs[i], shell=False))
    event_log_pars.append(subprocess.Popen(model.event_log, stdout=event_logs[i], shell=False))

# test start!
sequence = 1
scenarios = scenario.SCENARIO * 5
for app in scenarios:
    print("run this app[{}/{}] : {}".format(sequence, len(scenarios), app))
    for model in models:
        position = model.ui_info[app]
        x = position.split(",")[0]
        y = position.split(",")[1]
        cmd = "adb -s " + model.id + " shell input tap " + x + " " + y
        os.popen(cmd)
    time.sleep(10)

    cur_time = get_cur_time()
    for i in range(len(models)):
        model = models[i]
        proc_meminfo = os.popen(model.proc_meminfo).read()
        meminfo_extra = os.popen(model.meminfo_extra).read()
        dumpsys_meminfo = os.popen(model.dumpsys_meminfo).read()

        proc_meminfo_logs[i].write("{time}\nrun this app : {app}\n\n{log1}\n{log2}\n\n".format(
            time=cur_time, app=app, log1=proc_meminfo, log2=meminfo_extra))
        dumpsys_meminfo_logs[i].write("{time}\nrun this app : {app}\n\n{log}\n\n".format(
            time=cur_time, app=app, log=dumpsys_meminfo))
        proc_meminfo_logs[i].flush()
        dumpsys_meminfo_logs[i].flush()

    for model in models:
        model.press_home()
    time.sleep(3)
    sequence += 1

print("Test Done...!")
# close result log files
for i in range(len(models)):
    logcat_pars[i].terminate()
    event_log_pars[i].terminate()
    proc_meminfo_logs[i].close()
    dumpsys_meminfo_logs[i].close()

print("Start pulling bugreport log file.")
bugreports = []
for model in models:
    bugreports.append(subprocess.Popen(model.bugreport))

while True:
    done = 0
    for proc in bugreports:
        if proc.poll() is None:
            pass
            # still pulling bugreport log file
        else:
            done += 1
            if done == len(bugreports):
                print("pulled all bugreport log...!")
                exit(0)
