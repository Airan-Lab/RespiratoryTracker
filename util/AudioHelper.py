import threading
import time
#import simpleaudio as sa
from multiprocessing import Process

class AudioLoop():
    def __init__(self,path):
        #self.wave_obj = sa.WaveObject.from_wave_file(path)
        self.play_thread = Process(name="PlaySound",target=self.play)
        self.running = False

    def play(self):
        while self.running:
            if time.time() - self.previous_time > 2:
                self.previous_time = time.time()
                #play_obj = self.wave_obj.play()
                #play_obj.wait_done()
                print("RESPIRATORY ALARM \a")
                
                time.sleep(0.5)

    def start(self):
        if not self.running:
            self.running = True
            self.previous_time = time.time()
            self.play_thread.start()

    def stop(self):
        if self.running:
            self.running = False
            self.play_thread.terminate()
            # Recreate thread to resume
            self.play_thread = Process(name="PlaySound", target=self.play)


if __name__ == '__main__':
    test_obj = AudioLoop('../Media/Alarm.wav')

    try:
        test_obj.start()
        time.sleep(3)
    finally:
        test_obj.stop()
    
        
