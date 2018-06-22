# MBF-Python

A set of Python scripts in order to work with [DLS-MBF](https://github.com/DLS-Controls-Private-org/DLS-MBF). Currently these scripts are compatible only with the Transverse MBF.

## Documentation

Below are some detailed instructions to use these scripts.

### Setting up RF clock phase, DAC delay and ADC/DAC FIR

Here we assume we are working on axis Y. We want an ADC filter with a delay of 2, and a DAC filter delay of 3.

To make sure we start with a un-configured system we first reset ADC and DAC filter with:
```
./compute_FIR.py -r Y ADC
./compute_FIR.py -r Y DAC
```

Computing ADC filter requires to have only one bunch in the machine (or one very far from other bunches). First Set NCO in order to shake this bunch (at tune frequency), and only this bunch.

1) Adjust turn clock delay to have the good bunch numbering.

2) Adjust DAC delay to hit the bunch you wanted to work with.

3) Adjust RF phase input.

4) Compute ADC FIR:
```
./compute_FIR.py -n 2 Y ADC
```

It will adjust DAC delay by automatically add 2.

5) You can do one more iteration:
```
./compute_FIR.py -n 3 -f 3 Y DAC
```

6) Remove 2 to the turn clock delay.

Now we need to address one bunch with the NCO, with many bunches around (uniform filling).

7) Adjust DAC delay (using scan_dac_delay.py).

8) Compute DAC FIR with:
```
./compute_FIR.py -n 2 Y DAC
```

9) You can do one more iteration:
```
./compute_FIR.py -n 3 -f 3 Y DAC
```

That's it! Your system is now ready for bunch by bunch applications.

## Scripts

### [compute_FIR.py](https://github.com/abdomit/MBF-Python/blob/master/compute_FIR.py "compute_FIR.py")

```
usage: compute_FIR.py [-h] [-n FIR_DELAY] [-d DEVICE] [-f CUR_FIR_DELAY]
                      [-b BUNCH] [-r]
                      axis fir_type

Compute the correct DAC FIR.

positional arguments:
  axis              MBF axis (usually X or Y)
  fir_type          FIR type: ADC or DAC

optional arguments:
  -h, --help        show this help message and exit
  -n FIR_DELAY      desired FIR delay
  -d DEVICE         TMBF device name
  -f CUR_FIR_DELAY  Current filter delay
  -b BUNCH          Bunch number (override automatic detection)
  -r                Reset FIR
```

This script compute ADC and DAC FIR to correct for the imperfection of the RF Front-end and Back-end. See instructions above.

#### ADC FIR



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

The displayed bunch motion is phase sensitive: the bunch will highest oscillation amplitude is use as a reference with phase set to 0. The phase of the other bunches will be relative to this reference bunch, but also takes into account the phase different of NCO signal for different bunches.

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

