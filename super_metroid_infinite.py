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
        self.active_lead = None  # Main chorus lead
        
        # Effect toggles
        self.bass_effect = None
        self.melody_effect = None
        
        # Bass variation tracking (changes slower)
        self.bass_pattern_index = 0
        self.bass_variation_counter = 0
        
        # Section tracking (intro, verse, chorus, breakdown)
        self.current_section = 'intro'
        self.section_bar_counter = 0
        
    def change_section(self, new_section=None):
        """Change musical section (intro, verse, chorus, breakdown)"""
        if new_section:
            self.current_section = new_section
        else:
            # Cycle through sections intelligently
            sections = ['verse', 'chorus', 'verse', 'chorus', 'breakdown', 'chorus']
            section_idx = sections.index(self.current_section) if self.current_section in sections else 0
            self.current_section = sections[(section_idx + 1) % len(sections)]
        
        self.section_bar_counter = 0
        print(f"\n🎵 SECTION: {self.current_section.upper()}")
    
    def randomize_patterns(self, change_bass=True):
        """Choose new random patterns"""
        # Bass changes less frequently
        if change_bass and self.patterns['bass']:
            self.active_bass = random.choice(self.patterns['bass'])
            self.bass_effect = random.choice([None, 'distortion', 'delay', 'filter'])
            print(f"   🔊 New Bass: {self.active_bass['source']} ({self.bass_effect or 'dry'})")
        
        # Melody patterns
        if self.patterns['melody']:
            self.active_melody = random.choice(self.patterns['melody'])
            self.active_lead = random.choice(self.patterns['melody'])  # Separate lead for chorus
        
        # Pads and arps
        if self.patterns['pads']:
            self.active_pad = random.choice(self.patterns['pads'])
        if self.patterns['arpeggios']:
            self.active_arp = random.choice(self.patterns['arpeggios'])
        
        # Effects
        self.melody_effect = random.choice([None, 'reverb', 'delay'])
        
        print(f"🔀 Pattern Change:")
        print(f"   Melody: {self.active_melody['source'] if self.active_melody else 'None'}")
        print(f"   Lead: {self.active_lead['source'] if self.active_lead else 'None'}")
        print(f"   Pad: {self.active_pad['source'] if self.active_pad else 'None'}")
    
    def generate_bar(self, bar_num):
        """Generate one bar of music with current patterns"""
        bar = AudioSegment.silent(duration=int(self.bar_duration))
        
        # Track section progression
        self.section_bar_counter += 1
        
        is_chorus = self.current_section == 'chorus'
        is_breakdown = self.current_section == 'breakdown'
        is_verse = self.current_section == 'verse'
        
        # === DRUMS (always present except some breakdowns) ===
        drum_intensity = 0.5 if is_breakdown else 1.0
        
        if not (is_breakdown and bar_num % 4 < 2):  # Sometimes drop drums in breakdown
            # Kick - four on the floor
            for beat in range(4):
                kick_pos = int(beat * self.beat_duration)
                punch = (1.5 if is_chorus else 1.2) + random.uniform(-0.1, 0.2)
                gain = 3 if is_chorus else 2
                bar = bar.overlay(self.drums.kick(punch=punch) + gain, position=kick_pos)
            
            # Snare on 2 and 4
            for snare_beat in [1, 3]:
                snare_pos = int(snare_beat * self.beat_duration)
                bar = bar.overlay(self.drums.snare() + (1 if is_chorus else 0), position=snare_pos)
            
            # Hi-hats (16th notes)
            for sixteenth in range(16):
                if random.random() > 0.1:
                    hihat_pos = int(sixteenth * self.beat_duration / 4)
                    closed = not (sixteenth % 4 == 3)
                    bar = bar.overlay(self.drums.hihat(closed=closed) - 2, position=hihat_pos)
        
        # === BASS (with slower variation) ===
        if self.active_bass:
            bass_notes = self.active_bass['notes']
            
            # Create bass pattern variation every 4 bars
            variation_offset = (bar_num // 4) % 4
            
            for beat in range(4):
                # More complex bass pattern
                note_idx = (bar_num * 4 + beat + variation_offset) % len(bass_notes)
                bass_note = bass_notes[note_idx]
                bass_freq = midi_to_freq(bass_note)
                bass_pos = int(beat * self.beat_duration)
                
                # Double layer bass
                bass = self.synth.deep_bass(bass_freq, self.beat_duration * 0.9, fatness=5)
                
                # Apply effect
                if self.bass_effect == 'distortion':
                    bass = AudioEffects.distortion(bass, gain=1.5)
                elif self.bass_effect == 'delay':
                    bass = AudioEffects.delay(bass, delay_ms=int(self.beat_duration / 2), mix=0.2)
                elif self.bass_effect == 'filter':
                    bass = AudioEffects.filter_lowpass(bass, cutoff_ratio=0.6)
                
                bar = bar.overlay(bass - 5, position=bass_pos)
                
                # Add sub bass on beat 1 and 3
                if beat in [0, 2] and is_chorus:
                    sub = self.synth.deep_bass(bass_freq / 2, self.beat_duration * 1.2, fatness=3)
                    bar = bar.overlay(sub - 8, position=bass_pos)
        
        # === MAIN LEAD/MELODY (MUCH MORE PROMINENT!) ===
        if is_chorus and self.active_lead:
            # CHORUS - Big loud lead!
            lead_notes = self.active_lead['notes']
            num_steps = 8
            
            for step in range(num_steps):
                if random.random() > 0.15:  # 85% note density
                    note_idx = (bar_num * num_steps + step) % len(lead_notes)
                    lead_note = lead_notes[note_idx]
                    lead_freq = midi_to_freq(lead_note + 12)  # Octave up for prominence
                    step_duration = self.bar_duration / num_steps
                    lead_pos = int(step * step_duration)
                    
                    # Brass lead (loud and proud!)
                    lead = self.synth.brass_lead(lead_freq, step_duration * 0.8, velocity=100)
                    
                    # Layer with second voice for thickness
                    lead2 = self.synth.brass_lead(lead_freq * 1.01, step_duration * 0.8, velocity=90)
                    lead = lead.overlay(lead2 - 2)
                    
                    # Apply reverb for space
                    if self.melody_effect == 'reverb':
                        lead = AudioEffects.reverb(lead, mix=0.3)
                    elif self.melody_effect == 'delay':
                        lead = AudioEffects.delay(lead, delay_ms=int(self.beat_duration), mix=0.25)
                    
                    # MUCH LOUDER - only -4dB reduction instead of -11dB!
                    bar = bar.overlay(lead - 4, position=lead_pos)
        
        # === SUPPORTING MELODY (Verse/Other sections) ===
        if not is_chorus and self.active_melody and random.random() > 0.3:
            melody_notes = self.active_melody['notes']
            num_steps = random.choice([8, 16])
            
            for step in range(num_steps):
                if random.random() > 0.4:  # Sparser
                    note_idx = (bar_num * num_steps + step) % len(melody_notes)
                    melody_note = melody_notes[note_idx]
                    melody_freq = midi_to_freq(melody_note)
                    step_duration = self.bar_duration / num_steps
                    melody_pos = int(step * step_duration)
                    
                    # Vary voices
                    voice = random.choice(['brass', 'xylo', 'acid', 'brass'])  # More brass
                    if voice == 'brass':
                        melody = self.synth.brass_lead(melody_freq, step_duration * 0.7, velocity=85)
                    elif voice == 'xylo':
                        melody = self.synth.xylophone(melody_freq, step_duration * 0.5)
                    else:
                        melody = self.synth.acid_bass(melody_freq, step_duration * 0.6)
                    
                    if self.melody_effect == 'reverb':
                        melody = AudioEffects.reverb(melody, mix=0.25)
                    elif self.melody_effect == 'delay':
                        melody = AudioEffects.delay(melody, delay_ms=int(self.beat_duration), mix=0.3)
                    
                    bar = bar.overlay(melody - 9, position=melody_pos)
        
        # === PAD (Atmosphere) ===
        if self.active_pad and bar_num % 2 == 0:
            pad_notes = self.active_pad['notes'][:4]
            for i, pad_note in enumerate(pad_notes):
                pad_freq = midi_to_freq(pad_note)
                pad = self.synth.creepy_pad(pad_freq, self.bar_duration * 2)
                # Louder pads in chorus
                reduction = 18 if is_chorus else 22
                bar = bar.overlay(pad - reduction, position=0)
        
        # === ARPEGGIO (Texture) ===
        if self.active_arp and random.random() > 0.4:
            arp_notes = self.active_arp['notes']
            for sixteenth in range(16):
                if random.random() > 0.5:
                    note_idx = (bar_num * 16 + sixteenth) % len(arp_notes)
                    arp_note = arp_notes[note_idx]
                    arp_freq = midi_to_freq(arp_note + 12)
                    arp_pos = int(sixteenth * self.beat_duration / 4)
                    
                    arp = self.synth.xylophone(arp_freq, self.beat_duration * 0.15)
                    bar = bar.overlay(arp - 13, position=arp_pos)
        
        return bar


class AudioReactiveChaos(ChaosEffect):
    """Extended ChaosEffect that responds to audio parameters"""
    
    def __init__(self, width, height):
        super().__init__(width, height)
        self.audio_energy = 0.5
        self.bass_energy = 0.5
        self.mid_energy = 0.5
        self.high_energy = 0.5
        
        # Smoothed values for visual response
        self.smooth_bass = 0.5
        self.smooth_energy = 0.5
        
    def update_audio_data(self, energy=0.5, bass=0.5, mid=0.5, high=0.5):
        """Update with audio parameters"""
        # Smooth out the values for less jittery visuals
        smoothing = 0.3
        self.smooth_bass = self.smooth_bass * (1 - smoothing) + bass * smoothing
        self.smooth_energy = self.smooth_energy * (1 - smoothing) + energy * smoothing
        
        self.audio_energy = energy
        self.bass_energy = bass
        self.mid_energy = mid
        self.high_energy = high
        
        # Modulate chaos parameters based on audio
        self.max_particles = int(100 + bass * 150)  # More particles on bass
        self.kaleidoscope_segments = int(6 + high * 6)
        self.lissajous_a = 3 + int(mid * 4)
        
        # Spawn particles on bass hits
        if bass > 0.7:
            self.spawn_particles(int((bass - 0.7) * 30))
        
        # Extra particles on high energy
        if energy > 0.8:
            self.spawn_particles(int((energy - 0.8) * 40))
    
    def update(self):
        """Override update to include audio reactivity"""
        # Base update
        super().update()
        
        # Audio-reactive rotation speed
        rotation_speed = 0.02 + self.smooth_energy * 0.08
        self.fractal_angle += rotation_speed
    
    def draw(self, surface):
        """Override draw to add audio-reactive elements"""
        # Create layers for different effects with audio modulation
        
        # Layer 1: Voronoi diagram (background) - brightness responds to energy
        self.draw_voronoi(surface)
        
        # Layer 2: Geometric patterns - scale with bass
        self.draw_geometric_chaos(surface)
        
        # Layer 3: Strange attractor
        self.draw_strange_attractor(surface)
        
        # Layer 4: Particles
        self.draw_particles(surface)
        
        # Layer 5: Fractals - depth responds to mid
        self.fractal_depth = int(3 + 2 * math.sin(self.time * 0.01) + self.mid_energy * 2)
        self.draw_fractals(surface)
        
        # Layer 6: Lissajous curves
        self.draw_lissajous(surface)
        
        # Layer 7: Kaleidoscope overlay - intensity responds to high
        if self.time % 60 < 30 or self.high_energy > 0.6:
            self.draw_kaleidoscope(surface)
        
        # Layer 8: Bass-reactive center pulse
        self.draw_bass_pulse(surface)
    
    def draw_bass_pulse(self, surface):
        """Draw a pulsing center element that responds to bass"""
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Pulse size based on bass (more dramatic)
        base_radius = 30
        pulse_radius = int(base_radius + self.bass_energy * 150)
        
        # Color based on energy
        hue = (self.time * 2 + self.audio_energy * 100) % 360
        color = self.hsv_to_rgb(hue, 0.9, 0.8 + self.smooth_energy * 0.2)
        
        # Draw pulsing circle
        if pulse_radius > 10:
            pygame.draw.circle(surface, color, (int(center_x), int(center_y)), 
                             pulse_radius, max(3, int(5 * self.bass_energy)))
        
        # Draw inner glow on strong bass
        if self.bass_energy > 0.7:
            glow_radius = int(pulse_radius * 0.7)
            glow_color = self.hsv_to_rgb((hue + 60) % 360, 0.7, 0.6)
            pygame.draw.circle(surface, glow_color, (int(center_x), int(center_y)), 
                             glow_radius, 2)
    
    def draw_geometric_chaos(self, surface):
        """Override to make it bass-reactive"""
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Number of elements responds to energy
        num_elements = int(8 + self.audio_energy * 8)
        
        for i in range(num_elements):
            angle = self.time * (0.02 + self.smooth_energy * 0.03) + i * math.pi / 4
            
            # Distance pulses with bass
            base_distance = 100
            distance = base_distance + 50 * math.sin(self.time * 0.03 + i) + self.bass_energy * 80
            
            x = center_x + math.cos(angle) * distance
            y = center_y + math.sin(angle) * distance
            
            # Size pulses with mid frequencies
            size = 30 + 20 * math.sin(self.time * 0.05 + i) + self.mid_energy * 25
            rotation = self.time * 0.05 + i
            
            hue = (i * 45 + self.time + self.audio_energy * 50) % 360
            color = self.hsv_to_rgb(hue, 0.9, 0.7 + self.smooth_energy * 0.3)
            
            # Draw rotated square with audio-reactive size
            points = []
            for j in range(4):
                corner_angle = rotation + j * math.pi / 2
                px = x + math.cos(corner_angle) * size
                py = y + math.sin(corner_angle) * size
                points.append((px, py))
            
            pygame.draw.polygon(surface, color, points, max(1, int(2 + self.bass_energy * 2)))


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
        self.full_width = width
        self.full_height = height
        self.mini_width = 320
        self.mini_height = 120
        self.screen = None
        self.visualizer = None
        self.clock = None
        self.minimal_mode = False  # Toggle for CPU-light mode
        
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
        print("   V - Toggle visualization (full/minimal CPU mode)")
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
        pattern_change_interval = random.randint(8, 12)
        bass_change_interval = random.randint(16, 32)  # Bass changes slower!
        section_change_interval = random.randint(16, 24)
        
        # Start with intro
        self.mixer.change_section('intro')
        
        while not self.stop_generation.is_set():
            try:
                # Change section every 16-24 bars
                if bar_counter > 0 and bar_counter % section_change_interval == 0:
                    self.mixer.change_section()
                    section_change_interval = random.randint(16, 24)
                
                # Change bass less frequently (16-32 bars)
                change_bass = (bar_counter % bass_change_interval == 0)
                if change_bass and bar_counter > 0:
                    bass_change_interval = random.randint(16, 32)
                
                # Change other patterns every 8-12 bars
                if bar_counter % pattern_change_interval == 0 and bar_counter > 0:
                    self.mixer.randomize_patterns(change_bass=change_bass)
                    pattern_change_interval = random.randint(8, 12)
                elif change_bass:
                    # Just change bass without changing other patterns
                    self.mixer.randomize_patterns(change_bass=True)
                
                # Generate bar
                bar = self.mixer.generate_bar(bar_counter)
                
                # Master the bar
                bar = bar.normalize(headroom=1.5)
                
                # Calculate audio energy for visualization
                is_chorus = self.mixer.current_section == 'chorus'
                energy = random.uniform(0.7, 1.0) if is_chorus else random.uniform(0.5, 0.8)
                bass = 0.9 if self.mixer.active_bass else 0.3
                mid = 0.8 if self.mixer.active_melody or self.mixer.active_lead else 0.4
                high = 0.7 if self.mixer.active_arp else 0.3
                
                # Put in queue with metadata
                self.audio_queue.put({
                    'bar': bar,
                    'energy': energy,
                    'bass': bass,
                    'mid': mid,
                    'high': high,
                    'bar_num': bar_counter,
                    'section': self.mixer.current_section
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
        if self.minimal_mode:
            # Minimal mode - compact layout
            font = pygame.font.Font(None, 20)
            
            # Status and bar on one line
            status = "🔴 REC" if self.is_recording else "⏹️  STOP"
            status_color = (255, 100, 100) if self.is_recording else (150, 150, 150)
            status_text = font.render(f"{status} | Bar: {self.bar_counter}", True, status_color)
            self.screen.blit(status_text, (10, 10))
            
            # Section on second line
            section = getattr(self.mixer, 'current_section', 'playing').upper()
            section_colors = {
                'INTRO': (150, 150, 255),
                'VERSE': (150, 255, 150),
                'CHORUS': (255, 255, 0),
                'BREAKDOWN': (255, 150, 255)
            }
            section_color = section_colors.get(section, (200, 200, 200))
            section_text = font.render(f"Section: {section}", True, section_color)
            self.screen.blit(section_text, (10, 35))
            
            # File name on third line if recording
            if self.is_recording and self.current_file:
                file_text = font.render(self.current_file[:40], True, (255, 255, 100))
                self.screen.blit(file_text, (10, 60))
            
            # Help text
            help_text = font.render("V=Full | SPACE=Rec | ESC=Quit", True, (100, 100, 100))
            self.screen.blit(help_text, (10, 90))
            
            return (0, 0, 0, 0)  # No button in minimal mode
        
        else:
            # Full mode - regular layout
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
            
            # Bar counter and section
            bar_text = font.render(f"Bar: {self.bar_counter}", True, (200, 200, 200))
            self.screen.blit(bar_text, (10, 10))
            
            # Current section (big and prominent!)
            section = getattr(self.mixer, 'current_section', 'playing').upper()
            section_colors = {
                'INTRO': (150, 150, 255),
                'VERSE': (150, 255, 150),
                'CHORUS': (255, 255, 0),  # Yellow for chorus!
                'BREAKDOWN': (255, 150, 255)
            }
            section_color = section_colors.get(section, (200, 200, 200))
            big_font = pygame.font.Font(None, 32)
            section_text = big_font.render(section, True, section_color)
            self.screen.blit(section_text, (10, 40))
            
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
    
    def toggle_visualization(self):
        """Toggle between full visualization and minimal mode"""
        self.minimal_mode = not self.minimal_mode
        
        if self.minimal_mode:
            # Switch to minimal mode
            self.width = self.mini_width
            self.height = self.mini_height
            self.screen = pygame.display.set_mode((self.width, self.height))
            print("\n📉 Minimal mode (low CPU)")
        else:
            # Switch to full mode
            self.width = self.full_width
            self.height = self.full_height
            self.screen = pygame.display.set_mode((self.width, self.height))
            print("\n📈 Full visualization mode")
    
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
                            elif event.key == pygame.K_v:
                                self.toggle_visualization()
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
                    
                    # Update and draw visualization
                    if self.minimal_mode:
                        # Minimal mode - just black screen with text
                        self.screen.fill((0, 0, 0))
                        self.draw_ui()
                    else:
                        # Full visualization mode
                        self.visualizer.update()
                        self.visualizer.draw(self.screen)
                        self.draw_ui()
                    
                    pygame.display.flip()
                    
            except queue.Empty:
                # No audio ready, just update visualization
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                
                if self.minimal_mode:
                    self.screen.fill((0, 0, 0))
                    self.draw_ui()
                else:
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

