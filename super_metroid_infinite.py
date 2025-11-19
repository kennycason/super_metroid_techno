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

# Import our synthesizers from track02
from track02 import Synthesizer, DrumMachine, midi_to_freq


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


class AudioVisualizer:
    """Audio-reactive visualization based on chaos_effect.py"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.time = 0
        
        # Audio reactive parameters
        self.audio_energy = 0
        self.bass_energy = 0
        self.mid_energy = 0
        self.high_energy = 0
        
        # Visual elements
        self.particles = []
        self.max_particles = 100
        self.waveform_history = []
        
        # Rotating elements
        self.rotation = 0
        
    def update_audio_data(self, energy=0.5, bass=0.5, mid=0.5, high=0.5):
        """Update with audio parameters"""
        self.audio_energy = energy
        self.bass_energy = bass
        self.mid_energy = mid
        self.high_energy = high
    
    def update(self):
        """Update animation"""
        self.time += 1
        self.rotation += 0.02 + self.audio_energy * 0.05
        
        # Spawn particles based on audio
        if random.random() < self.audio_energy * 0.3:
            self.spawn_particle()
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 0.02
            particle['hue'] = (particle['hue'] + 2) % 360
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def spawn_particle(self):
        """Spawn new particle"""
        if len(self.particles) < self.max_particles:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6) * (1 + self.audio_energy)
            
            particle = {
                'x': self.width / 2,
                'y': self.height / 2,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'size': random.uniform(3, 8),
                'hue': random.uniform(0, 360),
                'life': 1.0
            }
            self.particles.append(particle)
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h / 360.0, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def draw(self, surface):
        """Draw visualization"""
        # Background based on bass
        bg_intensity = int(20 + self.bass_energy * 30)
        surface.fill((bg_intensity, bg_intensity // 2, bg_intensity // 2))
        
        # Center pulsing circle (bass reactive)
        center_x, center_y = self.width // 2, self.height // 2
        radius = int(50 + self.bass_energy * 100)
        hue = (self.time * 2) % 360
        color = self.hsv_to_rgb(hue, 0.8, 0.9)
        pygame.draw.circle(surface, color, (center_x, center_y), radius, 5)
        
        # Rotating bars (mid reactive)
        num_bars = 8
        for i in range(num_bars):
            angle = self.rotation + i * (2 * math.pi / num_bars)
            length = 80 + self.mid_energy * 150
            x1 = center_x + math.cos(angle) * 60
            y1 = center_y + math.sin(angle) * 60
            x2 = center_x + math.cos(angle) * length
            y2 = center_y + math.sin(angle) * length
            
            bar_hue = (hue + i * 45) % 360
            bar_color = self.hsv_to_rgb(bar_hue, 0.9, 0.8)
            pygame.draw.line(surface, bar_color, (int(x1), int(y1)), (int(x2), int(y2)), 4)
        
        # Outer ring (high reactive)
        ring_radius = int(180 + self.high_energy * 80)
        ring_color = self.hsv_to_rgb((hue + 180) % 360, 0.7, 0.7)
        pygame.draw.circle(surface, ring_color, (center_x, center_y), ring_radius, 3)
        
        # Particles
        for particle in self.particles:
            p_color = self.hsv_to_rgb(particle['hue'], 1.0, particle['life'])
            size = int(particle['size'] * particle['life'])
            if size > 0:
                pygame.draw.circle(surface, p_color, (int(particle['x']), int(particle['y'])), size)
        
        # Waveform-like pattern at bottom
        waveform_y = self.height - 50
        points = []
        for x in range(0, self.width, 10):
            offset = math.sin(x * 0.02 + self.time * 0.1) * 20 * self.audio_energy
            points.append((x, waveform_y + offset))
        
        if len(points) > 1:
            wave_color = self.hsv_to_rgb((hue + 90) % 360, 0.8, 0.9)
            pygame.draw.lines(surface, wave_color, False, points, 3)


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
        self.is_recording = False
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
        
        # Audio queue for visualization
        self.audio_queue = queue.Queue(maxsize=5)
        
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
        self.visualizer = AudioVisualizer(self.width, self.height)
        
        print("\n✅ Ready!")
        print("\n🎹 Controls:")
        print("   SPACE - Toggle recording")
        print("   ESC - Quit")
        print("   Click button - Toggle recording")
        
    def start_recording(self):
        """Start recording to WAV file"""
        timestamp = int(time.time())
        self.current_file = f"sm_infinite_{timestamp}.wav"
        self.audio_buffer = AudioSegment.silent(duration=0)
        self.is_recording = True
        print(f"\n🔴 RECORDING: {self.current_file}")
    
    def stop_recording(self):
        """Stop recording and save file"""
        if self.is_recording and len(self.audio_buffer) > 0:
            print(f"\n⏹️  Saving {self.current_file}...")
            self.audio_buffer.export(self.current_file, format="wav")
            duration = len(self.audio_buffer) / 1000
            print(f"   ✅ Saved {duration:.1f} seconds")
            self.current_file = None
        self.is_recording = False
    
    def generate_and_record_bar(self):
        """Generate one bar and add to recording"""
        # Randomly change patterns every 8-16 bars
        if self.bar_counter % random.randint(8, 16) == 0:
            self.mixer.randomize_patterns()
        
        # Generate bar
        bar = self.mixer.generate_bar(self.bar_counter)
        
        # Master the bar
        bar = bar.normalize(headroom=1.5)
        
        # Add to buffer if recording
        if self.is_recording:
            self.audio_buffer += bar
        
        # Update visualization (fake audio energy based on bar content)
        energy = random.uniform(0.6, 0.95)
        bass = random.uniform(0.5, 0.9)
        mid = random.uniform(0.4, 0.8)
        high = random.uniform(0.3, 0.7)
        self.visualizer.update_audio_data(energy, bass, mid, high)
        
        self.bar_counter += 1
        
        return bar
    
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
        
        # Generate first bar in background
        print("\n🎵 Generating music...")
        
        running = True
        space_was_pressed = False
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if not space_was_pressed:
                            self.toggle_recording()
                            space_was_pressed = True
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        space_was_pressed = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        button_rect = (self.width - 50, 10, 40, 40)
                        if self.check_button_click(event.pos, button_rect):
                            self.toggle_recording()
            
            # Generate audio bar
            bar = self.generate_and_record_bar()
            
            # Update visualization
            self.visualizer.update()
            
            # Draw
            self.visualizer.draw(self.screen)
            button_rect = self.draw_ui()
            
            pygame.display.flip()
            
            # Note: In real-time, we'd want to play audio too, but for now
            # we're just generating and optionally recording
            # Limit frame rate
            self.clock.tick(2)  # ~2 bars per second at 128 BPM
        
        # Clean up
        if self.is_recording:
            self.stop_recording()
        
        pygame.quit()
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    generator = InfiniteGenerator(width=640, height=480, bpm=128)
    generator.run()

