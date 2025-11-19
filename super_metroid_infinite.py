"""
SUPER METROID INFINITE - Endless Evolving Techno Generator
Randomly combines patterns from all Super Metroid MIDI tracks
Creates an ever-changing, never-repeating techno experience
"""

import pygame
import numpy as np
from pydub import AudioSegment
import mido
import math
import random
import time
import wave
import os
from collections import defaultdict
from pathlib import Path
import threading
import queue
import io
import pyaudio

# Import our synthesizers from track02
from track02 import Synthesizer, DrumMachine, midi_to_freq

# Import the chaos effect visualizer
from chaos_effect import ChaosEffect


class MIDIPatternAnalyzer:
    """Analyzes all MIDI files and extracts reusable patterns"""
    
    def __init__(self, reference_dir='reference'):
        self.reference_dir = reference_dir
        self.patterns = {
            'bass': [],
            'melody': [],
            'pads': [],
            'arpeggios': [],
            'percussion': [],
        }
        self.bpm_sources = {}
        
    def analyze_all_midis(self):
        """Parse all MIDI files and categorize patterns"""
        print("🎹 Analyzing MIDI library...")
        
        midi_files = list(Path(self.reference_dir).glob('*.mid'))
        
        for midi_path in midi_files:
            print(f"   Analyzing: {midi_path.name}")
            try:
                mid = mido.MidiFile(str(midi_path))
                source_name = midi_path.stem
                
                for track_idx, track in enumerate(mid.tracks):
                    notes = []
                    time = 0
                    tempo = 500000
                    
                    for msg in track:
                        time += msg.time
                        if msg.type == 'set_tempo':
                            tempo = msg.tempo
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes.append({
                                'note': msg.note,
                                'velocity': msg.velocity,
                                'time': time,
                                'channel': msg.channel
                            })
                    
                    if notes:
                        bpm = mido.tempo2bpm(tempo)
                        self.categorize_pattern(notes, source_name, track.name, bpm)
                        
            except Exception as e:
                print(f"   ⚠️  Skipped {midi_path.name}: {e}")
        
        print(f"\n✅ Pattern Library Built:")
        print(f"   Bass patterns: {len(self.patterns['bass'])}")
        print(f"   Melodies: {len(self.patterns['melody'])}")
        print(f"   Pads: {len(self.patterns['pads'])}")
        print(f"   Arpeggios: {len(self.patterns['arpeggios'])}")
        print(f"   Percussion: {len(self.patterns['percussion'])}")
    
    def categorize_pattern(self, notes, source, track_name, bpm):
        """Categorize notes into different pattern types"""
        if not notes:
            return
        
        avg_note = sum(n['note'] for n in notes) / len(notes)
        note_range = max(n['note'] for n in notes) - min(n['note'] for n in notes)
        note_density = len(notes) / (notes[-1]['time'] + 1)
        
        pattern = {
            'notes': [n['note'] for n in notes[:32]],  # Take first 32 notes
            'velocities': [n['velocity'] for n in notes[:32]],
            'source': source,
            'track': track_name,
            'bpm': bpm,
            'avg_note': avg_note
        }
        
        # Categorize based on characteristics
        if avg_note < 45:  # Low notes = bass
            self.patterns['bass'].append(pattern)
        elif note_density > 5:  # High density = arpeggio
            self.patterns['arpeggios'].append(pattern)
        elif note_range < 12 and note_density < 2:  # Sustained = pad
            self.patterns['pads'].append(pattern)
        elif avg_note > 60:  # High notes = melody
            self.patterns['melody'].append(pattern)
        else:  # Everything else
            self.patterns['melody'].append(pattern)


class AudioEffects:
    """Audio effects processor"""
    
    @staticmethod
    def delay(audio, delay_ms=250, feedback=0.4, mix=0.3):
        """Simple delay effect"""
        delayed = audio - (1000 * mix)  # Quieter
        result = audio.overlay(delayed, position=delay_ms)
        return result
    
    @staticmethod
    def reverb(audio, mix=0.2):
        """Simple reverb simulation using multiple delays"""
        result = audio
        delays = [50, 80, 120, 180, 250]
        for i, d in enumerate(delays):
            decay = mix * (0.8 ** i)
            result = result.overlay(audio - (decay * 30 * 1000), position=d)
        return result
    
    @staticmethod
    def filter_lowpass(audio, cutoff_ratio=0.7):
        """Simulate lowpass filter by reducing high frequencies"""
        # This is a crude approximation - just reduces volume
        return audio - (1 - cutoff_ratio) * 10
    
    @staticmethod
    def distortion(audio, gain=1.5):
        """Add some grit"""
        return (audio + (gain - 1) * 6).normalize(headroom=2.0)


class PatternMixer:
    """Randomly mixes patterns to create evolving music"""
    
    def __init__(self, pattern_analyzer, synth, drums, bpm=128):
        self.patterns = pattern_analyzer.patterns
        self.synth = synth
        self.drums = drums
        self.bpm = bpm
        self.beat_duration = 60000 / bpm
        self.bar_duration = self.beat_duration * 4
        
        # Current active patterns
        self.active_bass = None
        self.active_melody = None
        self.active_pad = None
        self.active_arp = None
        
        # Effect toggles
        self.bass_effect = None
        self.melody_effect = None
        
    def randomize_patterns(self):
        """Choose new random patterns"""
        if self.patterns['bass']:
            self.active_bass = random.choice(self.patterns['bass'])
        if self.patterns['melody']:
            self.active_melody = random.choice(self.patterns['melody'])
        if self.patterns['pads']:
            self.active_pad = random.choice(self.patterns['pads'])
        if self.patterns['arpeggios']:
            self.active_arp = random.choice(self.patterns['arpeggios'])
        
        # Randomly enable effects
        self.bass_effect = random.choice([None, 'distortion', 'delay'])
        self.melody_effect = random.choice([None, 'reverb', 'delay'])
        
        print(f"\n🔀 Pattern Change:")
        print(f"   Bass: {self.active_bass['source'] if self.active_bass else 'None'} ({self.bass_effect or 'dry'})")
        print(f"   Melody: {self.active_melody['source'] if self.active_melody else 'None'} ({self.melody_effect or 'dry'})")
        print(f"   Pad: {self.active_pad['source'] if self.active_pad else 'None'}")
    
    def generate_bar(self, bar_num):
        """Generate one bar of music with current patterns"""
        bar = AudioSegment.silent(duration=int(self.bar_duration))
        
        # === DRUMS (always present) ===
        # Kick - four on the floor
        for beat in range(4):
            kick_pos = int(beat * self.beat_duration)
            punch = 1.3 + random.uniform(-0.2, 0.3)
            bar = bar.overlay(self.drums.kick(punch=punch) + 2, position=kick_pos)
        
        # Snare on 2 and 4
        for snare_beat in [1, 3]:
            snare_pos = int(snare_beat * self.beat_duration)
            bar = bar.overlay(self.drums.snare(), position=snare_pos)
        
        # Hi-hats (16th notes)
        for sixteenth in range(16):
            if random.random() > 0.1:  # 90% chance
                hihat_pos = int(sixteenth * self.beat_duration / 4)
                closed = not (sixteenth % 4 == 3)
                bar = bar.overlay(self.drums.hihat(closed=closed) - 2, position=hihat_pos)
        
        # === BASS ===
        if self.active_bass and random.random() > 0.05:  # 95% chance
            bass_notes = self.active_bass['notes']
            for beat in range(4):
                note_idx = (bar_num * 4 + beat) % len(bass_notes)
                bass_note = bass_notes[note_idx]
                bass_freq = midi_to_freq(bass_note)
                bass_pos = int(beat * self.beat_duration)
                
                bass = self.synth.deep_bass(bass_freq, self.beat_duration * 0.85, fatness=4)
                
                # Apply effect
                if self.bass_effect == 'distortion':
                    bass = AudioEffects.distortion(bass, gain=1.4)
                elif self.bass_effect == 'delay':
                    bass = AudioEffects.delay(bass, delay_ms=int(self.beat_duration / 2), mix=0.2)
                
                bar = bar.overlay(bass - 6, position=bass_pos)
        
        # === MELODY ===
        if self.active_melody and random.random() > 0.2:  # 80% chance
            melody_notes = self.active_melody['notes']
            num_steps = random.choice([4, 8, 16])  # Vary rhythm
            
            for step in range(num_steps):
                if random.random() > 0.3:  # Some notes skip
                    note_idx = (bar_num * num_steps + step) % len(melody_notes)
                    melody_note = melody_notes[note_idx]
                    melody_freq = midi_to_freq(melody_note)
                    step_duration = self.bar_duration / num_steps
                    melody_pos = int(step * step_duration)
                    
                    # Choose synth voice
                    voice = random.choice(['brass', 'xylo', 'acid'])
                    if voice == 'brass':
                        melody = self.synth.brass_lead(melody_freq, step_duration * 0.7)
                    elif voice == 'xylo':
                        melody = self.synth.xylophone(melody_freq, step_duration * 0.5)
                    else:
                        melody = self.synth.acid_bass(melody_freq, step_duration * 0.6)
                    
                    # Apply effect
                    if self.melody_effect == 'reverb':
                        melody = AudioEffects.reverb(melody, mix=0.25)
                    elif self.melody_effect == 'delay':
                        melody = AudioEffects.delay(melody, delay_ms=int(self.beat_duration), mix=0.3)
                    
                    bar = bar.overlay(melody - 11, position=melody_pos)
        
        # === PAD ===
        if self.active_pad and bar_num % 2 == 0:  # Every 2 bars
            pad_notes = self.active_pad['notes'][:4]  # Use first 4 notes as chord
            for pad_note in pad_notes:
                pad_freq = midi_to_freq(pad_note)
                pad = self.synth.creepy_pad(pad_freq, self.bar_duration * 2)
                bar = bar.overlay(pad - 20, position=0)
        
        # === ARPEGGIO ===
        if self.active_arp and random.random() > 0.5:  # 50% chance
            arp_notes = self.active_arp['notes']
            for sixteenth in range(16):
                if random.random() > 0.6:  # Sparse
                    note_idx = (bar_num * 16 + sixteenth) % len(arp_notes)
                    arp_note = arp_notes[note_idx]
                    arp_freq = midi_to_freq(arp_note + 12)  # Octave up
                    arp_pos = int(sixteenth * self.beat_duration / 4)
                    
                    arp = self.synth.xylophone(arp_freq, self.beat_duration * 0.15)
                    bar = bar.overlay(arp - 15, position=arp_pos)
        
        return bar


class AudioReactiveChaos(ChaosEffect):
    """Extended ChaosEffect that responds to audio parameters"""
    
    def __init__(self, width, height):
        super().__init__(width, height)
        self.audio_energy = 0.5
        self.bass_energy = 0.5
        
    def update_audio_data(self, energy=0.5, bass=0.5, mid=0.5, high=0.5):
        """Update with audio parameters"""
        self.audio_energy = energy
        self.bass_energy = bass
        
        # Modulate chaos parameters based on audio
        self.max_particles = int(150 + bass * 100)
        self.kaleidoscope_segments = int(6 + high * 6)
        self.lissajous_a = 3 + int(mid * 4)
        
        # Spawn extra particles on energy spikes
        if energy > 0.8:
            self.spawn_particles(int((energy - 0.8) * 50))


class InfiniteGenerator:
    """Main infinite music generator"""
    
    def __init__(self, width=640, height=480, bpm=128):
        # Initialize components
        self.analyzer = MIDIPatternAnalyzer()
        self.synth = Synthesizer()
        self.drums = DrumMachine()
        self.bpm = bpm
        
        # Pattern mixer
        self.mixer = None  # Will be set after analysis
        
        # State
        self.is_recording = True  # Start recording by default!
        self.should_stop = False
        self.bar_counter = 0
        self.audio_buffer = AudioSegment.silent(duration=0)
        
        # File handling
        self.current_file = None
        self.wav_file = None
        
        # Pygame
        self.width = width
        self.height = height
        self.screen = None
        self.visualizer = None
        self.clock = None
        
        # PyAudio for playback
        self.pyaudio_instance = None
        self.audio_stream = None
        
        # Audio buffer queue (producer-consumer pattern)
        self.audio_queue = queue.Queue(maxsize=8)  # Buffer up to 8 bars
        self.generation_thread = None
        self.stop_generation = threading.Event()
        
    def initialize(self):
        """Initialize everything"""
        print("🎮 SUPER METROID INFINITE")
        print("=" * 60)
        
        # Analyze MIDI
        self.analyzer.analyze_all_midis()
        
        # Create mixer
        self.mixer = PatternMixer(self.analyzer, self.synth, self.drums, self.bpm)
        self.mixer.randomize_patterns()
        
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Super Metroid Infinite")
        self.clock = pygame.time.Clock()
        self.visualizer = AudioReactiveChaos(self.width, self.height)
        
        # Initialize PyAudio for playback
        self.pyaudio_instance = pyaudio.PyAudio()
        self.audio_stream = self.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            output=True,
            frames_per_buffer=1024
        )
        
        print("\n✅ Ready!")
        print("\n🎹 Controls:")
        print("   SPACE - Toggle recording")
        print("   ESC - Quit")
        print("   Click button - Toggle recording")
        
        # Start recording immediately
        self.start_recording()
        print("   🔴 Recording started automatically!")
        
        # Start background audio generation thread
        self.stop_generation.clear()
        self.generation_thread = threading.Thread(target=self._generate_audio_loop, daemon=True)
        self.generation_thread.start()
        print("   🎵 Background audio generation started!")
        
    def start_recording(self):
        """Start recording to WAV file"""
        if not self.is_recording:
            timestamp = int(time.time())
            self.current_file = f"sm_infinite_{timestamp}.wav"
            self.audio_buffer = AudioSegment.silent(duration=0)
            self.is_recording = True
            print(f"\n🔴 RECORDING: {self.current_file}")
        else:
            # Already recording, just create new file
            timestamp = int(time.time())
            self.current_file = f"sm_infinite_{timestamp}.wav"
            self.audio_buffer = AudioSegment.silent(duration=0)
    
    def stop_recording(self):
        """Stop recording and save file"""
        if self.is_recording and len(self.audio_buffer) > 0:
            print(f"\n⏹️  Saving {self.current_file}...")
            self.audio_buffer.export(self.current_file, format="wav")
            duration = len(self.audio_buffer) / 1000
            print(f"   ✅ Saved {duration:.1f} seconds")
            self.current_file = None
        self.is_recording = False
    
    def _generate_audio_loop(self):
        """Background thread that continuously generates audio bars"""
        bar_counter = 0
        pattern_change_interval = random.randint(8, 16)
        
        while not self.stop_generation.is_set():
            try:
                # Randomly change patterns
                if bar_counter % pattern_change_interval == 0 and bar_counter > 0:
                    self.mixer.randomize_patterns()
                    pattern_change_interval = random.randint(8, 16)
                
                # Generate bar
                bar = self.mixer.generate_bar(bar_counter)
                
                # Master the bar
                bar = bar.normalize(headroom=1.5)
                
                # Calculate audio energy for visualization
                energy = random.uniform(0.6, 0.95)
                bass = 0.8 if self.mixer.active_bass else 0.3
                mid = 0.7 if self.mixer.active_melody else 0.4
                high = 0.6 if self.mixer.active_arp else 0.3
                
                # Put in queue with metadata
                self.audio_queue.put({
                    'bar': bar,
                    'energy': energy,
                    'bass': bass,
                    'mid': mid,
                    'high': high,
                    'bar_num': bar_counter
                }, timeout=1.0)
                
                bar_counter += 1
                
            except queue.Full:
                # Queue is full, wait a bit
                time.sleep(0.1)
            except Exception as e:
                print(f"⚠️  Generation error: {e}")
                time.sleep(0.1)
    
    def draw_ui(self):
        """Draw UI elements"""
        # Record button (top right)
        button_size = 40
        button_x = self.width - button_size - 10
        button_y = 10
        
        if self.is_recording:
            # Red circle (recording)
            pygame.draw.circle(self.screen, (255, 0, 0), 
                             (button_x + button_size // 2, button_y + button_size // 2), 
                             button_size // 2)
        else:
            # White square (stopped)
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           (button_x, button_y, button_size, button_size))
        
        # Border
        pygame.draw.rect(self.screen, (100, 100, 100), 
                       (button_x, button_y, button_size, button_size), 3)
        
        # Status text
        font = pygame.font.Font(None, 24)
        status = "REC" if self.is_recording else "STOP"
        status_color = (255, 100, 100) if self.is_recording else (150, 150, 150)
        text = font.render(status, True, status_color)
        self.screen.blit(text, (button_x - 45, button_y + 10))
        
        # Bar counter
        bar_text = font.render(f"Bar: {self.bar_counter}", True, (200, 200, 200))
        self.screen.blit(bar_text, (10, 10))
        
        # File name if recording
        if self.is_recording and self.current_file:
            file_text = font.render(self.current_file, True, (255, 255, 100))
            self.screen.blit(file_text, (10, self.height - 30))
        
        return (button_x, button_y, button_size, button_size)
    
    def check_button_click(self, pos, button_rect):
        """Check if record button was clicked"""
        bx, by, bw, bh = button_rect
        if bx <= pos[0] <= bx + bw and by <= pos[1] <= by + bh:
            return True
        return False
    
    def toggle_recording(self):
        """Toggle recording state"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def run(self):
        """Main loop"""
        self.initialize()
        
        print("\n🎵 Buffering...")
        
        running = True
        space_was_pressed = False
        
        # Wait for initial buffer
        while self.audio_queue.qsize() < 3 and running:
            time.sleep(0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        
        print("🎵 Playing!")
        
        while running:
            try:
                # Get next bar from queue (with timeout to check events)
                audio_data = self.audio_queue.get(timeout=0.5)
                bar = audio_data['bar']
                
                # Update bar counter
                self.bar_counter = audio_data['bar_num']
                
                # Add to recording buffer
                if self.is_recording:
                    self.audio_buffer += bar
                
                # Update visualization parameters
                self.visualizer.update_audio_data(
                    audio_data['energy'],
                    audio_data['bass'],
                    audio_data['mid'],
                    audio_data['high']
                )
                
                # Play audio (this will block for ~bar duration)
                # We'll update visualization in a non-blocking way
                raw_data = bar.raw_data
                chunk_size = 2048  # Small chunks for responsiveness
                
                for i in range(0, len(raw_data), chunk_size):
                    # Check for quit events while playing
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running = False
                            break
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                running = False
                                break
                            elif event.key == pygame.K_SPACE:
                                if not space_was_pressed:
                                    self.toggle_recording()
                                    space_was_pressed = True
                        elif event.type == pygame.KEYUP:
                            if event.key == pygame.K_SPACE:
                                space_was_pressed = False
                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            if event.button == 1:
                                button_rect = (self.width - 50, 10, 40, 40)
                                if self.check_button_click(event.pos, button_rect):
                                    self.toggle_recording()
                    
                    if not running:
                        break
                    
                    # Play chunk
                    chunk = raw_data[i:i+chunk_size]
                    self.audio_stream.write(chunk)
                    
                    # Update visualization
                    self.visualizer.update()
                    self.visualizer.draw(self.screen)
                    self.draw_ui()
                    pygame.display.flip()
                    
            except queue.Empty:
                # No audio ready, just update visualization
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                
                self.visualizer.update()
                self.visualizer.draw(self.screen)
                self.draw_ui()
                pygame.display.flip()
                self.clock.tick(60)
        
        # Clean up
        print("\n🛑 Stopping...")
        self.stop_generation.set()
        if self.generation_thread:
            self.generation_thread.join(timeout=2.0)
        
        if self.is_recording:
            self.stop_recording()
        
        # Close audio stream
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
        if self.pyaudio_instance:
            self.pyaudio_instance.terminate()
        
        pygame.quit()
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    generator = InfiniteGenerator(width=640, height=480, bpm=128)
    generator.run()

