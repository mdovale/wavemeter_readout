"""
WaveMeter readout
My take at previous code by @jdahn

Miguel Dovale
spectools@pm.me
"""
import pyvisa
import os, sys
import time
import csv
import threading
import argparse
import sys
from datetime import datetime
import random
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

INSTRUMENT_RESOURCE = 'GPIB0::4::INSTR'
"""
If you don't know the resource string:
>>> import pyvisa
>>> rm = pyvisa.ResourceManager()
>>> rm.list_resources()
('ASRL1::INSTR', 'ASRL2::INSTR', 'GPIB0::12::INSTR')
>>> inst = rm.open_resource('GPIB0::12::INSTR')
>>> print(inst.query("*IDN?"))
"""


def configure_wavemeter(wm, prop='WAVelength', res='.001', medium='air', ave='OFF'):
    """Configures the wavemeter. Skipped in debug mode."""
    if wm is None:
        print("Debug mode: Skipping wavemeter configuration.")
        return
    
    print('Configuring WaveMeter')
    wm.write(f':CONFigure:{prop}')
    wm.write(f':DISPlay:RESolution {res}')
    wm.write(f':SENSe:AVERage {ave}')
    wm.write(f':SENSe:MEDium {medium}')
    print('WaveMeter Configured')


class PlotWindow(QtWidgets.QMainWindow):
    """
    A Qt Window to plot Wavelength vs Time in real-time.
    Uses Qt signals to safely receive data from the measurement thread.
    """

    close_signal = QtCore.pyqtSignal()  # Signal emitted when the window is closed
    data_signal = QtCore.pyqtSignal(float, float)  # Signal for new data (time, wavelength)

    def __init__(self, max_points=500):
        super().__init__()
        self.setWindowTitle("Wavelength Measurement")
        self.setGeometry(100, 100, 800, 500)

        self.max_points = max_points
        self.wm_time = []
        self.wm_wavelength = []

        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.curve = self.plot_widget.plot(pen='y')

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # Update every 100ms

        # Connect the data signal to the slot function
        self.data_signal.connect(self.add_data)

    def update_plot(self):
        """Update the plot with new data."""
        if len(self.wm_time) > 0:
            self.curve.setData(self.wm_time[-self.max_points:], self.wm_wavelength[-self.max_points:])

    def add_data(self, time_val, wavelength_val):
        """Safely add new data points from another thread via Qt Signal."""
        self.wm_time.append(time_val)
        self.wm_wavelength.append(wavelength_val)

    def closeEvent(self, event):
        """Handle window close event by stopping measurement."""
        print("\nPlot window closed. Stopping measurement...")
        self.close_signal.emit()  # Notify the main thread to stop
        event.accept()


def measurement_loop(wm, config_dict, stop_event, plot_window=None, debug_mode=False):
    """Handles the measurement loop, acquiring data and sending it to the plot."""
    t_start = time.perf_counter()
    output_file = os.path.join(config_dict['readout_dir'], 'wavemeter_readout.csv')

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Time (s)', 'Wavelength'])
        if plot_window:
            print('Measurement started. Close the plot window to stop.')
        else:
            print('Measurement started. Press Ctrl+C to stop.')

        try:
            while not stop_event.is_set():
                current_time = time.perf_counter() - t_start

                if debug_mode:
                    current_wavelength = random.uniform(500.0, 600.0)  # Fake wavelength values
                else:
                    current_wavelength = float(wm.query(f':MEASure:{config_dict["property"]}?'))

                # Overwrite the same line in the terminal
                sys.stdout.write(f"\rTime: {current_time:.2f} s, Wavelength: {current_wavelength:.6f} nm")
                sys.stdout.flush()

                writer.writerow([current_time, current_wavelength])
                csvfile.flush()

                # Use Qt Signals to update the plot safely
                if plot_window:
                    plot_window.data_signal.emit(current_time, current_wavelength)

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nMeasurement stopped by user.")
            stop_event.set()

    print("\nMeasurement loop exiting...")


def main():
    parser = argparse.ArgumentParser(description="WaveMeter Data Acquisition")
    parser.add_argument('-g', '--graph', action='store_true', help="Enable real-time graphing")
    parser.add_argument('-p', '--property', type=str, default='WAVelength', help="Measurement property")
    parser.add_argument('-r', '--resolution', type=str, default='.001', help="Display resolution")
    parser.add_argument('-m', '--medium', type=str, default='air', help="Measurement medium")
    parser.add_argument('-a', '--averaging', type=str, default='OFF', help="Averaging setting")
    parser.add_argument('-d', '--debug', action='store_true', help="Enable debug mode (no hardware interfacing)")
    args = parser.parse_args()

    base_dir = os.getcwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    readout_dir = os.path.join(base_dir, 'readout', timestamp)
    os.makedirs(readout_dir, exist_ok=True)

    debug_mode = args.debug
    wm = None

    if not debug_mode:
        rm = pyvisa.ResourceManager()
        try:
            wm = rm.open_resource(INSTRUMENT_RESOURCE)
            print('Connected to instrument: ' + wm.query('*IDN?'))
        except pyvisa.errors.VisaIOError:
            print('Error querying wavemeter')
            return
    else:
        print("Debug mode enabled: No hardware connection.")

    config_dict = {
        'property': args.property,
        'resolution': args.resolution,
        'medium': args.medium,
        'averaging': args.averaging,
        'readout_dir': readout_dir,
    }

    configure_wavemeter(wm, config_dict['property'], config_dict['resolution'], config_dict['medium'], config_dict['averaging'])

    stop_event = threading.Event()

    # Initialize GUI in the main thread
    app = None
    plot_window = None

    if args.graph:
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)

        plot_window = PlotWindow()
        plot_window.close_signal.connect(lambda: stop_event.set())  # Stop when window is closed
        plot_window.show()

    measurement_thread = threading.Thread(target=measurement_loop, args=(wm, config_dict, stop_event, plot_window, debug_mode))
    measurement_thread.start()

    try:
        if args.graph:
            app.exec_()  # Run the Qt event loop
        else:
            while measurement_thread.is_alive():
                measurement_thread.join(timeout=1)
    except KeyboardInterrupt:
        stop_event.set()
        print("\nStopping measurement...")  # Now guaranteed to execute

        if args.graph and plot_window:
            plot_window.close()
            QtWidgets.QApplication.quit()

        measurement_thread.join()
        print("\nMeasurement completed.\nData saved to:", config_dict['readout_dir'])

        if wm:
            wm.close()
        os.chdir(base_dir)

        sys.exit(0)  # Force full exit

if __name__ == "__main__":
    main()