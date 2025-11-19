# 🎵 Super Metroid Techno

A Python-based techno music generator that creates epic tracks using synthesized sounds and MIDI-inspired patterns from Super Metroid.

Built entirely from scratch using numpy DSP and custom synthesizers.

## 📦 Setup + Run

```bash
pip install -r requirements.txt

# Generate a static track
python track02.py

# Run the INFINITE generator (with visualizations!)
python super_metroid_infinite.py
```

## 🎮 Super Metroid Infinite

The **infinite generator** is where things get wild! It:

- 🎹 Analyzes ALL MIDI tracks in the `reference/` folder
- 🔀 Randomly combines basslines, melodies, pads, and arpeggios
- 🎨 Creates a constantly evolving, never-repeating track
- 🎚️ Applies random effects (reverb, delay, distortion)
- 📺 Shows real-time audio-reactive visualizations (640x480)
- 💾 Records to WAV files with timestamps

### Controls:
- **SPACE** or **Click Button** - Toggle recording
- **ESC** - Quit

The generator will save files as `sm_infinite_<timestamp>.wav` when you're recording!

## 🎧 More Music

Want to hear more? Check out my SoundCloud:

**[soundcloud.com/kenny-cason](https://soundcloud.com/kenny-cason)**

