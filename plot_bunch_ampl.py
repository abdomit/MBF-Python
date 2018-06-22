#!/usr/bin/env python2
#-*- coding: utf-8 -*-

from __future__ import print_function

from time import time, sleep
import argparse
from pylab import *
import matplotlib.animation as animation

from cothread import catools, Sleep
from threading import Thread, Condition, Lock
from mbf_memory import MBF_mem


class DataAcquisition(Thread):
    def __init__(self, device):
        Thread.__init__(self)
        mem_trig_request_lock = Lock()
        mem_trig_request_lock.acquire()
        self.trigger_cdt = Condition(mem_trig_request_lock)
        self.device = device
        self.axis = catools.caget(device+':AXIS{}'.format(int(channel)))
        # Set runout to 12.5 %
        catools.caput(device+':MEM:RUNOUT_S', 0, wait=True)
        self.new_data = 0
        self.stop = 0
        self.do_reset_axis()
        self.mbf = MBF_mem(device)
        self.decimation = self.mbf.get_max_decimation()
        self.max_count = self.mbf.get_count_max(self.decimation)
        
    def do_reset_axis(self, event=None):
        self.reset_axis = True

    def run(self):
        device = self.device
        axis = self.axis
        offset = 0
        bunch = None
        while not self.stop:
            self.trigger_cdt.wait()
            tune = self.tune
            count = self.max_count//8
            try:
                ampl_cplx = self.mbf.read_mem_avg(count, offset, channel, self.decimation, tune)
            except:
                print("Error in read_mem (Timeout?)")
                raise
                sleep(0.2)
            else:
                max_i = argmax(abs(ampl_cplx))
                f = ampl_cplx*conj(ampl_cplx[max_i]/abs(ampl_cplx[max_i]))
                self.I = f.real
                self.Q = f.imag
                self.new_data = 1


def animate(i, ax1, thread_1):
    if thread_1.new_data == 1:
        axis_bk = axis()
        ax1.clear()
        sca(ax1)
        xlabel('Bunch #')
        ylabel('Amplitude')
        title("Bunch "+thread_1.axis+" oscillation amplitude @ NCO={:.5f}".format(thread_1.tune))
        plot(thread_1.I, '-o')
        plot(thread_1.Q, '-o')
        if not thread_1.reset_axis:
            axis(axis_bk)
        else:
            thread_1.reset_axis = False
        thread_1.new_data = 0
    # Ask for a new capture as soon as previous mem_read is finished
    with thread_1.trigger_cdt:
        thread_1.tune = catools.caget(thread_1.device+':'+thread_1.axis+
                ':NCO:FREQ_S')
        # Capture command doesn't work so well (mis-aligned data)
        #catools.caput(thread_1.device+':MEM:CAPTURE_S', 1, wait=True)
        catools.caput(thread_1.device+':TRG:MEM:ARM_S', 1, wait=True)
        catools.caput(thread_1.device+':TRG:SOFT_S', 1, wait=True)
        # Wait for memory to be actually triggered
        Sleep(0.05)
        thread_1.trigger_cdt.notify()


def Button2_callback(event):
    pass


def Button3_callback(event):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Show beam motion at NCO frequency.")
    parser.add_argument("-c", default=0, type=int, help="Channel number", dest="channel")
    parser.add_argument("-d", default="SR-TMBF", type=str, help="TMBF device name", dest="device_name")
    args = parser.parse_args()
    device_name = args.device_name
    
    channel = args.channel
    if channel not in [0, 1]:
        print("Invalid channel number: {}".format(channel))
        exit(1)
    
    # Thread creation
    thread_1 = DataAcquisition(device_name)
    thread_1.start()
    
    # New figure
    fig = figure()
    ax1 = fig.add_subplot(1,1,1)
    # Add buttons
    #  Autoscale
    subplots_adjust(bottom=0.17)
    ax_butt = axes([0.75, 0.025, 0.15, 0.05])
    b_autoscale = Button(ax_butt, 'Autoscale')
    b_autoscale.on_clicked(thread_1.do_reset_axis)
    #  Button number 2
    """
    ax_butt = axes([0.45, 0.025, 0.25, 0.05])
    b_2 = Button(ax_butt, 'Button number 2')
    b_2.on_clicked(Button2_callback)
    """
    #  Button number 3
    """
    ax_butt = axes([0.15, 0.025, 0.25, 0.05])
    b_3 = Button(ax_butt, 'Button number 3')
    b_3.on_clicked(Button3_callback)
    """
    
    # Start plotting data
    ani = animation.FuncAnimation(fig, animate, interval=100, fargs=(ax1, thread_1))
    try:
        show()
    finally:
        # Figure has been closed: we stop thread_1 and exit
        thread_1.stop = 1
        thread_1.join()
