# 🎵 Super Metroid Techno

A Python-based techno music generator that creates epic tracks using synthesized sounds and MIDI-inspired patterns from Super Metroid.

Built entirely from scratch using numpy DSP and custom synthesizers.

## 📦 Setup + Run

```bash
# Install dependencies (includes pygame and pyaudio for playback)
pip install -r requirements.txt

# Generate a static track
python track02.py

# Run the INFINITE generator (with visualizations + real-time audio!)
python super_metroid_infinite.py
```

**Note:** Recording starts automatically when you launch the infinite generator! Press SPACE to stop/start recording.

## 🎮 Super Metroid Infinite

The **infinite generator** is where things get wild! It:

- 🎹 Analyzes ALL MIDI tracks in the `reference/` folder
- 🔀 Randomly combines basslines, melodies, pads, and arpeggios
- 🎨 Creates a constantly evolving, never-repeating track
- 🎚️ Applies random effects (reverb, delay, distortion)
- 📺 Shows real-time audio-reactive chaos visualizations (640x480)
- 💾 Records to WAV files with timestamps
- 🎵 **Dynamic sections**: Intro → Verse → Chorus → Breakdown with different intensities
- 🔊 **Prominent choruses** with layered leads and big sound
- 🎸 **Slower bass changes** for more coherent groove (16-32 bars)

### Controls:
- **SPACE** or **Click Button** - Toggle recording
- **V** - Toggle visualization mode (640x480 full / 320x120 minimal)
- **ESC** - Quit

The generator will save files as `sm_infinite_<timestamp>.wav` when you're recording!

Watch the screen for section changes (INTRO/VERSE/**CHORUS**/BREAKDOWN) - choruses hit HARD! 🔥

**Pro tip:** Press **V** to switch to minimal mode (320x120, black screen) for lower CPU usage during long recordings! 💻

## 🎧 More Music

Want to hear more? Check out my SoundCloud:

**[soundcloud.com/kenny-cason](https://soundcloud.com/kenny-cason)**

