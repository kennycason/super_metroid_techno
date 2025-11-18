import mido
import os
from collections import defaultdict

def analyze_midi(filepath):
    """Comprehensive MIDI analysis"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {os.path.basename(filepath)}")
    print(f"{'='*60}")
    
    try:
        mid = mido.MidiFile(filepath)
        print(f"Type: {mid.type}")
        print(f"Number of tracks: {len(mid.tracks)}")
        print(f"Ticks per beat: {mid.ticks_per_beat}")
        
        # Analyze each track
        for i, track in enumerate(mid.tracks):
            print(f"\n--- Track {i}: {track.name} ---")
            
            notes_by_channel = defaultdict(list)
            time = 0
            tempo = 500000  # Default tempo (120 BPM)
            
            for msg in track:
                time += msg.time
                
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                    bpm = mido.tempo2bpm(tempo)
                    print(f"  Tempo: {bpm:.1f} BPM")
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes_by_channel[msg.channel].append({
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'time': time,
                        'channel': msg.channel
                    })
            
            # Print note statistics per channel
            for channel, notes in notes_by_channel.items():
                if notes:
                    note_nums = [n['note'] for n in notes]
                    print(f"  Channel {channel}:")
                    print(f"    Notes: {len(notes)}")
                    print(f"    Range: {min(note_nums)} - {max(note_nums)}")
                    print(f"    Unique notes: {sorted(set(note_nums))[:20]}")  # First 20
                    
                    # Sample first few notes with timing
                    print(f"    First 8 notes pattern:")
                    for note in notes[:8]:
                        note_name = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][note['note'] % 12]
                        octave = note['note'] // 12 - 1
                        print(f"      {note_name}{octave} (MIDI {note['note']}) @ tick {note['time']}, vel {note['velocity']}")
        
        return mid
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Analyze all MIDI files
    midi_files = [
        'reference/Lower Norfair 2 MIDI.mid',
        'reference/brinstar-1-2-.mid',
        'reference/introduction.mid'
    ]
    
    for filepath in midi_files:
        if os.path.exists(filepath):
            analyze_midi(filepath)
        else:
            print(f"File not found: {filepath}")

