from pydub.generators import Sine, Square, Sawtooth, WhiteNoise
from pydub import AudioSegment
import mido
import math
import random
import numpy as np

# Synthesizer classes
class Synthesizer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def generate_waveform(self, frequency, duration_ms, waveform='sine', phase=0):
        """Generate a waveform with given frequency and duration"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        if waveform == 'sine':
            samples = np.sin(2 * np.pi * frequency * t + phase)
        elif waveform == 'square':
            samples = np.sign(np.sin(2 * np.pi * frequency * t + phase))
        elif waveform == 'sawtooth':
            samples = 2 * (frequency * t % 1) - 1
        elif waveform == 'triangle':
            samples = 2 * np.abs(2 * (frequency * t % 1) - 1) - 1
        else:
            samples = np.sin(2 * np.pi * frequency * t + phase)
        
        # Convert to 16-bit PCM
        samples = (samples * 32767).astype(np.int16)
        audio_data = samples.tobytes()
        
        return AudioSegment(
            data=audio_data,
            sample_width=2,
            frame_rate=self.sample_rate,
            channels=1
        )
    
    def bass_synth(self, frequency, duration_ms, cutoff_mod=1.0):
        """Create a fat bass sound with multiple oscillators"""
        # Main oscillator - square wave
        bass1 = self.generate_waveform(frequency, duration_ms, 'square')
        # Sub oscillator - sine wave an octave down
        bass2 = self.generate_waveform(frequency / 2, duration_ms, 'sine')
        # Slight detune for fatness
        bass3 = self.generate_waveform(frequency * 1.01, duration_ms, 'sawtooth')
        
        # Mix oscillators
        bass = bass1.overlay(bass2 - 3).overlay(bass3 - 6)
        
        # Apply envelope (ADSR-like)
        bass = self.apply_envelope(bass, attack=5, decay=50, sustain=0.7, release=100)
        
        return bass
    
    def lead_synth(self, frequency, duration_ms, cutoff=1.0):
        """Create an aggressive lead sound"""
        # Detuned sawtooth oscillators
        lead1 = self.generate_waveform(frequency, duration_ms, 'sawtooth')
        lead2 = self.generate_waveform(frequency * 1.005, duration_ms, 'sawtooth')
        lead3 = self.generate_waveform(frequency * 0.995, duration_ms, 'square')
        
        # Mix and apply envelope
        lead = lead1.overlay(lead2 - 2).overlay(lead3 - 4)
        lead = self.apply_envelope(lead, attack=10, decay=100, sustain=0.6, release=150)
        
        return lead
    
    def acid_bass(self, frequency, duration_ms, resonance=0.8):
        """Create a 303-style acid bass"""
        # Sawtooth base
        acid = self.generate_waveform(frequency, duration_ms, 'sawtooth')
        # Add some square for bite
        acid = acid.overlay(self.generate_waveform(frequency, duration_ms, 'square') - 6)
        
        # Aggressive envelope
        acid = self.apply_envelope(acid, attack=1, decay=80, sustain=0.3, release=50)
        
        return acid
    
    def pad_synth(self, frequency, duration_ms):
        """Create a lush pad sound"""
        # Multiple detuned sines
        pad = self.generate_waveform(frequency, duration_ms, 'sine')
        pad = pad.overlay(self.generate_waveform(frequency * 1.01, duration_ms, 'sine') - 3)
        pad = pad.overlay(self.generate_waveform(frequency * 0.99, duration_ms, 'sine') - 3)
        pad = pad.overlay(self.generate_waveform(frequency * 2, duration_ms, 'sine') - 8)
        
        # Slow attack, long release
        pad = self.apply_envelope(pad, attack=200, decay=300, sustain=0.8, release=400)
        
        return pad
    
    def apply_envelope(self, audio, attack=10, decay=100, sustain=0.7, release=100):
        """Apply ADSR envelope to audio"""
        total_ms = len(audio)
        
        # Create fade in (attack)
        if attack > 0:
            audio = audio.fade_in(min(attack, total_ms // 2))
        
        # Create fade out (release)
        if release > 0:
            audio = audio.fade_out(min(release, total_ms // 2))
        
        return audio

class DrumMachine:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def kick(self, duration_ms=300):
        """Generate a punchy techno kick"""
        # Start at high freq and sweep down
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        # Frequency sweep from 150Hz to 40Hz
        freq = 150 * np.exp(-t * 10)
        phase = np.cumsum(2 * np.pi * freq / self.sample_rate)
        
        # Generate sine wave
        kick = np.sin(phase)
        
        # Apply exponential decay envelope
        envelope = np.exp(-t * 12)
        kick = kick * envelope
        
        # Add click for punch
        click = np.exp(-t * 50)
        kick = kick + click * 0.3
        
        # Clip and convert
        kick = np.clip(kick, -1, 1)
        kick = (kick * 32767).astype(np.int16)
        
        audio = AudioSegment(
            data=kick.tobytes(),
            sample_width=2,
            frame_rate=self.sample_rate,
            channels=1
        )
        
        return audio + 3  # Boost kick
    
    def snare(self, duration_ms=200):
        """Generate a snare"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        # Tone component (200Hz)
        tone = np.sin(2 * np.pi * 200 * t)
        
        # Noise component
        noise = np.random.randn(num_samples)
        
        # Mix tone and noise
        snare = tone * 0.3 + noise * 0.7
        
        # Apply envelope
        envelope = np.exp(-t * 20)
        snare = snare * envelope
        
        snare = np.clip(snare, -1, 1)
        snare = (snare * 32767 * 0.6).astype(np.int16)
        
        return AudioSegment(
            data=snare.tobytes(),
            sample_width=2,
            frame_rate=self.sample_rate,
            channels=1
        )
    
    def hihat(self, duration_ms=50, closed=True):
        """Generate hi-hat"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        # High-frequency noise
        hihat = np.random.randn(num_samples)
        
        # High-pass character using multiple sines
        for freq in [8000, 10000, 12000]:
            hihat += np.sin(2 * np.pi * freq * t) * 0.1
        
        # Envelope
        decay = 40 if closed else 15
        envelope = np.exp(-t * decay)
        hihat = hihat * envelope
        
        hihat = np.clip(hihat, -1, 1)
        gain = 0.3 if closed else 0.4
        hihat = (hihat * 32767 * gain).astype(np.int16)
        
        return AudioSegment(
            data=hihat.tobytes(),
            sample_width=2,
            frame_rate=self.sample_rate,
            channels=1
        )
    
    def clap(self, duration_ms=150):
        """Generate a clap"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        # Noise burst
        clap = np.random.randn(num_samples)
        
        # Multiple attacks for realistic clap
        envelope = (np.exp(-t * 30) + 
                   np.exp(-(t - 0.01) * 30) * 0.8 +
                   np.exp(-(t - 0.02) * 30) * 0.6)
        envelope = np.maximum(envelope, 0)
        
        clap = clap * envelope
        clap = np.clip(clap, -1, 1)
        clap = (clap * 32767 * 0.5).astype(np.int16)
        
        return AudioSegment(
            data=clap.tobytes(),
            sample_width=2,
            frame_rate=self.sample_rate,
            channels=1
        )

def midi_to_freq(midi_note):
    """Convert MIDI note number to frequency"""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

def parse_midi_file(filepath):
    """Extract note patterns from MIDI file"""
    mid = mido.MidiFile(filepath)
    notes = []
    
    for track in mid.tracks:
        time = 0
        for msg in track:
            time += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append({
                    'note': msg.note,
                    'velocity': msg.velocity,
                    'time': time
                })
    
    return notes

def generate_epic_techno_track():
    """Generate an EPIC techno track with MIDI inspiration"""
    print("🎵 Initializing epic techno generation...")
    
    # Constants
    bpm = 128
    beat_duration = 60000 / bpm  # ~468ms per beat
    bar_duration = beat_duration * 4  # ~1875ms per bar
    
    # Initialize synthesizers
    synth = Synthesizer()
    drums = DrumMachine()
    
    # Parse MIDI files for inspiration
    print("🎹 Parsing MIDI files for musical patterns...")
    try:
        midi_notes_1 = parse_midi_file('reference/Lower Norfair 2 MIDI.mid')
        midi_notes_2 = parse_midi_file('reference/lower-norfair-2-.mid')
        all_midi_notes = midi_notes_1 + midi_notes_2
        print(f"   Found {len(all_midi_notes)} notes to inspire our track!")
    except:
        print("   Using generated patterns instead")
        all_midi_notes = []
    
    # Extract unique notes for our sequences
    if all_midi_notes:
        unique_notes = list(set([n['note'] for n in all_midi_notes[:32]]))
        bass_notes = [n for n in unique_notes if n < 60][:8]
        lead_notes = [n for n in unique_notes if n >= 60][:8]
    else:
        # Fallback patterns
        bass_notes = [36, 38, 41, 43, 36, 38, 46, 43]  # C, D, F, G pattern
        lead_notes = [60, 63, 67, 70, 72, 70, 67, 63]  # C minor scale
    
    print(f"   Bass pattern: {bass_notes}")
    print(f"   Lead pattern: {lead_notes}")
    
    # Create the track structure (32 bars = ~60 seconds)
    num_bars = 48
    track_duration = bar_duration * num_bars
    
    print(f"🎛️  Generating {num_bars} bars of pure techno energy...")
    
    # Initialize empty track
    track = AudioSegment.silent(duration=int(track_duration))
    
    # SECTION 1: Build-up (Bars 0-8)
    print("   [Section 1] Building tension...")
    for bar in range(8):
        bar_start = int(bar * bar_duration)
        
        # Kick drum (every beat from bar 4)
        if bar >= 4:
            for beat in range(4):
                kick_pos = bar_start + int(beat * beat_duration)
                track = track.overlay(drums.kick(), position=kick_pos)
        
        # Hi-hats (16th notes from bar 2)
        if bar >= 2:
            for sixteenth in range(16):
                hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
                track = track.overlay(drums.hihat(closed=True), position=hihat_pos)
        
        # Bass (enters bar 6)
        if bar >= 6:
            for beat in range(4):
                note_idx = (bar * 4 + beat) % len(bass_notes)
                bass_note = bass_notes[note_idx]
                bass_freq = midi_to_freq(bass_note)
                bass_pos = bar_start + int(beat * beat_duration)
                bass_sound = synth.bass_synth(bass_freq, beat_duration * 0.9)
                track = track.overlay(bass_sound - 6, position=bass_pos)
    
    # SECTION 2: Main drop (Bars 8-24)
    print("   [Section 2] DROPPING THE BASS 💥")
    for bar in range(8, 24):
        bar_start = int(bar * bar_duration)
        
        # Four-to-the-floor kick
        for beat in range(4):
            kick_pos = bar_start + int(beat * beat_duration)
            track = track.overlay(drums.kick(), position=kick_pos)
        
        # Snare on 2 and 4
        for snare_beat in [1, 3]:
            snare_pos = bar_start + int(snare_beat * beat_duration)
            track = track.overlay(drums.snare(), position=snare_pos)
        
        # 16th note hi-hats
        for sixteenth in range(16):
            hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
            closed = sixteenth % 4 != 3
            track = track.overlay(drums.hihat(closed=closed), position=hihat_pos)
        
        # Clap layers
        if bar % 2 == 1:
            for clap_beat in [1, 3]:
                clap_pos = bar_start + int(clap_beat * beat_duration + beat_duration/2)
                track = track.overlay(drums.clap() - 3, position=clap_pos)
        
        # Aggressive acid bass line
        for beat in range(4):
            note_idx = (bar * 4 + beat) % len(bass_notes)
            bass_note = bass_notes[note_idx]
            bass_freq = midi_to_freq(bass_note)
            bass_pos = bar_start + int(beat * beat_duration)
            
            # Alternate between bass types
            if bar % 4 < 2:
                bass_sound = synth.acid_bass(bass_freq, beat_duration * 0.85)
            else:
                bass_sound = synth.bass_synth(bass_freq, beat_duration * 0.9)
            
            track = track.overlay(bass_sound - 5, position=bass_pos)
        
        # Lead synth (enters bar 12)
        if bar >= 12:
            # Play lead on every other beat
            for lead_step in range(8):
                if random.random() > 0.3:  # Add some variation
                    note_idx = (bar * 8 + lead_step) % len(lead_notes)
                    lead_note = lead_notes[note_idx]
                    lead_freq = midi_to_freq(lead_note)
                    lead_pos = bar_start + int(lead_step * beat_duration / 2)
                    lead_sound = synth.lead_synth(lead_freq, beat_duration * 0.4)
                    track = track.overlay(lead_sound - 10, position=lead_pos)
        
        # Add pads for atmosphere (from bar 16)
        if bar >= 16 and bar % 4 == 0:
            pad_note = lead_notes[bar % len(lead_notes)]
            pad_freq = midi_to_freq(pad_note)
            pad_sound = synth.pad_synth(pad_freq, bar_duration * 4)
            track = track.overlay(pad_sound - 18, position=bar_start)
    
    # SECTION 3: Breakdown (Bars 24-32)
    print("   [Section 3] Breaking it down...")
    for bar in range(24, 32):
        bar_start = int(bar * bar_duration)
        
        # Kick drops out progressively
        if bar < 28:
            for beat in range(4):
                if not (bar >= 26 and beat % 2 == 1):  # Remove some kicks
                    kick_pos = bar_start + int(beat * beat_duration)
                    track = track.overlay(drums.kick(), position=kick_pos)
        
        # Sparse hi-hats
        for eighth in range(8):
            if random.random() > 0.5:
                hihat_pos = bar_start + int(eighth * beat_duration / 2)
                track = track.overlay(drums.hihat(closed=False) - 3, position=hihat_pos)
        
        # Atmospheric pads
        if bar % 2 == 0:
            pad_note = lead_notes[(bar // 2) % len(lead_notes)]
            pad_freq = midi_to_freq(pad_note)
            pad_sound = synth.pad_synth(pad_freq, bar_duration * 2)
            track = track.overlay(pad_sound - 16, position=bar_start)
        
        # Melodic lead
        for beat in range(4):
            note_idx = (bar * 4 + beat) % len(lead_notes)
            lead_note = lead_notes[note_idx]
            lead_freq = midi_to_freq(lead_note)
            lead_pos = bar_start + int(beat * beat_duration)
            lead_sound = synth.lead_synth(lead_freq, beat_duration * 1.5)
            track = track.overlay(lead_sound - 12, position=lead_pos)
    
    # SECTION 4: Final drop (Bars 32-48)
    print("   [Section 4] FINAL DROP - Going HARD 🔥")
    for bar in range(32, 48):
        bar_start = int(bar * bar_duration)
        
        # Heavy kick
        for beat in range(4):
            kick_pos = bar_start + int(beat * beat_duration)
            track = track.overlay(drums.kick() + 2, position=kick_pos)
        
        # Layered snares and claps
        for snare_beat in [1, 3]:
            hit_pos = bar_start + int(snare_beat * beat_duration)
            track = track.overlay(drums.snare(), position=hit_pos)
            track = track.overlay(drums.clap() - 2, position=hit_pos + 10)
        
        # Complex hi-hat pattern
        for sixteenth in range(16):
            hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
            closed = not (sixteenth % 4 == 3 or sixteenth % 4 == 1)
            gain_adj = -2 if sixteenth % 4 == 0 else -4
            track = track.overlay(drums.hihat(closed=closed) + gain_adj, position=hihat_pos)
        
        # Two bass layers for maximum impact
        for beat in range(4):
            note_idx = (bar * 4 + beat) % len(bass_notes)
            bass_note = bass_notes[note_idx]
            bass_freq = midi_to_freq(bass_note)
            bass_pos = bar_start + int(beat * beat_duration)
            
            # Layer 1: Deep sub
            bass1 = synth.bass_synth(bass_freq, beat_duration * 0.9)
            track = track.overlay(bass1 - 4, position=bass_pos)
            
            # Layer 2: Acid line
            if beat % 2 == 0:
                bass2 = synth.acid_bass(bass_freq * 2, beat_duration * 0.6)
                track = track.overlay(bass2 - 8, position=bass_pos)
        
        # Aggressive lead stabs
        if bar % 2 == 0:
            for stab in range(4):
                if random.random() > 0.2:
                    note_idx = (bar * 4 + stab) % len(lead_notes)
                    lead_note = lead_notes[note_idx] + (12 if stab % 2 else 0)
                    lead_freq = midi_to_freq(lead_note)
                    stab_pos = bar_start + int(stab * beat_duration)
                    lead_sound = synth.lead_synth(lead_freq, beat_duration * 0.3)
                    track = track.overlay(lead_sound - 8, position=stab_pos)
        
        # Pad layers for depth
        if bar % 4 == 0:
            pad_note = lead_notes[0]  # Root note
            pad_freq = midi_to_freq(pad_note)
            pad_sound = synth.pad_synth(pad_freq, bar_duration * 4)
            track = track.overlay(pad_sound - 20, position=bar_start)
    
    # Apply mastering effects
    print("🎚️  Applying mastering effects...")
    
    # Subtle compression (normalize, then reduce peaks)
    track = track.normalize()
    
    # Add some saturation/warmth by subtle clipping
    track = track + 1
    
    # Final limiting
    track = track.normalize(headroom=0.5)
    
    print("💾 Exporting epic techno track...")
    track.export("epic_techno_masterpiece.wav", format="wav")
    print("✅ DONE! Your epic techno track is ready: epic_techno_masterpiece.wav")
    print(f"   Duration: {len(track) / 1000:.1f} seconds ({num_bars} bars @ {bpm} BPM)")
    print("   🔊 Turn it up and feel the bass!")

if __name__ == "__main__":
    generate_epic_techno_track()
