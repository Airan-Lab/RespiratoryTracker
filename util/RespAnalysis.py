import numpy as np
import scipy.signal as signal
import threading
import traceback
import time

class RespData():
    def __init__(self,arduino,history=20,rate=50,num_channels=4,cutoff=[0.01,3]):
        self.history = history #Length of data buffer, in seconds
        self.sample_rate = rate #Sample Rate, in Hz
        self.nyrate = 0.5 * self.sample_rate
        self.buff_len = history*rate
        self.num_channels = num_channels

        #Filter Setup
        filt_cutoff = np.array(cutoff)/self.nyrate
        self.filt_b, self.filt_a = signal.butter(4, filt_cutoff, 'bandpass') #Filter coefs
        self.filts_zi = np.array([signal.lfilter_zi(self.filt_b,self.filt_a)
                                  for i in range(num_channels)]).T #Initial states of filters

        self.ring_buffer = np.zeros((2*self.buff_len,num_channels))
        self.frame_num = 0

        self.streaming = False
        self.stream_thread = None
        self.arduino = arduino

    #Input expected: val should be a 1D array with length = num_channels
    def process_packet(self,val):
        assert len(val) == self.num_channels
        val = val.reshape([1,-1])
        idx = self.frame_num % self.buff_len

        if self.frame_num == 0:
            #If first frame, then initialize our filters appropriately then throw out the datapoint
            self.filts_zi *= np.tile(val,(len(self.filts_zi),1))
            filt_val = val
            self.frame_num += 1
            return
        else:
            #Otherwise incorporate into our real-time filter
            filt_val, self.filts_zi = signal.lfilter(self.filt_b,self.filt_a,val,axis=0,zi=self.filts_zi)
        #print(filt_val)
        self.ring_buffer[idx,:] = self.ring_buffer[idx + self.buff_len,:] = -filt_val
        buffer = self.ring_buffer[idx + 1:idx + 1 + self.buff_len,:]

        if self.frame_num % 4 == 0:#self.frame_num >= self.buff_len:
            rates,peaks_found =  self.resp_rate(buffer) #Only compute RR if buffer is full
            self.plotter.plot(buffer,rates,peaks_found)
        #else:
        #    self.plotter.plot(buffer,[],[])

        self.frame_num += 1

    def resp_rate(self,buffer):
        rates = np.zeros(self.num_channels) #Rates in resps/min
        peaks_found = []
        for i in range(self.num_channels):
            peaks,peaks_data = signal.find_peaks(buffer[:,i],width=5,prominence=30)
            peaks_found.append(peaks)
            time = np.min([self.frame_num/self.sample_rate,self.history])
            rates[i] = int(np.round((len(peaks) / time) * 60.0))
        
        return rates,peaks_found

    def stream(self):
        while self.streaming:
            start_time = time.time()
            input = self.arduino.port.readline().strip()
            input = input.decode('ascii')
            try:
                input = np.array(input.split(','),dtype=float)
                self.process_packet(input)
            except Exception as err:
                err_str = 'ERROR: ' + str(err) + '\n\n'
                err_str += traceback.format_exc()
                print(self, 'Error', err_str)

            #print(time.time() - start_time)

    def start(self,plotter):
        if not self.streaming:
            self.plotter = plotter
            self.arduino.start()
            if self.arduino.port is not None and self.arduino.port.isOpen():
                self.streaming = True
                self.stream_thread = threading.Thread(target=self.stream)
                self.stream_thread.start()
            else:
                IOError('Arduino not Connected')

    def stop(self):
        if self.streaming:
            self.streaming = False
            self.stream_thread.join()
            self.stream_thread = None
            self.arduino.stop()
        

