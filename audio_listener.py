import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
import wave as wave_module

class MacAudioCapture:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.channels = 1  # Start with mono, we'll adjust based on device
        
        # Show available devices
        print("=== Available Audio Devices ===")
        self.list_devices()
        print("=" * 50)
        
        # Try to find the best input device
        self.recommended_device = self.find_best_input_device()
    
    def list_devices(self):
        """List all available audio devices with their capabilities"""
        devices = sd.query_devices()
        
        print("INPUT DEVICES (for capturing audio):")
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                default_mark = " (DEFAULT)" if i == sd.default.device[0] else ""
                print(f"  Device {i}: {device['name']}{default_mark}")
                print(f"    • Channels: {device['max_input_channels']}")
                print(f"    • Sample Rate: {device['default_samplerate']}")
                input_devices.append((i, device))
                print()
        
        print("OUTPUT DEVICES (where Ableton should send audio):")
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                default_mark = " (DEFAULT)" if i == sd.default.device[1] else ""
                print(f"  Device {i}: {device['name']}{default_mark}")
                print(f"    • Channels: {device['max_output_channels']}")
                print()
        
        return input_devices
    
    def find_best_input_device(self):
        """Find the best available input device"""
        devices = sd.query_devices()
        
        # Look for BlackHole or other virtual audio devices first
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                name = device['name'].lower()
                if any(keyword in name for keyword in ['blackhole', 'soundflower', 'virtual', 'loopback']):
                    print(f"🎯 Found virtual audio device: {device['name']} (Device {i})")
                    return i
        
        # Fall back to default input device
        default_input = sd.default.device[0]
        if default_input is not None:
            print(f"📱 Using default input device: {devices[default_input]['name']} (Device {default_input})")
            return default_input
        
        return None
    
    def test_device(self, device_id):
        """Test if a device works and determine its optimal settings"""
        try:
            device_info = sd.query_devices(device_id)
            max_channels = device_info['max_input_channels']
            
            print(f"Testing device {device_id}: {device_info['name']}")
            print(f"Max input channels: {max_channels}")
            
            # Test with 1 channel first
            test_duration = 0.1  # Very short test
            
            for channels in [1, min(2, max_channels)]:
                try:
                    print(f"  Testing {channels} channel(s)...")
                    test_data = sd.rec(
                        int(test_duration * self.sample_rate),
                        samplerate=self.sample_rate,
                        channels=channels,
                        device=device_id,
                        dtype=np.float32
                    )
                    sd.wait()
                    print(f"  ✅ {channels} channel(s) work!")
                    return channels
                except Exception as e:
                    print(f"  ❌ {channels} channel(s) failed: {e}")
            
            return None
            
        except Exception as e:
            print(f"❌ Device {device_id} test failed: {e}")
            return None
    
    def capture_audio(self, duration=10, device=None):
        """Capture audio with automatic device configuration"""
        
        # Use recommended device if none specified
        if device is None:
            device = self.recommended_device
            if device is None:
                print("❌ No suitable input device found!")
                print("\n💡 SETUP HELP:")
                print("You need to set up audio routing to capture Ableton's output.")
                print("Options:")
                print("1. Install BlackHole: brew install blackhole-2ch")
                print("2. Set Ableton Output → BlackHole 2ch")
                print("3. Run this script to capture from BlackHole 2ch")
                return None
        
        # Test the device and get optimal channel count
        optimal_channels = self.test_device(device)
        if optimal_channels is None:
            print(f"❌ Device {device} is not working properly")
            return None
        
        self.channels = optimal_channels
        device_info = sd.query_devices(device)
        
        print(f"\n🎵 Capturing from: {device_info['name']}")
        print(f"📊 Using {self.channels} channel(s) at {self.sample_rate}Hz")
        print(f"⏱️ Duration: {duration} seconds")
        print("\n▶️  Make sure Ableton is playing and routing audio to this device!")
        print("🔴 Recording starts in 3 seconds...")
        
        # Countdown
        for i in range(3, 0, -1):
            print(f"   {i}...")
            sd.sleep(1000)
        
        try:
            print("🎙️ RECORDING...")
            
            # Record audio
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device,
                dtype=np.float32
            )
            
            # Wait for recording to complete
            sd.wait()
            
            print("✅ Recording complete!")
            
            # Check if we actually captured something
            if np.max(np.abs(audio_data)) < 0.001:
                print("⚠️  WARNING: Very low audio levels detected!")
                print("   Make sure:")
                print("   • Ableton is playing")
                print("   • Audio is routed to the correct output device")
                print("   • Volume levels are adequate")
            
            return audio_data
            
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None
    
    def create_spectrogram(self, audio_data, title="Audio Analysis"):
        """Create spectrogram with automatic mono conversion"""
        if audio_data is None or len(audio_data) == 0:
            print("❌ No audio data to analyze")
            return None
        
        # Convert to mono if stereo
        if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
            audio_mono = np.mean(audio_data, axis=1)
            print("🔄 Converted stereo to mono")
        else:
            audio_mono = audio_data.flatten()
        
        # Check audio levels
        max_level = np.max(np.abs(audio_mono))
        print(f"📊 Audio level: {max_level:.4f} (should be > 0.01 for good results)")
        
        if max_level < 0.001:
            print("⚠️  Audio level too low - check your routing!")
        
        # Calculate spectrogram
        frequencies, times, Sxx = signal.spectrogram(
            audio_mono,
            fs=self.sample_rate,
            window='hann',
            nperseg=2048,
            noverlap=1536
        )
        
        # Create visualization
        fig, axes = plt.subplots(3, 1, figsize=(14, 10))
        
        # 1. Waveform
        time_axis = np.linspace(0, len(audio_mono)/self.sample_rate, len(audio_mono))
        axes[0].plot(time_axis, audio_mono, color='blue', alpha=0.8)
        axes[0].set_title(f'Waveform - Max Level: {max_level:.4f}')
        axes[0].set_xlabel('Time (s)')
        axes[0].set_ylabel('Amplitude')
        axes[0].grid(True, alpha=0.3)
        
        # 2. Musical range spectrogram (20Hz-4kHz)
        Sxx_db = 10 * np.log10(Sxx + 1e-12)
        musical_freq_idx = (frequencies >= 20) & (frequencies <= 4000)
        
        if np.any(musical_freq_idx):
            im1 = axes[1].pcolormesh(times, frequencies[musical_freq_idx], 
                                   Sxx_db[musical_freq_idx], 
                                   shading='gouraud', cmap='magma')
            axes[1].set_ylabel('Frequency (Hz)')
            axes[1].set_title('Musical Range (20Hz-4kHz)')
            plt.colorbar(im1, ax=axes[1], label='Power (dB)')
        
        # 3. Full spectrum
        full_freq_idx = frequencies <= 10000
        im2 = axes[2].pcolormesh(times, frequencies[full_freq_idx], 
                               Sxx_db[full_freq_idx], 
                               shading='gouraud', cmap='viridis')
        axes[2].set_ylabel('Frequency (Hz)')
        axes[2].set_xlabel('Time (s)')
        axes[2].set_title('Full Spectrum (0-10kHz)')
        plt.colorbar(im2, ax=axes[2], label='Power (dB)')
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.show()
        
        return frequencies, times, Sxx
    
    def save_audio(self, audio_data, filename="ableton_capture.wav"):
        """Save captured audio"""
        if audio_data is None:
            return False
        
        try:
            # Convert to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            with wave_module.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            print(f"💾 Saved: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return False

def main():
    """Main function with device selection"""
    print("🎛️  Ableton Audio Capture & Spectrogram Analysis")
    print("=" * 55)
    
    capture = MacAudioCapture()
    
    # Let user choose device
    print("\nSelect input device:")
    print("Press Enter for recommended device, or enter device number:")
    
    try:
        user_input = input("Device choice: ").strip()
        if user_input:
            device = int(user_input)
        else:
            device = None
            
        # Capture and analyze
        audio_data = capture.capture_audio(duration=8, device=device)
        
        if audio_data is not None:
            capture.create_spectrogram(audio_data, "Ableton Live Capture")
            # capture.save_audio(audio_data)
            print("\n✨ Analysis complete!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except ValueError:
        print("❌ Invalid device number")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()