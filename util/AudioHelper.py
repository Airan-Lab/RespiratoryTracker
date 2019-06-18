import simpleaudio as sa
import threading
import time

class AudioLoop():
    def __init__(self,path):
        self.wave_obj = sa.WaveObject.from_wave_file(path)
        self.play_thread = threading.Thread(target=self.play)
        self.running = False

    def play(self):
        while self.running:
            if time.time() - self.previous_time > 2:
                print("\a")
                self.previous_time = time.time()
                time.sleep(0.5)

    def start(self):
        if not self.running:
            self.running = True
            self.previous_time = time.time()
            self.play_thread.start()

    def stop(self):
        if self.running:
            self.running = False
            self.play_thread.join()
            self.play_thread = threading.Thread(target=self.play) #Recreate thread to resume


if __name__ == '__main__':
    test_obj = AudioLoop('../Media/Alarm.wav')

    try:
        test_obj.start()
        time.sleep(3)
    finally:
        test_obj.stop()
    
        
