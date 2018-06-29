#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import sys

from pylab import *
from cothread.catools import *
from cothread import Sleep
import argparse
from mbf_memory import MBF_mem
from common import printProgressBar

STEP_NB = 8
FDLY_NB = 24
BUNCH_NB_SCAN = 4


parser = argparse.ArgumentParser(description="Scan DAC Delay and plot bunches motion.")
parser.add_argument("-b", default=0, type=int, help="Number of the first bunch to monitor", dest="bunch")
parser.add_argument("-c", default=0, type=int, help="Channel number (0 or 1)", dest="channel")
parser.add_argument("-d", default="SR-TMBF", type=str, help="TMBF device name", dest="device_name")
parser.add_argument("-s", default=1, type=int, help="Step size for delay scan (default: 1)", dest="scan_step")
args = parser.parse_args()

pv_base = args.device_name
bunch = args.bunch
scan_step = args.scan_step
channel = args.channel
if channel not in [0, 1]:
    print("Invalid channel number: {}".format(channel))
    exit(1)

# TODO:
#  Save and restore DAC delay
#  Set NCO on bunch #1 and put it on
#  Disable all triggers
#  Wait for possible current acquisition to finish

# Set Long Buffer Selection to ADC0/ADC1
caput(pv_base+':MEM:SELECT_S', 0)

# Set runout to 12.5 %
caput(pv_base+':MEM:RUNOUT_S', 0)
# Set arming in one-shot mode
caput(pv_base+':TRG:MEM:MODE_S', 0)
bunch_nb = caget(pv_base+':BUNCHES')
caput(pv_base+':DLY:DAC:RESET_S', 0)

mbf = MBF_mem(pv_base)

mbf_axis = caget(pv_base+':AXIS{}'.format(int(channel)))
bunches_i = arange(bunch, bunch+BUNCH_NB_SCAN)%bunch_nb
scan_a = zeros((STEP_NB*FDLY_NB, BUNCH_NB_SCAN+1))

decimation = mbf.get_max_decimation()
count = mbf.get_count_max(decimation)//8
tune = caget(pv_base+':'+mbf_axis+':NCO:FREQ_S')
offset = 0

ii = 0
print "Scanning DAC delay:"
for step in range(STEP_NB):
    for fine_delay in range(FDLY_NB):
        printProgressBar(ii+1, STEP_NB*FDLY_NB, prefix=' ', length=50)
        # set delay
        caput(pv_base+':DLY:DAC:FINE_DELAY_S', fine_delay)
        Sleep(0.01)
        if ii%scan_step == 0:
            # Capture command doesn't work so well (mis-aligned data)
            #caput(pv_base+':MEM:CAPTURE_S', 1)
            caput(pv_base+':TRG:MEM:ARM_S', 1, wait=True)
            caput(pv_base+':TRG:SOFT_S', 1, wait=True)
            Sleep(0.1)
            dly = caget(pv_base+':DLY:DAC:DELAY_PS')
            scan_a[ii, 0] = dly
            # Measure bunch amplitude at NCO frequency
            std_wf = mbf.read_mem_avg(count, offset, channel, decimation, tune)
            scan_a[ii, 1:BUNCH_NB_SCAN+1] = abs(std_wf[bunches_i])
        ii += 1
    caput(pv_base+':DLY:DAC:STEP_S', 0)

figure()
for ii, bunch_i in enumerate(bunches_i):
    plot(scan_a[:, 0], scan_a[:, ii+1], '*', label="bunch #{}".format(bunch_i))
legend(loc='best')
xlabel('DAC delay (ps)')
ylabel('Oscillation amplitude (a.u.)')
title("Scan DAC delay (" + mbf_axis + " axis)")
show()

