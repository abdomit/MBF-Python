#!/usr/bin/env python2
#-*- coding: utf-8 -*-

from cothread import catools, Sleep
from mbf_memory import MBF_mem
from pylab import *
import argparse

class FIR:
    def __init__(self, fir, delay):
        self.fir = array(fir)
        self.N = size(self.fir)
        self.delay = int(delay)
    
    def __mul__(self, b):
        if isinstance(b, FIR):
            if self.N == b.N:
                return FIR(ifft(fft(self.fir)*fft(b.fir)).real,
                    self.delay+b.delay)
            else:
                return None
        else:
            return FIR(b*self.fir)
    
    def change_delay(self, new_delay):
        dt = self.delay - int(new_delay)
        if abs(dt) > self.N:
            dt = sign(dt)*self.N
        if dt > 0:
            self.fir[:dt] = 0
        elif dt < 0:
            self.fir[dt:] = 0
        self.fir = roll(self.fir, -dt)
        self.delay = int(new_delay)
    
    def fir_x_y(self):
        fir_x = arange(self.N) - self.delay
        return (fir_x, self.fir)


def get_NCO_bunch(device, dev_axis):
    nco_ena = catools.caget(device+':'+dev_axis+':NCO:ENABLE_S')
    bank_n = catools.caget(device+':'+dev_axis+':SEQ:1:BANK_S')
    bank_n_str = "{}".format(int(bank_n))
    outwf = catools.caget(device+':'+dev_axis+':BUN:'+bank_n_str+':OUTWF_S')
    bunch_not_off = where(outwf != 0)[0]
    if bunch_not_off.size == 1:
        bunch_i = bunch_not_off[0]
        if outwf[bunch_i] == 2:
            if nco_ena != 1:
                raise NameError("Please switch ON NCO.")
            return bunch_i
    raise NameError("You need one bunch with NCO, others OFF")


def deconvolution_fir(Beam_resp, x_max, n_max):
    # h: system's response to a dirac
    h = roll(Beam_resp.fir, -Beam_resp.delay)
    N = conj(fft(h))*x_max
    D = abs(fft(h))**2*x_max+n_max
    fir = ifft(N/D).real
    fir = roll(fir, Beam_resp.delay)
    return FIR(fir, Beam_resp.delay)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Compute a suitable ADC or \
            DAC FIR in order to cope for the system's imperfections.")
    parser.add_argument("-n", default=0, type=int,
        help="desired FIR delay", dest="fir_delay")
    parser.add_argument("-d", default="SR-TMBF", type=str,
        help="TMBF device name", dest="device")
    parser.add_argument("-f", default=0, type=int,
        help="Current filter delay", dest="cur_fir_delay")
    parser.add_argument("-b", default=None, type=int,
        help="Bunch number (override automatic detection)", dest="bunch")
    parser.add_argument("-r", action='store_true',
        help="Reset FIR", dest="reset_fir")
    parser.add_argument("axis", type=str,
        help="MBF axis (usually X or Y)")
    parser.add_argument("fir_type", type=str,
        help="FIR type: ADC or DAC")
    args = parser.parse_args()
    device = args.device
    bunch = args.bunch
    fir_delay = args.fir_delay
    cur_fir_delay = args.cur_fir_delay
    reset_fir = args.reset_fir
    dev_axis = args.axis.upper()
    
    fir_type = args.fir_type.upper()
    if fir_type not in ['ADC', 'DAC']:
        print("Invalid FIR type: {}".format(fir_type))
        exit(1)
    
    # Get axis channel number
    axis_name_tab = ["", ""]
    for channel in [0, 1]:
        axis_name_tab[channel] = catools.caget(
            device+':AXIS{}'.format(int(channel)))
    
    if dev_axis not in axis_name_tab:
        print("Invalid axis name: {}".format(dev_axis))
        exit(1)
    channel = axis_name_tab.index(dev_axis)
    
    n_TAPS = catools.caget(device+':{}_TAPS'.format(fir_type))
    
    if reset_fir:
        fir = zeros(n_TAPS)
        fir[0] = 1
        catools.caput(device+':{}:{}:FILTER_S'.format(dev_axis, fir_type),
            around(fir, 5))
        exit(0)
    
    offset = 0
    tune = catools.caget(device+':'+dev_axis+':NCO:FREQ_S')
    
    # Check than NCO is used only on one bunch
    # and get that bunch number
    if bunch is None:
        bunch = get_NCO_bunch(device, dev_axis)

    # Set SEQ mode to 'One Shot' and stop current acquisition
    catools.caput(device+':'+dev_axis+':TRG:SEQ:MODE_S', 0, wait=True)
    catools.caput(device+':'+dev_axis+':TRG:SEQ:DISARM_S', 1, wait=True)
    catools.caput(device+':'+dev_axis+':SEQ:RESET_S', 1, wait=True)
        
    # Set runout to 99.5 %
    catools.caput(device+':MEM:RUNOUT_S', 4, wait=True)
    # Set Long Buffer Selection to ADC0/ADC1
    catools.caput(device+':MEM:SELECT_S', 0)
    # MEM source after FIR
    catools.caput(device+':'+dev_axis+':ADC:DRAM_SOURCE_S', 1, wait=True)
    # Set mode to 'One Shot', enable soft trig.
    catools.caput(device+':TRG:MEM:MODE_S', 0, wait=True)
    catools.caput(device+':TRG:MEM:SOFT:EN_S', 1, wait=True)
    # Arm and trig memory
    catools.caput(device+':TRG:MEM:ARM_S', 1, wait=True)
    catools.caput(device+':TRG:SOFT_S', 1, wait=True)
    Sleep(0.1)

    mbf = MBF_mem(device)
    decimation = mbf.get_max_decimation()
    _, max_turn = mbf.get_turn_min_max()
    count = max_turn//decimation

    try:
        ampl_cplx = mbf.read_mem_avg(count, offset, channel, decimation, tune)
    except:
        print("Error in read_mem (Timeout?)")
        raise
    else:
        max_i = argmax(abs(ampl_cplx))
        f = ampl_cplx*conj(ampl_cplx[max_i]/abs(ampl_cplx[max_i]))
        I = f.real

    I = roll(I, -bunch)
    n_max = sqrt(2)*I[n_TAPS:].std()
    I = roll(I, fir_delay)
    I = I[:n_TAPS]
    x_max = abs(I).max()
    Beam_resp = FIR(I, fir_delay)
    
    # Plot system's response
    figure()
    plot(*Beam_resp.fir_x_y())
    title("System's response to an impulsion")
    xlabel('Bunch #')
    ylabel('bunch ampl. (a.u.)')

    # Get current FIR
    cur_fir = catools.caget(device+':{}:{}:FILTER_S'.format(dev_axis,
        fir_type))
    #cur_fir_delay = catools.caget(device+':{}:DAC:FILTER:DELAY_S'.format(dev_axis))
    cur_FIR = FIR(cur_fir, cur_fir_delay)
    cur_dac_delay = catools.caget(device+':{}:DAC:DELAY_S'.format(dev_axis))
    cur_fir = roll(cur_fir, -cur_fir_delay)

    # Compute new FIR
    corr_FIR = deconvolution_fir(Beam_resp, x_max, n_max)
    new_FIR = corr_FIR*cur_FIR
    new_FIR.fir /= abs(new_FIR.fir).max()
    new_FIR.change_delay(fir_delay)

    # Plot old and new FIR
    figure()
    plot(*cur_FIR.fir_x_y(), label="old {} FIR".format(fir_type))
    plot(*new_FIR.fir_x_y(), label="new {} FIR".format(fir_type))
    title(fir_type + ' FIR')
    legend(loc='best')
    xlabel('FIR taps')
    ylabel('FIR')
    show()
    
    user_answer = None
    while user_answer not in ['y', 'n']:
        user_answer = raw_input("Apply new FIR? (y/n) ")
        user_answer = user_answer.lower()
    
    if user_answer == 'y':
    # Update FIR
        catools.caput(device+':{}:{}:FILTER_S'.format(dev_axis, fir_type),
            around(new_FIR.fir, 5))
        #catools.caput(device+':{}:DAC:FILTER:DELAY_S'.format(dev_axis),
        #    new_FIR.delay)
        new_dac_delay = cur_dac_delay - (new_FIR.delay - cur_FIR.delay)
        catools.caput(device+':{}:DAC:DELAY_S'.format(dev_axis), new_dac_delay)
