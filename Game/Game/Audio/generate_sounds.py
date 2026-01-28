#!/usr/bin/env python3
"""
Générateur de sons style Égypte antique pour Antique War.
Crée des fichiers WAV avec des sons orientaux/égyptiens.

Usage: python generate_sounds.py
"""
import wave
import struct
import math
import os
import random

# Dossier de sortie
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sounds")
SAMPLE_RATE = 44100

# Crée le dossier de sortie pour les fichiers audio s'il n'existe pas déjà
def ensure_output_dir():
    """Crée le dossier de sortie s'il n'existe pas."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sauvegarde une liste d'échantillons audio dans un fichier WAV 16-bit mono
def save_wav(filename: str, samples: list, sample_rate: int = SAMPLE_RATE):
    """Sauvegarde les samples en fichier WAV 16-bit mono."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for sample in samples:
            # Clamp et convertir en 16-bit
            sample = max(-1.0, min(1.0, sample))
            packed = struct.pack('<h', int(sample * 32767))
            wav_file.writeframes(packed)
    
    print(f"  [OK] {filename} ({len(samples) / sample_rate:.2f}s)")

# ============================================================================
# GAMMES ORIENTALES (Maqamat)
# ============================================================================

# Maqam Hijaz - très égyptien/oriental (1, 3, 1, 2, 1, 3, 1 demi-tons)
# Retourne les fréquences de la gamme orientale Hijaz (style égyptien)
def maqam_hijaz(base_freq: float) -> list:
    """Retourne les fréquences du maqam Hijaz."""
    ratios = [1, 1.0595, 1.2599, 1.3348, 1.4983, 1.5874, 1.8877, 2.0]
    return [base_freq * r for r in ratios]

# Maqam Bayati - mélancolique (3/4, 3/4, 1, 1, 1/2, 1, 1 tons)
# Retourne les fréquences de la gamme orientale Bayati (style mélancolique)
def maqam_bayati(base_freq: float) -> list:
    """Retourne les fréquences du maqam Bayati."""
    ratios = [1, 1.0595, 1.1892, 1.3348, 1.4983, 1.5874, 1.7818, 2.0]
    return [base_freq * r for r in ratios]

# ============================================================================
# FONCTIONS DE SYNTHÈSE
# ============================================================================

# Génère une enveloppe ADSR (Attack, Decay, Sustain, Release) pour modeler le son
def envelope_adsr(t: float, attack: float, decay: float, sustain: float, 
                  release: float, duration: float) -> float:
    """Envelope ADSR."""
    if t < attack:
        return t / attack
    elif t < attack + decay:
        return 1.0 - (1.0 - sustain) * (t - attack) / decay
    elif t < duration - release:
        return sustain
    else:
        return sustain * (duration - t) / release

# Génère une enveloppe percussive avec attaque rapide et déclin exponentiel
def envelope_percussive(t: float, attack: float = 0.005, decay_rate: float = 10) -> float:
    """Envelope percussive (attaque rapide, decay exponentiel)."""
    if t < attack:
        return t / attack
    return math.exp(-(t - attack) * decay_rate)

# Génère un échantillon de bruit blanc aléatoire
def noise() -> float:
    """Génère du bruit blanc."""
    return random.uniform(-1, 1)

# Génère une onde sinusoïdale à une fréquence donnée
def sine(freq: float, t: float, phase: float = 0) -> float:
    """Onde sinusoïdale."""
    return math.sin(2 * math.pi * freq * t + phase)

# Génère une onde triangulaire à une fréquence donnée
def triangle(freq: float, t: float) -> float:
    """Onde triangulaire."""
    period = 1 / freq
    pos = (t % period) / period
    return 4 * abs(pos - 0.5) - 1

# ============================================================================
# GÉNÉRATEURS DE SONS ÉGYPTIENS
# ============================================================================

# Génère un son de doumbek (percussion égyptienne traditionnelle)
def generate_doumbek_hit() -> list:
    """Génère un son de doumbek/darbouka (percussion égyptienne)."""
    duration = 0.25
    samples = []
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        # Envelope percussive
        env = envelope_percussive(t, attack=0.002, decay_rate=15)
        
        # Corps du tambour (basses fréquences)
        body = sine(75, t) * 0.5
        body += sine(120, t) * 0.3
        
        # Attaque (membrane)
        attack_env = envelope_percussive(t, attack=0.001, decay_rate=40)
        attack = sine(280, t) * attack_env * 0.4
        attack += sine(450, t) * attack_env * 0.2
        
        # Bruit d'impact
        noise_env = envelope_percussive(t, attack=0.001, decay_rate=60)
        n = noise() * noise_env * 0.3
        
        sample = env * (body + attack) + n
        samples.append(sample * 0.8)
    
    return samples

# Génère un son 'tek' aigu et sec du doumbek
def generate_tek_sound() -> list:
    """Génère un son 'tek' aigu de doumbek."""
    duration = 0.12
    samples = []
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        env = envelope_percussive(t, attack=0.001, decay_rate=25)
        
        # Son aigu et sec
        s = sine(800, t) * 0.4
        s += sine(1200, t) * 0.3
        s += sine(2000, t) * 0.2
        
        # Bruit court
        noise_env = envelope_percussive(t, attack=0.0005, decay_rate=80)
        n = noise() * noise_env * 0.4
        
        samples.append((env * s + n) * 0.7)
    
    return samples

# Génère un son de harpe égyptienne avec harmoniques
def generate_harp_pluck(freq: float, duration: float = 0.4) -> list:
    """Génère un son de harpe égyptienne."""
    samples = []
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        # Envelope de corde pincée
        env = envelope_percussive(t, attack=0.002, decay_rate=6)
        
        # Harmoniques de harpe
        s = sine(freq, t) * 1.0
        s += sine(freq * 2, t) * 0.5
        s += sine(freq * 3, t) * 0.25
        s += sine(freq * 4, t) * 0.125
        
        # Légère désaccordage pour réalisme
        s += sine(freq * 1.002, t) * 0.1
        
        samples.append(env * s * 0.4)
    
    return samples

# Génère un son de oud (luth arabe) avec vibrato oriental
def generate_oud_note(freq: float, duration: float = 0.5) -> list:
    """Génère un son de oud (luth arabe)."""
    samples = []
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        # Envelope avec sustain
        env = envelope_adsr(t, 0.01, 0.1, 0.6, 0.15, duration)
        
        # Son de oud (riche en harmoniques)
        s = sine(freq, t) * 1.0
        s += sine(freq * 2, t) * 0.6
        s += sine(freq * 3, t) * 0.4
        s += sine(freq * 4, t) * 0.25
        s += sine(freq * 5, t) * 0.15
        
        # Vibrato oriental
        vibrato = 1 + 0.008 * sine(5.5, t)
        s = sine(freq * vibrato, t) * 0.7 + s * 0.3
        
        samples.append(env * s * 0.35)
    
    return samples

# Génère un son de cloche mystique de temple avec harmoniques inharmoniques
def generate_mystical_bell() -> list:
    """Génère un son de cloche mystique/temple."""
    duration = 1.2
    samples = []
    
    # Fréquences inharmoniques typiques des cloches
    freqs = [220, 277, 311, 370, 440, 554]
    decays = [3, 4, 5, 6, 4, 5]
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        s = 0
        for j, (freq, decay) in enumerate(zip(freqs, decays)):
            env = envelope_percussive(t, attack=0.005, decay_rate=decay)
            amp = 1.0 / (j + 1)
            s += sine(freq, t) * env * amp
        
        samples.append(s * 0.3)
    
    return samples

# Génère un son de flèche en vol avec fréquence descendante
def generate_arrow_whoosh() -> list:
    """Génère un son de flèche/projectile."""
    duration = 0.15
    samples = []
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        progress = i / (SAMPLE_RATE * duration)
        
        # Fréquence descendante
        freq = 1200 - 800 * progress
        
        # Envelope en cloche
        env = math.sin(math.pi * progress)
        env *= min(1.0, i / (SAMPLE_RATE * 0.01))
        
        # Son sifflant
        s = sine(freq, t) * 0.5
        s += noise() * 0.3 * (1 - progress)
        
        samples.append(env * s * 0.5)
    
    return samples

# Génère un son d'impact sourd
def generate_impact_hit() -> list:
    """Génère un son d'impact."""
    duration = 0.18
    samples = []
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        env = envelope_percussive(t, attack=0.002, decay_rate=20)
        
        # Impact sourd
        s = sine(100, t) * 0.5
        s += sine(180, t) * 0.3
        
        # Craquement
        noise_env = envelope_percussive(t, attack=0.001, decay_rate=50)
        n = noise() * noise_env * 0.4
        
        samples.append((env * s + n) * 0.7)
    
    return samples

# Génère un son de mort dramatique avec descente de fréquence
def generate_death_sound() -> list:
    """Génère un son de mort (descente mélodique)."""
    duration = 0.45
    samples = []
    scale = maqam_hijaz(220)
    
    notes = [scale[4], scale[3], scale[2], scale[1], scale[0]]
    note_duration = duration / len(notes)
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        note_idx = min(int(t / note_duration), len(notes) - 1)
        freq = notes[note_idx]
        
        # Envelope décroissante
        env = 1 - (t / duration)
        env *= min(1.0, i / (SAMPLE_RATE * 0.02))
        
        # Vibrato triste
        vibrato = 1 + 0.02 * sine(6, t)
        
        s = sine(freq * vibrato, t) * 0.7
        s += sine(freq * 2 * vibrato, t) * 0.2
        
        samples.append(env * s * 0.5)
    
    return samples

# Génère un son d'apparition magique avec montée de fréquence
def generate_spawn_sound() -> list:
    """Génère un son de spawn (montée mystique)."""
    duration = 0.3
    samples = []
    scale = maqam_bayati(220)
    
    notes = [scale[0], scale[2], scale[4], scale[5]]
    note_duration = duration / len(notes)
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        progress = t / duration
        note_idx = min(int(t / note_duration), len(notes) - 1)
        freq = notes[note_idx]
        
        # Envelope montante
        env = progress * envelope_percussive(duration - t, decay_rate=3)
        env = min(1.0, env * 2)
        
        s = sine(freq, t) * 0.6
        s += sine(freq * 2, t) * 0.25
        s += sine(freq * 3, t) * 0.1
        
        samples.append(env * s * 0.5)
    
    return samples

# Génère un arpège montant pour le son d'amélioration
def generate_upgrade_arpeggio() -> list:
    """Génère un arpège d'upgrade (harpe égyptienne)."""
    samples = []
    scale = maqam_hijaz(330)
    
    notes = [scale[0], scale[2], scale[4], scale[5], scale[7]]
    note_gap = 0.07
    note_duration = 0.35
    total_duration = note_gap * len(notes) + note_duration
    
    for i in range(int(SAMPLE_RATE * total_duration)):
        t = i / SAMPLE_RATE
        sample = 0
        
        for j, freq in enumerate(notes):
            note_start = j * note_gap
            if t >= note_start:
                local_t = t - note_start
                env = envelope_percussive(local_t, attack=0.003, decay_rate=5)
                
                s = sine(freq, local_t) * 0.7
                s += sine(freq * 2, local_t) * 0.3
                s += sine(freq * 3, local_t) * 0.15
                
                sample += env * s
        
        samples.append(sample * 0.25)
    
    return samples

# Génère une fanfare de victoire triomphante
def generate_victory_fanfare() -> list:
    """Génère une fanfare de victoire."""
    samples = []
    scale = maqam_hijaz(330)
    
    # Mélodie triomphante
    melody = [
        (scale[0], 0.15),
        (scale[2], 0.15),
        (scale[4], 0.15),
        (scale[4], 0.2),
        (scale[5], 0.25),
        (scale[7], 0.4),
    ]
    
    total_duration = sum(d for _, d in melody)
    
    current_time = 0
    for freq, dur in melody:
        note_samples = int(SAMPLE_RATE * dur)
        
        for i in range(note_samples):
            t = i / SAMPLE_RATE
            global_t = current_time + t
            
            # Envelope avec sustain
            env = envelope_adsr(t, 0.02, 0.05, 0.8, 0.1, dur)
            env *= (1 - global_t / (total_duration * 1.2))
            
            # Son riche et triomphant
            s = sine(freq, global_t) * 0.6
            s += sine(freq * 2, global_t) * 0.25
            s += sine(freq * 3, global_t) * 0.1
            
            # Légère quinte pour richesse
            s += sine(freq * 1.5, global_t) * 0.15
            
            samples.append(env * s * 0.4)
        
        current_time += dur
    
    return samples

# Génère une lamentation mélancolique de défaite
def generate_defeat_lament() -> list:
    """Génère une lamentation de défaite."""
    samples = []
    scale = maqam_bayati(220)
    
    # Mélodie descendante triste
    melody = [
        (scale[5], 0.25),
        (scale[4], 0.25),
        (scale[3], 0.25),
        (scale[2], 0.3),
        (scale[1], 0.35),
        (scale[0], 0.5),
    ]
    
    total_duration = sum(d for _, d in melody)
    
    current_time = 0
    for freq, dur in melody:
        note_samples = int(SAMPLE_RATE * dur)
        
        for i in range(note_samples):
            t = i / SAMPLE_RATE
            global_t = current_time + t
            
            env = envelope_adsr(t, 0.05, 0.1, 0.7, 0.15, dur)
            env *= (1 - global_t / (total_duration * 1.1))
            
            # Vibrato mélancolique
            vibrato = 1 + 0.015 * sine(5, global_t)
            
            s = sine(freq * vibrato, global_t) * 0.7
            s += sine(freq * 2, global_t) * 0.2
            
            samples.append(env * s * 0.45)
        
        current_time += dur
    
    return samples

# Génère un son de gong pour les événements importants
def generate_event_gong() -> list:
    """Génère un son de gong pour les événements."""
    duration = 0.8
    samples = []
    
    # Fréquences de gong
    base = 110
    freqs = [base, base * 1.4, base * 2.1, base * 2.8, base * 3.5]
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        # Attaque puis decay long
        env = envelope_percussive(t, attack=0.01, decay_rate=2.5)
        
        s = 0
        for j, freq in enumerate(freqs):
            amp = 1.0 / (j + 1)
            # Légère modulation
            mod = 1 + 0.01 * sine(0.5, t)
            s += sine(freq * mod, t) * amp
        
        samples.append(env * s * 0.35)
    
    return samples

# Génère un son de clic doux et subtil pour la sélection
def generate_select_click() -> list:
    """Génère un son de sélection doux (petit tintement subtil)."""
    duration = 0.12
    samples = []
    
    # Fréquence plus douce et aiguë (comme une petite clochette)
    freq = 880  # La5 - plus aigu mais plus doux
    
    for i in range(int(SAMPLE_RATE * duration)):
        t = i / SAMPLE_RATE
        
        # Envelope très douce avec attaque progressive
        attack = min(1.0, i / (SAMPLE_RATE * 0.008))  # 8ms d'attaque
        decay = math.exp(-t * 20)  # Decay rapide
        env = attack * decay
        
        # Son pur et doux (moins d'harmoniques)
        s = sine(freq, t) * 0.7
        s += sine(freq * 2, t) * 0.15  # Juste un peu d'harmonique
        
        # Volume très réduit pour être subtil
        samples.append(env * s * 0.25)
    
    return samples

# Génère une boucle musicale complète de 8 secondes style égyptien
def generate_music_loop() -> list:
    """Génère une boucle musicale style égyptien (8 secondes)."""
    duration = 8.0
    samples = [0.0] * int(SAMPLE_RATE * duration)
    
    scale = maqam_hijaz(220)
    
    # Pattern de percussion (doumbek)
    drum_pattern = [
        (0.0, 'dum'), (0.5, 'tek'), (0.75, 'tek'),
        (1.0, 'dum'), (1.5, 'tek'), (1.75, 'tek'),
        (2.0, 'dum'), (2.25, 'tek'), (2.5, 'dum'), (2.75, 'tek'),
        (3.0, 'dum'), (3.5, 'tek'), (3.75, 'tek'),
    ]
    
    # Répéter le pattern
    for bar in range(2):
        bar_offset = bar * 4.0
        for beat_time, drum_type in drum_pattern:
            t = bar_offset + beat_time
            start_idx = int(t * SAMPLE_RATE)
            
            if drum_type == 'dum':
                drum_samples = generate_doumbek_hit()
            else:
                drum_samples = generate_tek_sound()
            
            for i, s in enumerate(drum_samples):
                if start_idx + i < len(samples):
                    samples[start_idx + i] += s * 0.4
    
    # Mélodie de oud
    melody_notes = [
        (0.0, scale[0], 0.4),
        (0.5, scale[2], 0.3),
        (1.0, scale[4], 0.4),
        (1.5, scale[3], 0.3),
        (2.0, scale[2], 0.5),
        (2.75, scale[4], 0.2),
        (3.0, scale[5], 0.4),
        (3.5, scale[4], 0.3),
        (4.0, scale[2], 0.5),
        (4.5, scale[3], 0.3),
        (5.0, scale[4], 0.4),
        (5.5, scale[5], 0.3),
        (6.0, scale[4], 0.5),
        (6.5, scale[2], 0.3),
        (7.0, scale[0], 0.7),
    ]
    
    for note_time, freq, dur in melody_notes:
        start_idx = int(note_time * SAMPLE_RATE)
        note_samples = generate_oud_note(freq, dur)
        
        for i, s in enumerate(note_samples):
            if start_idx + i < len(samples):
                samples[start_idx + i] += s * 0.5
    
    # Normaliser
    max_val = max(abs(s) for s in samples)
    if max_val > 0:
        samples = [s / max_val * 0.8 for s in samples]
    
    return samples

# ============================================================================
# MAIN
# ============================================================================

# Fonction principale qui génère tous les fichiers sons et musiques
def main():
    print("=" * 50)
    print("Génération des sons égyptiens pour Antique War")
    print("=" * 50)
    
    ensure_output_dir()
    
    print("\nGénération des effets sonores...")
    
    # Effets sonores
    save_wav("shoot.wav", generate_arrow_whoosh())
    save_wav("hit.wav", generate_impact_hit())
    save_wav("death.wav", generate_death_sound())
    save_wav("spawn.wav", generate_spawn_sound())
    save_wav("upgrade.wav", generate_upgrade_arpeggio())
    save_wav("event.wav", generate_event_gong())
    save_wav("victory.wav", generate_victory_fanfare())
    save_wav("defeat.wav", generate_defeat_lament())
    save_wav("select.wav", generate_select_click())
    
    # Sons additionnels
    save_wav("doumbek.wav", generate_doumbek_hit())
    save_wav("tek.wav", generate_tek_sound())
    save_wav("bell.wav", generate_mystical_bell())
    save_wav("harp.wav", generate_harp_pluck(330, 0.5))
    
    print("\nGénération de la musique...")
    save_wav("music.wav", generate_music_loop())
    
    print("\n" + "=" * 50)
    print(f"Terminé ! Sons générés dans : {OUTPUT_DIR}")
    print("=" * 50)

if __name__ == "__main__":
    main()