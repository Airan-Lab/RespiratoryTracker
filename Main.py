''' Main driver app for Respiratory Tracker displaying code
    Adapted from: https://pythonspot.com/pyqt5-matplotlib/

    @Author Jeffrey B. Wang
'''

import sys

from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, 
                               QSizePolicy, QMessageBox, QWidget, QPushButton, 
                               QComboBox, QLabel, QCheckBox, QLineEdit)
from PyQt5.QtGui import QIcon, QFont, QDoubleValidator
from PyQt5.QtCore import pyqtSignal
import qdarkstyle

import traceback

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import seaborn as sbs

import random
import numpy as np

import util.RespAnalysis as Resp
import util.ArduinoSerial as Arduino
import util.AudioHelper as Audio

class App(QMainWindow):

    def __init__(self,arduino,resp):
        super().__init__()
        #Initialize Window Settings
        plt.style.use("dark_background")
        self.left = 100
        self.top = 100
        self.title = 'Respiratory Tracker'
        self.width = 640
        self.height = 400

        grid = QGridLayout()
        self.setLayout(grid)

        #Initialize Subroutines
        self.arduino = arduino
        self.resp = resp

        self.alarm = Audio.AudioLoop('./Media/Alarm.wav')

        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        #Initialize Widgets
        self.plotter = PlotCanvas(self, width=5, height=4)
        self.plotter.move(0,0)
        self.plotter.alarm_sig.connect(self.alarm_start)
        self.plotter.alarm_cancel.connect(self.alarm.stop)

        self.refresh_button = QPushButton('Refresh Ports', self)
        self.refresh_button.move(500,75)
        self.refresh_button.resize(135,40)
        self.refresh_button.setIcon(QIcon('./Media/Refresh.png'))
        self.refresh_button.clicked.connect(self.refresh)

        #Port Selection
        self.ports_label = QLabel('Serial Port', self)
        self.ports_label.move(500, 0)

        self.ports_list = QComboBox(self)
        self.ports_list.move(500,30)
        self.ports_list.resize(135,40)

        self.connect_button = QPushButton('Connect', self)
        self.connect_button.move(500, 120)
        self.connect_button.resize(135, 40)
        self.connect_button.setIcon(QIcon('./Media/Connect.png'))
        self.connect_button.clicked.connect(self.connect)

        self.start_button = QPushButton('Start', self)
        self.start_button.move(500, 165)
        self.start_button.resize(135, 40)
        self.start_button.setIcon(QIcon('./Media/Execute.png'))
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.resize(135, 40)
        self.stop_button.move(500, 210)
        self.stop_button.setIcon(QIcon('./Media/Stop.png'))
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)

        #Controls for enabling channels
        self.channel_label = QLabel('Channels Enabled', self)
        self.channel_label.move(500, 250)
        self.channel_checks = []
        for i in range(4):
            self.channel_checks.append(QCheckBox(str(i),self))
            self.channel_checks[i].move(500 + 67*(i // 2),270 + 25*(i % 2))
            self.channel_checks[i].setTristate(False)
            self.channel_checks[i].stateChanged[int].connect(
                lambda x, ch=i: self.plotter.change_channel_state(ch, x))
            self.channel_checks[i].setChecked(True)

        #Control for enabling sound
        self.sound_check = QCheckBox('Sound?',self)
        self.sound_check.setTristate(False)
        self.sound_check.setChecked(True)
        self.sound_check.move(500,325)
        self.sound_check.stateChanged[int].connect(self.alarm_state)
        
        #Limits for Alarm
        self.double_valid = QDoubleValidator() #Set positive doubles only
        self.double_valid.setBottom(0.0)

        self.low_label = QLabel('L: ',self)
        self.low_label.move(500,350)
        self.low_edit = QLineEdit(self)
        self.low_edit.setValidator(self.double_valid)
        self.low_edit.resize(45,20)
        self.low_edit.move(520,355)
        self.low_edit.textChanged[str].connect(self.plotter.changelow)
        self.low_edit.setText('30')

        self.high_label = QLabel('H: ', self)
        self.high_label.move(567, 350)
        self.high_edit = QLineEdit(self)
        self.high_edit.setValidator(self.double_valid)
        self.high_edit.resize(45, 20)
        self.high_edit.move(587, 355)
        self.high_edit.textChanged[str].connect(self.plotter.changehigh)
        self.high_edit.setText('70')

        self.refresh()
        self.show()

    #Refresh Ports available
    def refresh(self):
        self.ports_list.clear()
        ports_avail = self.arduino.update_ports()
        self.ports_list.addItems([p.device for p in ports_avail])

    #Connect to Arduino
    def connect(self):
        port = str(self.ports_list.currentText())
        if port is not '':
            try:
                self.arduino.connect(port)
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(True)
            except Exception as err:
                err_str = 'ERROR: ' + str(err) + '\n\n'
                err_str += traceback.format_exc()
                QMessageBox.critical(self,'Error',err_str)
        else:
            QMessageBox.critical(self,'Error','No Port Selected!')

    #Start streaming from Arduino
    def start(self):
        try:
            self.resp.start(self.plotter)
        except Exception as err:
            err_str = 'ERROR: ' + str(err) + '\n\n'
            err_str += traceback.format_exc()
            QMessageBox.critical(self, 'Error', err_str)

    #Stop streaming
    def stop(self):
        self.resp.stop()
        self.alarm.stop()

    #Cleanup if application is closed
    def closeEvent(self, event):
        self.resp.stop()
        self.arduino.disconnect()
        self.alarm.stop()
        event.accept()

    #Start the respiratory alarm (assuming enough data has been collected)
    def alarm_start(self):
        if self.sound_check.isChecked() and self.resp.frame_num / self.resp.sample_rate > 0.25*self.resp.history:
            self.alarm.start()

    #Turn off alarm if respiratory alarm is turned off
    def alarm_state(self,state):
        if not state:
            self.alarm.stop()
        

#Widget to plot data as it's coming in
class PlotCanvas(FigureCanvas):

    alarm_sig = pyqtSignal()
    alarm_cancel = pyqtSignal()

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        
        self.fig, self.ax = plt.subplots(
            1, 1, figsize=(width, height), dpi=dpi)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.fig.patch.set_facecolor('#19232D')
        self.ax.set_facecolor('#19232D')

        self.states = [True,True,True,True] # To store channels that are enabled

        self.low_rate = 30
        self.high_rate = 70
        self.alarm_set = False

        self.plot(np.zeros((1000,4)),[],[[],[],[],[]])


    #Update Function
    def plot(self,data,resp_rates,peaks_found):
        num_channels = data.shape[-1]
        times = np.arange(len(data)) / 50
        times -= times[-1]

        plt.cla()

        alarmQ = False #Whether to trigger alarm

        for i in range(num_channels):
            if not self.states[i]:
                self.ax.plot(times, np.zeros_like(times)+i, 'C'+str(i))
                self.ax.text(1.4, i, 'N/A', horizontalalignment='center',
                             verticalalignment='center', size=14)
                continue

            minmax = max(np.max(data[:,i]) - np.min(data[:,i]),0.5)
            norm_data = ((data[:, i]-np.mean(data[:,i])) / minmax) + i

            self.ax.plot(times, norm_data, 'C'+str(i))

            #Plot called peaks
            if len(peaks_found) > 0 and len(peaks_found[i]) > 0:
                self.ax.plot(times[peaks_found[i]],norm_data[peaks_found[i]],'C'+str(i)+'*',markersize=12)

            #Print Respiratory Rates
            if len(resp_rates) > 0:
                if resp_rates[i] < self.low_rate or resp_rates[i] > self.high_rate:
                    self.ax.text(1.4,i,'{:d}'.format(int(resp_rates[i])),horizontalalignment='center',
                             verticalalignment='center',size=14,backgroundcolor='red')
                    alarmQ = True
                else:
                    self.ax.text(1.4, i, '{:d}'.format(int(resp_rates[i])), horizontalalignment='center',
                                 verticalalignment='center', size=14)
            else:
                self.ax.text(1.4, i, 'N/A', horizontalalignment='center',
                             verticalalignment='center', size=14)

            self.ax.plot([np.min(times), np.max(times)],[i, i], 'w', linewidth=0.5)

        if alarmQ:
            self.alarm_sig.emit()
            self.alarm_set = True
        elif self.alarm_set:
            self.alarm_cancel.emit()
            self.alarm_set = False

        self.ax.text(1.4, num_channels-0.5, 'RR', horizontalalignment='center',
                     verticalalignment='center', weight='bold', size=14)
        self.ax.set_xlim([times[0],times[-1]])
        self.ax.set_ylim([-0.5,num_channels-0.4])
        self.ax.set_yticks(np.arange(num_channels))

        #self.ax.set_title('Respiration Output')
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Channel')

        self.ax.spines['right'].set_visible(False)
        self.ax.spines['top'].set_visible(False)
        plt.tight_layout()
        plt.subplots_adjust(right=0.85)
        self.draw()

    def change_channel_state(self,channel,state):
        self.states[channel] = bool(state)
        print(str(channel) + ': ' + str(state))

    def changelow(self,lim):
        self.low_rate = float(lim)

    def changehigh(self, lim):
        self.high_rate = float(lim)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    arduino = Arduino.ArduinoSerial()
    resp = Resp.RespData(arduino)
    ex = App(arduino,resp)

    sys.exit(app.exec_())
