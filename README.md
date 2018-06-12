# MBF-Python

A set of Python scripts in order to work with [DLS-MBF](https://github.com/DLS-Controls-Private-org/DLS-MBF). Currently these scripts are compatible only with the Transverse MBF.

## Documentation

A small description of every script is available with:

```
 script_name.py -h
```
## Scripts

### [plot_bunch_ampl.py](https://github.com/abdomit/MBF-Python/blob/master/plot_bunch_ampl.py "plot_bunch_ampl.py")

```
usage: plot_bunch_ampl.py [-h] [-c CHANNEL] [-d DEVICE_NAME]

Show beam motion at NCO frequency.

optional arguments:
   -h, --help      show this help message and exit 
   -c CHANNEL      Channel number
   -d DEVICE_NAME  TMBF device name
```

This script will display a live graph showing beam motion amplitude for every bunches, at NCO frequency. Note that the script doesn't configure MBF to enable NCO: it has to be done manually.

The displayed bunch motion is phase sensitive: the bunch with the highest oscillation amplitude is used as a reference with phase set to 0. The phase of the other bunches will be relative to this reference bunch, but also takes into account the phase different of NCO signal for different bunches. Two curves are shown: the in-phase component of the motion (blue), and quadrature component (green).

A possible application is the following: one wants to adjust DAC FIR. For that purpose the NCO has to be enabled to excite a *single* bunch at its betatron oscillation frequency. The script will be used to measure how much neighbor bunches oscillates, and adjust DAC FIR to lower it. For this measurement one has to use the lower possible NCO frequency, ideally mode 0.

### [scan_dac_delay.py](https://github.com/abdomit/MBF-Python/blob/master/scan_dac_delay.py "scan_dac_delay.py")

```
usage: scan_dac_delay.py [-h] [-b BUNCH] [-c CHANNEL] [-d DEVICE_NAME]
                         [-s SCAN_STEP]

Scan DAC Delay and plot bunches motion.

optional arguments:
  -h, --help      show this help message and exit
  -b BUNCH        Number of the first bunch to monitor
  -c CHANNEL      Channel number (0 or 1)
  -d DEVICE_NAME  TMBF device name
  -s SCAN_STEP    Step size for delay scan (default: 1)
```

Display a graph showing bunch oscillation amplitude at NCO frequency, for 4 bunches: BUNCH to BUNCH+3.

Typical usage is to adjust DAC delay. For that purpose the NCO has to be enabled to excite a *single* bunch at its betatron oscillation frequency. The ideal DAC delay will be chosen with the help of the output graph.

### [mbf_memory.py](https://github.com/abdomit/MBF-Python/blob/master/mbf_memory.py "mbf_memory.py")

```
usage: mbf_memory.py [-h] [-c CHANNEL] [-d DEVICE_NAME] [-t TUNE]

Read memory buffer.

optional arguments:
  -h, --help      show this help message and exit
  -c CHANNEL      Channel number
  -d DEVICE_NAME  TMBF device name
  -t TUNE         Frequency for homodyne detection (in SR turns units)
```

Lower level script to read MBF's fast memory.

## Building and Installation

### Dependencies

The project has the following general dependencies.

* Python 2.7

### Python Module Dependencies

* Pylab
* cothread
