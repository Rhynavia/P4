import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt

FS = 44100
CHANNELS = 1
MUTE = False
LOOP = False


class Wave:
    def __init__(self, frequency=440.0, amplitude=0.5):
        self.frequency = frequency
        self.amplitude = amplitude
        self.time_offset = 0.0  # total playback time
    


    def create_wave(self, frames):

        # Envelope duration in seconds
        envelope_duration = 2.0

        # Create local time array within envelope cycle
        t = (np.arange(frames) / FS + self.time_offset)
        if LOOP:
            t = t % envelope_duration

        # Update time offset
        self.time_offset += frames / FS

        # Base wave
        f = self.frequency
        wave = 0.8 * np.sin(2 * np.pi * f * t)
        if f * 2 < FS / 2:
            wave += 0.3 * np.sin(2 * np.pi * f * 2 * t)
        if f * 3 < FS / 2:
            wave += 0.2 * np.sin(2 * np.pi * f * 3 * t)

        # Envelope (looped)
        attack = 0.1
        decay = 0.4
        env = np.ones_like(t)
        env[t < attack] = t[t < attack] / attack
        env[t >= attack] = np.exp(-(t[t >= attack] - attack) / decay)

        wave *= env
        return (self.amplitude * wave).reshape(-1, 1)
    
    def __repr__(self):
        return f"Wave(frequency={self.frequency}, amplitude={self.amplitude})"


class AudioManager:
    def __init__(self, bodies):
        self.phase = 0.0
        self.stream = sd.OutputStream(samplerate=FS, channels=CHANNELS, callback=self.callback)
        self.bodies = bodies


    def callback(self, outdata, frames, time, status):
        if status:
            print(status)

        data = np.zeros((frames, 1))
        for body in self.bodies:
            data += body.wave.create_wave(frames)

        max_val = np.max(np.abs(data))
        if max_val > 1.0:
            data /= max_val

        outdata[:] = data
    
    def start(self):
        if MUTE:
            print("Audio is muted.")
            return
        self.stream.start()
    
    def stop(self):
        self.stream.stop()
        self.stream.close()

    def plot_waveform(self, duration=2):
        frames = int(FS * duration)
        t = np.arange(frames) / FS
        data = np.zeros((frames, 1))
        for body in self.bodies:
            data += body.wave.create_wave(frames)

        plt.plot(t, data)
        plt.title("Synth Waveform")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)
        plt.show(block=False)

class Obj:
    def __init__(self, wave: Wave):
        self.wave = wave
        pass

if __name__ == "__main__":
    bodies = [
        Obj(Wave(261.63, 0.3)),  # C4
        # Obj(Wave(329.63, 0.3)),  # E4
        # Obj(Wave(392.00, 0.3)),  # G4
    ]

    auddioManager = AudioManager(bodies)
    auddioManager.plot_waveform()

    # Plot the waveform
    auddioManager.start()
    input("Press Enter to plot the waveform...")


