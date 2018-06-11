#!/usr/bin/env python2
#-*- coding: utf-8 -*-

import numpy as np
import argparse
import socket
from time import time

from cothread import catools


class MBF_mem():
    def __init__(self, device):
        self.device = device
        self.bunch_nb = catools.caget(device + ":BUNCHES")
        hostname_l = catools.caget(device + ":HOSTNAME")
        hostname = "".join(map(chr, hostname_l))
        hostname = hostname.rstrip("\0")
        port = catools.caget(device + ":SOCKET")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(6.)
        self.s.connect((hostname, port))

    def __del__(self):
        self.s.close()

    def get_turn_min_max(self):
        runout_ = catools.caget(self.device + ":MEM:RUNOUT_S")
        runout = [0.125, 0.25, 0.5, 0.75, 255./256][runout_]
        min_turn = np.ceil(((runout-1)*2.**29)/self.bunch_nb)
        max_turn = np.floor((runout*2.**29)/self.bunch_nb)
        return min_turn, max_turn
    
    def get_count_max(self, decimation):
        return ((2**29)//self.bunch_nb)//decimation
    
    def get_max_decimation(self):
        READ_BUFFER_BYTES = 2**20-64
        sizeof_uint32 = 4
        buffer_size = READ_BUFFER_BYTES  / sizeof_uint32 - self.bunch_nb
        return int(np.ceil((1.*buffer_size) / self.bunch_nb) - 1)

    def read_mem_avg(self, count, offset=0, channel=None, decimation=None,
            tune=None, verbose=False):
        d = self.read_mem(count, offset=offset, channel=channel,
            decimation=decimation, tune=tune, verbose=verbose)
        n = np.size(d)
        out_buffer_size = self.bunch_nb
        if channel is None:
            out_buffer_size *= 2
        N = n//out_buffer_size
        d.shape = (N, out_buffer_size)
        return d.mean(0)

    def read_mem(self, count, offset=0, channel=None, bunch=None,
            decimation=None, tune=None, verbose=False):
        cmd_str = "M{}O{}".format(count, int(offset))
        expected_msg_len = count
        msg_fmt = 'int16'

        if channel is not None:
            if channel not in [0, 1]:
                raise NameError("channel should be: None, 0 or 1")
            cmd_str += "C{}".format(channel)
        else:
            expected_msg_len *= 2

        if bunch is not None:
            if (int(bunch) < 0) or (int(bunch) > self.bunch_nb):
                raise NameError("bunch should be between 0 and {}".format(
                    self.bunch_nb))
            cmd_str += "B{}".format(int(bunch))
        else:
            expected_msg_len *= self.bunch_nb

        if decimation is not None:
            if (int(decimation) < 1) or (int(decimation) > self.get_max_decimation()):
                raise NameError("decimation should be between 1 and {}".format(self.get_max_decimation()))
            cmd_str += "D{}".format(int(decimation))
            msg_fmt = 'float32'

        if tune is not None:
            cmd_str += "T{}".format(float(tune))
            msg_fmt = 'complex64'

        if msg_fmt == 'int16':
            expected_msg_len *= 2
        elif msg_fmt == 'float32':
            expected_msg_len *= 4
        elif msg_fmt == 'complex64':
            expected_msg_len *= 8

        # Add a timeout of 5 s.
        cmd_str += 'LW5000'
        
        if verbose:
            print cmd_str, " | ", expected_msg_len

        self.s.send(cmd_str + '\n')
        BUFFER_SIZE = 1024
        data = self.s.recv(BUFFER_SIZE)

        if data[0] != chr(0):
            raise NameError(data)

        data = data[1:]
        recv_bytes = len(data)
        while recv_bytes < expected_msg_len:
            d = self.s.recv(BUFFER_SIZE)
            data += d
            recv_bytes += len(d)
        if verbose:
            print "recv_bytes: ", recv_bytes

        dt = np.dtype(np.__dict__[msg_fmt])
        dt = dt.newbyteorder('<')
        d = np.frombuffer(data, dtype=dt)

        return d


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Read memory buffer.")
    parser.add_argument("-c", default=None, type=int, help="Channel number", dest="channel")
    parser.add_argument("-d", default="SR-TMBF", type=str, help="TMBF device name", dest="device_name")
    parser.add_argument("-t", default=None, type=float, help="Frequency for domodyne detection (in SR turns units)", dest="tune")
    args = parser.parse_args()
    
    device_name = args.device_name
    tune = args.tune
    channel = args.channel
    
    mbf = MBF_mem(device_name)

    bunch = None
    decimation = mbf.get_max_decimation()
    count = mbf.get_count_max(decimation)
    min_turn, _ = mbf.get_turn_min_max()
    offset = min_turn

    data = mbf.read_mem(count, offset, channel, bunch, decimation, tune)
    print data
