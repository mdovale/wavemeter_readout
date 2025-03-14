# WaveMeter Readout

## Author
**Miguel Dovale**  
mdovale@arizona.edu  

## Overview
This project provides a **Python-based tool** for real-time data acquisition from a **wavemeter** via **GPIB communication**. It supports configurable measurement parameters, real-time visualization using **PyQtGraph**, and data logging to CSV.

## Features
- ✅ Interfaces with a **GPIB-connected wavemeter** using `pyvisa`
- ✅ Configurable **measurement parameters** (wavelength, resolution, averaging, medium)
- ✅ **Real-time plotting** of wavelength vs. time (optional)
- ✅ **CSV logging** for data storage
- ✅ **Debug mode** for testing without hardware
- ✅ **Multi-threaded** implementation for smooth UI performance

## Installation
Before running the script, ensure you have the required dependencies installed:

```bash
pip install pyvisa pyqtgraph pyqt5
```

For hardware communication, you may also need to install NI-VISA or a compatible VISA library.

Usage

1. Basic Command

Run the script without visualization:

```bash
python wavemeter_readout.py
```

2. Enable Real-Time Graphing

To visualize wavelength vs. time:

```bash
python wavemeter_readout.py --graph
```

3. Debug Mode (No Hardware Required)

For testing without a physical wavemeter:

```bash
python wavemeter_readout.py --graph --debug
```

4. Configuring Measurement Parameters

You can customize the acquisition settings using the following options:

```bash
python wavemeter_readout.py --property WAVelength --resolution .001 --medium air --averaging OFF
```

	•	`--property`: Measurement property (default: `WAVelength`)
	•	`--resolution`: Display resolution (default: `.001`)
	•	`--medium`: Measurement medium (`air` or `vacuum`, default: `air`)
	•	`--averaging`: Enable/disable averaging (`ON` or `OFF`, default: `OFF`)

File Output

All recorded data is saved in the readout/ directory. The output CSV file format:

```bash
Time (s), Wavelength
0.10, 532.0012
0.20, 532.0015
```
...

Code Structure
	•	`wavemeter_readout.py`: Main script for acquiring and logging data.
	•	`PlotWindow`: Handles real-time visualization using PyQtGraph.
	•	`measurement_loop`: Manages data acquisition and writes CSV logs.
	•	`configure_wavemeter`: Configures measurement settings.

Debugging & Troubleshooting

Checking Available Instruments

If unsure about the GPIB resource string, you can list available devices:

```bash
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())
```

Common Issues
	•	GPIB Connection Error: Ensure NI-VISA or a compatible driver is installed.
	•	No Graph Appears: Make sure PyQt5 is installed.
	•	Permission Denied (Linux/Mac): Run with sudo if required.

License

This project is licensed under the GPL3 License.