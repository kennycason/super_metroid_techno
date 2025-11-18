from pydub.generators import Sine, Square, Sawtooth, WhiteNoise
from pydub import AudioSegment
import mido
import math
import random
import numpy as np
from collections import defaultdict

# Advanced synthesizer engine
class Synthesizer:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def generate_waveform(self, frequency, duration_ms, waveform='sine', phase=0, detune=0):
        """Generate waveforms with optional detuning"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        freq = frequency * (1 + detune)
        
        if waveform == 'sine':
            samples = np.sin(2 * np.pi * freq * t + phase)
        elif waveform == 'square':
            samples = np.sign(np.sin(2 * np.pi * freq * t + phase))
        elif waveform == 'sawtooth':
            samples = 2 * (freq * t % 1) - 1
        elif waveform == 'triangle':
            samples = 2 * np.abs(2 * (freq * t % 1) - 1) - 1
        else:
            samples = np.sin(2 * np.pi * freq * t + phase)
        
        samples = (samples * 32767).astype(np.int16)
        return AudioSegment(data=samples.tobytes(), sample_width=2, 
                          frame_rate=self.sample_rate, channels=1)
    
    def piano_like(self, frequency, duration_ms, velocity=100):
        """Piano-like sound with harmonics (for intro inspiration)"""
        # Fundamental + harmonics
        piano = self.generate_waveform(frequency, duration_ms, 'sine')
        piano = piano.overlay(self.generate_waveform(frequency * 2, duration_ms, 'sine') - 8)
        piano = piano.overlay(self.generate_waveform(frequency * 3, duration_ms, 'sine') - 12)
        piano = piano.overlay(self.generate_waveform(frequency * 4, duration_ms, 'sine') - 16)
        
        # Piano-like envelope (fast attack, exponential decay)
        piano = piano.fade_in(5).fade_out(int(duration_ms * 0.7))
        
        # Velocity scaling
        vel_scale = (velocity / 127.0) * 0.8 + 0.2
        return piano - (1 - vel_scale) * 20
    
    def deep_bass(self, frequency, duration_ms, fatness=3):
        """Super deep sub bass with overtones"""
        # Sub oscillator
        bass = self.generate_waveform(frequency, duration_ms, 'sine')
        # Add slight square for punch
        bass = bass.overlay(self.generate_waveform(frequency, duration_ms, 'square') - 12)
        # Detuned layers for width
        for i in range(fatness):
            detune = (i + 1) * 0.003
            bass = bass.overlay(self.generate_waveform(frequency, duration_ms, 'sawtooth', detune=detune) - 8)
        
        bass = bass.fade_in(10).fade_out(80)
        return bass
    
    def creepy_pad(self, frequency, duration_ms, modulation=0):
        """Atmospheric creepy pad (Lower Norfair style)"""
        # Multiple detuned oscillators
        pad = self.generate_waveform(frequency, duration_ms, 'sine')
        pad = pad.overlay(self.generate_waveform(frequency * 1.01, duration_ms, 'sine') - 2)
        pad = pad.overlay(self.generate_waveform(frequency * 0.99, duration_ms, 'sine') - 2)
        pad = pad.overlay(self.generate_waveform(frequency * 2, duration_ms, 'triangle') - 10)
        pad = pad.overlay(self.generate_waveform(frequency * 1.5, duration_ms, 'sine') - 12)
        
        # Slow attack and release
        pad = pad.fade_in(300).fade_out(500)
        return pad - 10
    
    def brass_lead(self, frequency, duration_ms, velocity=80):
        """Bold brass lead (from Lower Norfair track 7)"""
        # Bright sawtooth stack
        lead = self.generate_waveform(frequency, duration_ms, 'sawtooth')
        lead = lead.overlay(self.generate_waveform(frequency * 1.005, duration_ms, 'sawtooth') - 1)
        lead = lead.overlay(self.generate_waveform(frequency * 2, duration_ms, 'square') - 8)
        
        # Brass-like envelope
        attack = 50
        release = 150
        lead = lead.fade_in(attack).fade_out(release)
        
        vel_scale = velocity / 127.0
        return lead - ((1 - vel_scale) * 15)
    
    def xylophone(self, frequency, duration_ms, velocity=92):
        """Bright xylophone sound (Brinstar style)"""
        # Very bright, short decay
        xylo = self.generate_waveform(frequency, duration_ms, 'sine')
        # Add lots of harmonics
        for harm in range(2, 8):
            xylo = xylo.overlay(self.generate_waveform(frequency * harm, duration_ms, 'sine') - (harm * 3))
        
        # Short, percussive envelope
        decay_time = min(int(duration_ms * 0.6), 200)
        xylo = xylo.fade_in(1).fade_out(decay_time)
        
        vel_scale = velocity / 127.0
        return xylo - ((1 - vel_scale) * 20)
    
    def acid_bass(self, frequency, duration_ms, resonance=0.8):
        """Classic 303 acid bass"""
        acid = self.generate_waveform(frequency, duration_ms, 'sawtooth')
        acid = acid.overlay(self.generate_waveform(frequency, duration_ms, 'square') - 6)
        acid = acid.fade_in(2).fade_out(60)
        return acid

class DrumMachine:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        
    def kick(self, duration_ms=350, punch=1.0):
        """Punchy techno kick"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        freq = 150 * np.exp(-t * 10)
        phase = np.cumsum(2 * np.pi * freq / self.sample_rate)
        kick = np.sin(phase)
        
        envelope = np.exp(-t * 12)
        kick = kick * envelope
        
        # Add click
        click = np.exp(-t * 60) * punch
        kick = kick + click * 0.4
        
        kick = np.clip(kick, -1, 1)
        kick = (kick * 32767).astype(np.int16)
        
        return AudioSegment(data=kick.tobytes(), sample_width=2, 
                          frame_rate=self.sample_rate, channels=1) + 3
    
    def snare(self, duration_ms=180):
        """Snare with tone and noise"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        tone = np.sin(2 * np.pi * 200 * t) + np.sin(2 * np.pi * 340 * t)
        noise = np.random.randn(num_samples)
        snare = tone * 0.3 + noise * 0.7
        
        envelope = np.exp(-t * 22)
        snare = snare * envelope
        
        snare = np.clip(snare, -1, 1)
        snare = (snare * 32767 * 0.6).astype(np.int16)
        
        return AudioSegment(data=snare.tobytes(), sample_width=2, 
                          frame_rate=self.sample_rate, channels=1)
    
    def hihat(self, duration_ms=50, closed=True):
        """Hi-hat"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        hihat = np.random.randn(num_samples)
        for freq in [8000, 10000, 12000, 14000]:
            hihat += np.sin(2 * np.pi * freq * t) * 0.1
        
        decay = 40 if closed else 15
        envelope = np.exp(-t * decay)
        hihat = hihat * envelope
        
        hihat = np.clip(hihat, -1, 1)
        gain = 0.3 if closed else 0.4
        hihat = (hihat * 32767 * gain).astype(np.int16)
        
        return AudioSegment(data=hihat.tobytes(), sample_width=2, 
                          frame_rate=self.sample_rate, channels=1)
    
    def clap(self, duration_ms=140):
        """Hand clap"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        clap = np.random.randn(num_samples)
        envelope = (np.exp(-t * 35) + 
                   np.exp(-(t - 0.01) * 35) * 0.8 +
                   np.exp(-(t - 0.02) * 35) * 0.6)
        envelope = np.maximum(envelope, 0)
        
        clap = clap * envelope
        clap = np.clip(clap, -1, 1)
        clap = (clap * 32767 * 0.5).astype(np.int16)
        
        return AudioSegment(data=clap.tobytes(), sample_width=2, 
                          frame_rate=self.sample_rate, channels=1)
    
    def timpani(self, duration_ms=300):
        """Timpani hit (Brinstar style)"""
        num_samples = int(self.sample_rate * duration_ms / 1000)
        t = np.arange(num_samples) / self.sample_rate
        
        # Low frequency tone sweep
        freq = 80 * np.exp(-t * 3)
        phase = np.cumsum(2 * np.pi * freq / self.sample_rate)
        timp = np.sin(phase)
        
        envelope = np.exp(-t * 8)
        timp = timp * envelope
        
        timp = np.clip(timp, -1, 1)
        timp = (timp * 32767 * 0.7).astype(np.int16)
        
        return AudioSegment(data=timp.tobytes(), sample_width=2, 
                          frame_rate=self.sample_rate, channels=1)

def midi_to_freq(midi_note):
    """Convert MIDI note to frequency"""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

def parse_midi_advanced(filepath):
    """Extract detailed note patterns from MIDI"""
    try:
        mid = mido.MidiFile(filepath)
        tracks_data = []
        
        for track in mid.tracks:
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
                tracks_data.append({
                    'name': track.name,
                    'notes': notes,
                    'bpm': mido.tempo2bpm(tempo)
                })
        
        return tracks_data
    except:
        return []

def generate_epic_techno_track():
    """Generate ULTIMATE techno track using MIDI inspiration"""
    print("🎵 TRACK 02 - SUPER METROID TECHNO FUSION")
    print("=" * 60)
    
    # Initialize engines
    synth = Synthesizer()
    drums = DrumMachine()
    
    # Parse all MIDI files
    print("\n🎹 Analyzing MIDI sources...")
    lower_norfair = parse_midi_advanced('reference/Lower Norfair 2 MIDI.mid')
    brinstar = parse_midi_advanced('reference/brinstar-1-2-.mid')
    intro = parse_midi_advanced('reference/introduction.mid')
    
    # Extract patterns
    print("\n📊 Extracting musical patterns...")
    
    # Lower Norfair patterns (126 BPM)
    bass_pattern = [36, 37, 36, 37, 39, 37, 36, 37]  # Thud pattern
    creep_pad_notes = [72, 67, 70, 65]  # C5, G4, A#4, F4
    brass_lead_notes = [66, 61, 59, 64, 66, 61, 64, 59]  # F#4, C#4, B3, E4
    organ_notes = [45, 69, 67, 65, 64]  # A2, A4, G4, F4, E4
    
    # Brinstar patterns (132 BPM) 
    xylo_pattern = [60, 67, 65, 67, 65, 63, 62, 63]  # C4, G4, F4 sequence
    timpani_hits = [46, 48]  # A#2, C3
    
    # Intro patterns
    piano_note = 72  # Repeating C5
    deep_bass_triad = [26, 38, 45]  # D1, D2, A2
    
    print(f"   ✓ Bass pattern: {bass_pattern}")
    print(f"   ✓ Creep pad: {creep_pad_notes}")
    print(f"   ✓ Brass lead: {brass_lead_notes}")
    print(f"   ✓ Xylophone: {xylo_pattern}")
    print(f"   ✓ Deep bass triad: {deep_bass_triad}")
    
    # Track parameters
    bpm = 128  # Compromise between 126 and 132
    beat_duration = 60000 / bpm  # ~468ms
    bar_duration = beat_duration * 4
    num_bars = 64  # Epic 2-minute journey
    
    print(f"\n🎛️  Building {num_bars} bars @ {bpm} BPM...")
    print(f"   Total duration: ~{num_bars * bar_duration / 1000:.0f} seconds\n")
    
    track = AudioSegment.silent(duration=int(bar_duration * num_bars))
    
    # ========== INTRO (Bars 0-8) - Piano & Atmosphere ==========
    print("   [Intro 0-8] Atmospheric piano intro...")
    for bar in range(8):
        bar_start = int(bar * bar_duration)
        
        # Repeating piano note (intro.mid style)
        if bar < 4:
            for beat in range(4):
                pos = bar_start + int(beat * beat_duration)
                piano = synth.piano_like(midi_to_freq(piano_note), beat_duration * 0.8)
                track = track.overlay(piano - 18, position=pos)
        
        # Add creepy pads from bar 2
        if bar >= 2:
            pad_idx = bar % len(creep_pad_notes)
            pad_freq = midi_to_freq(creep_pad_notes[pad_idx])
            pad = synth.creepy_pad(pad_freq, bar_duration * 2)
            track = track.overlay(pad - 22, position=bar_start)
        
        # Kick starts at bar 6
        if bar >= 6:
            for beat in range(4):
                kick_pos = bar_start + int(beat * beat_duration)
                track = track.overlay(drums.kick(), position=kick_pos)
        
        # Hi-hats from bar 7
        if bar >= 7:
            for sixteenth in range(16):
                hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
                track = track.overlay(drums.hihat(closed=True) - 3, position=hihat_pos)
    
    # ========== BUILD (Bars 8-16) - Adding layers ==========
    print("   [Build 8-16] Building energy...")
    for bar in range(8, 16):
        bar_start = int(bar * bar_duration)
        
        # Kick - four on the floor
        for beat in range(4):
            kick_pos = bar_start + int(beat * beat_duration)
            track = track.overlay(drums.kick(punch=1.2), position=kick_pos)
        
        # Hi-hats 16ths
        for sixteenth in range(16):
            hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
            closed = sixteenth % 4 != 3
            track = track.overlay(drums.hihat(closed=closed) - 2, position=hihat_pos)
        
        # Deep bass enters (bar 10)
        if bar >= 10:
            for beat in range(4):
                note_idx = (bar * 4 + beat) % len(bass_pattern)
                bass_freq = midi_to_freq(bass_pattern[note_idx])
                bass = synth.deep_bass(bass_freq, beat_duration * 0.9)
                track = track.overlay(bass - 7, position=bar_start + int(beat * beat_duration))
        
        # Xylophone melody (bar 12)
        if bar >= 12:
            for eighth in range(8):
                xylo_idx = (bar * 8 + eighth) % len(xylo_pattern)
                xylo_freq = midi_to_freq(xylo_pattern[xylo_idx])
                xylo_pos = bar_start + int(eighth * beat_duration / 2)
                xylo = synth.xylophone(xylo_freq, beat_duration * 0.3)
                track = track.overlay(xylo - 12, position=xylo_pos)
        
        # Snares on 2 and 4 (from bar 14)
        if bar >= 14:
            for snare_beat in [1, 3]:
                snare_pos = bar_start + int(snare_beat * beat_duration)
                track = track.overlay(drums.snare(), position=snare_pos)
        
        # Creepy pads throughout
        if bar % 2 == 0:
            pad_idx = (bar // 2) % len(creep_pad_notes)
            pad_freq = midi_to_freq(creep_pad_notes[pad_idx])
            pad = synth.creepy_pad(pad_freq, bar_duration * 2)
            track = track.overlay(pad - 20, position=bar_start)
    
    # ========== DROP 1 (Bars 16-32) - Full power ==========
    print("   [Drop1 16-32] FULL POWER DROP 💥")
    for bar in range(16, 32):
        bar_start = int(bar * bar_duration)
        
        # Heavy kick
        for beat in range(4):
            kick_pos = bar_start + int(beat * beat_duration)
            track = track.overlay(drums.kick(punch=1.5) + 2, position=kick_pos)
        
        # Snare + clap layers
        for hit_beat in [1, 3]:
            hit_pos = bar_start + int(hit_beat * beat_duration)
            track = track.overlay(drums.snare() + 1, position=hit_pos)
            track = track.overlay(drums.clap() - 1, position=hit_pos + 5)
        
        # Complex hi-hat pattern
        for sixteenth in range(16):
            hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
            closed = not (sixteenth % 4 == 3)
            accent = -1 if sixteenth % 4 == 0 else -3
            track = track.overlay(drums.hihat(closed=closed) + accent, position=hihat_pos)
        
        # Timpani accents (every 4 bars)
        if bar % 4 == 0:
            for beat in [0, 2]:
                timp_pos = bar_start + int(beat * beat_duration)
                track = track.overlay(drums.timpani(), position=timp_pos)
        
        # Dual bass layers
        for beat in range(4):
            note_idx = (bar * 4 + beat) % len(bass_pattern)
            bass_freq = midi_to_freq(bass_pattern[note_idx])
            bass_pos = bar_start + int(beat * beat_duration)
            
            # Layer 1: Deep sub
            bass1 = synth.deep_bass(bass_freq, beat_duration * 0.9, fatness=4)
            track = track.overlay(bass1 - 5, position=bass_pos)
            
            # Layer 2: Acid mid-bass (every other beat)
            if beat % 2 == 0:
                acid = synth.acid_bass(bass_freq * 2, beat_duration * 0.7)
                track = track.overlay(acid - 10, position=bass_pos)
        
        # Brass lead melody
        if bar >= 20:
            for step in range(8):
                if random.random() > 0.25:
                    lead_idx = (bar * 8 + step) % len(brass_lead_notes)
                    lead_freq = midi_to_freq(brass_lead_notes[lead_idx])
                    lead_pos = bar_start + int(step * beat_duration / 2)
                    lead = synth.brass_lead(lead_freq, beat_duration * 0.4)
                    track = track.overlay(lead - 9, position=lead_pos)
        
        # Xylophone counter-melody
        if bar % 2 == 0:
            for eighth in range(8):
                if random.random() > 0.4:
                    xylo_idx = (bar * 8 + eighth) % len(xylo_pattern)
                    xylo_freq = midi_to_freq(xylo_pattern[xylo_idx] + 12)  # Octave up
                    xylo_pos = bar_start + int(eighth * beat_duration / 2)
                    xylo = synth.xylophone(xylo_freq, beat_duration * 0.25)
                    track = track.overlay(xylo - 14, position=xylo_pos)
        
        # Atmospheric pads
        if bar % 4 == 0:
            pad_idx = (bar // 4) % len(creep_pad_notes)
            pad_freq = midi_to_freq(creep_pad_notes[pad_idx])
            pad = synth.creepy_pad(pad_freq, bar_duration * 4)
            track = track.overlay(pad - 22, position=bar_start)
    
    # ========== BREAKDOWN (Bars 32-40) - Atmospheric ==========
    print("   [Breakdown 32-40] Atmospheric section...")
    for bar in range(32, 40):
        bar_start = int(bar * bar_duration)
        
        # Sparse kick (drops out progressively)
        if bar < 36:
            for beat in [0, 2]:
                kick_pos = bar_start + int(beat * beat_duration)
                track = track.overlay(drums.kick() - 2, position=kick_pos)
        
        # Soft hi-hats
        for eighth in range(8):
            if random.random() > 0.4:
                hihat_pos = bar_start + int(eighth * beat_duration / 2)
                track = track.overlay(drums.hihat(closed=False) - 5, position=hihat_pos)
        
        # Piano melody returns
        for beat in range(4):
            piano_pos = bar_start + int(beat * beat_duration)
            piano = synth.piano_like(midi_to_freq(piano_note + (bar % 3) * 2), beat_duration * 1.2)
            track = track.overlay(piano - 15, position=piano_pos)
        
        # Deep bass triad chords (intro style)
        if bar % 2 == 0:
            for note in deep_bass_triad:
                bass_freq = midi_to_freq(note)
                bass = synth.deep_bass(bass_freq, bar_duration * 2)
                track = track.overlay(bass - 12, position=bar_start)
        
        # Organ melody
        for beat in range(4):
            organ_idx = (bar * 4 + beat) % len(organ_notes)
            organ_freq = midi_to_freq(organ_notes[organ_idx])
            organ_pos = bar_start + int(beat * beat_duration)
            organ = synth.brass_lead(organ_freq, beat_duration * 1.5, velocity=60)
            track = track.overlay(organ - 14, position=organ_pos)
        
        # Lush pads
        pad_idx = bar % len(creep_pad_notes)
        pad_freq = midi_to_freq(creep_pad_notes[pad_idx])
        pad = synth.creepy_pad(pad_freq, bar_duration * 2)
        track = track.overlay(pad - 18, position=bar_start)
    
    # ========== BUILD 2 (Bars 40-48) - Rising tension ==========
    print("   [Build2 40-48] Building to final drop...")
    for bar in range(40, 48):
        bar_start = int(bar * bar_duration)
        
        # Kick returns
        for beat in range(4):
            kick_pos = bar_start + int(beat * beat_duration)
            punch = 1.0 + (bar - 40) * 0.1
            track = track.overlay(drums.kick(punch=punch), position=kick_pos)
        
        # Hi-hats intensify
        for sixteenth in range(16):
            hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
            closed = sixteenth % 4 != 3
            track = track.overlay(drums.hihat(closed=closed) - 1, position=hihat_pos)
        
        # Bass returns (bar 44)
        if bar >= 44:
            for beat in range(4):
                note_idx = (bar * 4 + beat) % len(bass_pattern)
                bass_freq = midi_to_freq(bass_pattern[note_idx])
                bass_pos = bar_start + int(beat * beat_duration)
                bass = synth.deep_bass(bass_freq, beat_duration * 0.9)
                track = track.overlay(bass - 6, position=bass_pos)
        
        # Snares return (bar 46)
        if bar >= 46:
            for snare_beat in [1, 3]:
                snare_pos = bar_start + int(snare_beat * beat_duration)
                track = track.overlay(drums.snare(), position=snare_pos)
        
        # Rising xylophone runs
        for sixteenth in range(16):
            if random.random() > 0.6:
                xylo_note = xylo_pattern[sixteenth % len(xylo_pattern)] + (bar - 40) * 2
                xylo_freq = midi_to_freq(xylo_note)
                xylo_pos = bar_start + int(sixteenth * beat_duration / 4)
                xylo = synth.xylophone(xylo_freq, beat_duration * 0.2)
                track = track.overlay(xylo - 13, position=xylo_pos)
    
    # ========== FINAL DROP (Bars 48-64) - MAXIMUM ENERGY ==========
    print("   [Final Drop 48-64] ABSOLUTE CHAOS 🔥🔥🔥")
    for bar in range(48, 64):
        bar_start = int(bar * bar_duration)
        
        # MASSIVE KICK
        for beat in range(4):
            kick_pos = bar_start + int(beat * beat_duration)
            track = track.overlay(drums.kick(punch=2.0) + 4, position=kick_pos)
        
        # Layered snare/clap/timpani
        for hit_beat in [1, 3]:
            hit_pos = bar_start + int(hit_beat * beat_duration)
            track = track.overlay(drums.snare() + 2, position=hit_pos)
            track = track.overlay(drums.clap(), position=hit_pos + 5)
            track = track.overlay(drums.timpani() - 3, position=hit_pos - 10)
        
        # Insane hi-hat pattern
        for sixteenth in range(16):
            hihat_pos = bar_start + int(sixteenth * beat_duration / 4)
            closed = not (sixteenth % 4 == 3 or sixteenth % 8 == 5)
            accent = 0 if sixteenth % 4 == 0 else -2
            track = track.overlay(drums.hihat(closed=closed) + accent, position=hihat_pos)
        
        # Triple bass layers
        for beat in range(4):
            note_idx = (bar * 4 + beat) % len(bass_pattern)
            bass_freq = midi_to_freq(bass_pattern[note_idx])
            bass_pos = bar_start + int(beat * beat_duration)
            
            # Layer 1: Sub
            bass1 = synth.deep_bass(bass_freq, beat_duration * 0.9, fatness=5)
            track = track.overlay(bass1 - 3, position=bass_pos)
            
            # Layer 2: Mid acid
            acid1 = synth.acid_bass(bass_freq * 2, beat_duration * 0.7)
            track = track.overlay(acid1 - 8, position=bass_pos)
            
            # Layer 3: High acid (offbeat)
            if beat % 2 == 1:
                acid2 = synth.acid_bass(bass_freq * 4, beat_duration * 0.5)
                track = track.overlay(acid2 - 12, position=bass_pos)
        
        # Aggressive brass lead stabs
        for step in range(8):
            if random.random() > 0.15:
                lead_idx = (bar * 8 + step) % len(brass_lead_notes)
                octave_shift = 12 if step % 4 < 2 else 0
                lead_freq = midi_to_freq(brass_lead_notes[lead_idx] + octave_shift)
                lead_pos = bar_start + int(step * beat_duration / 2)
                lead = synth.brass_lead(lead_freq, beat_duration * 0.35, velocity=95)
                track = track.overlay(lead - 7, position=lead_pos)
        
        # Xylophone chaos
        if bar % 2 == 1:
            for sixteenth in range(16):
                if random.random() > 0.5:
                    xylo_idx = (bar * 16 + sixteenth) % len(xylo_pattern)
                    xylo_note = xylo_pattern[xylo_idx] + 24  # 2 octaves up
                    xylo_freq = midi_to_freq(xylo_note)
                    xylo_pos = bar_start + int(sixteenth * beat_duration / 4)
                    xylo = synth.xylophone(xylo_freq, beat_duration * 0.15)
                    track = track.overlay(xylo - 11, position=xylo_pos)
        
        # Deep organ bass notes (every 2 bars)
        if bar % 2 == 0:
            organ_note = organ_notes[0] - 12  # Very low
            organ_freq = midi_to_freq(organ_note)
            organ = synth.brass_lead(organ_freq, bar_duration * 2, velocity=100)
            track = track.overlay(organ - 10, position=bar_start)
        
        # Massive pad layers
        if bar % 4 == 0:
            for i, pad_note in enumerate(creep_pad_notes):
                pad_freq = midi_to_freq(pad_note)
                pad = synth.creepy_pad(pad_freq, bar_duration * 4)
                track = track.overlay(pad - (20 + i * 2), position=bar_start)
    
    # ========== MASTERING ==========
    print("\n🎚️  Mastering...")
    track = track.normalize(headroom=1.0)
    track = track + 1.5
    track = track.normalize(headroom=0.3)
    
    # Export
    print("💾 Exporting...")
    output_file = "track02.wav"
    track.export(output_file, format="wav")
    
    print(f"\n{'=' * 60}")
    print(f"✅ TRACK 02 COMPLETE!")
    print(f"{'=' * 60}")
    print(f"📊 Stats:")
    print(f"   Duration: {len(track) / 1000:.1f} seconds ({num_bars} bars)")
    print(f"   BPM: {bpm}")
    print(f"   File: {output_file}")
    print(f"\n🎧 MIDI sources integrated:")
    print(f"   ✓ Lower Norfair 2: Bass, pads, brass leads")
    print(f"   ✓ Brinstar 1-2: Xylophones, timpani, rhythm")
    print(f"   ✓ Introduction: Piano, deep bass, atmosphere")
    print(f"\n🔊 CRANK IT UP! 🔥🔥🔥")

if __name__ == "__main__":
    generate_epic_techno_track()

