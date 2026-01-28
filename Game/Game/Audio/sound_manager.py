"""
SoundManager - Gestion des sons du jeu style Égypte antique.

Utilise pygame.mixer pour jouer des sons.
Charge des fichiers audio si disponibles, sinon génère des sons procéduraux orientaux.
"""
import pygame
import math
import array
import os
from pathlib import Path


class SoundManager:
    """Gère les effets sonores et la musique du jeu."""
    
    def __init__(self):
        self.initialized = False
        self.enabled = True
        self.music_enabled = True
        self.volume = 0.7  # Volume des effets (augmenté)
        self.music_volume = 0.4  # Volume de la musique
        self.sounds = {}
        self.music_playing = False
        
        # Chemin vers le dossier audio
        self.audio_path = Path(__file__).parent / "sounds"
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            self.initialized = True
            self._load_or_generate_sounds()
            print("[OK] SoundManager initialized")
        except Exception as e:
            print(f"[WARN] Sound init failed: {e}")
            self.initialized = False
    
    def _load_or_generate_sounds(self):
        """Charge les fichiers audio ou génère des sons procéduraux."""
        if not self.initialized:
            return
        
        # Liste des sons à charger/générer
        sound_files = {
            "shoot": "shoot.wav",
            "hit": "hit.wav",
            "death": "death.wav",
            "spawn": "spawn.wav",
            "upgrade": "upgrade.wav",
            "event": "event.wav",
            "victory": "victory.wav",
            "defeat": "defeat.wav",
            "select": "select.wav",
        }
        
        sample_rate = 44100
        
        for sound_name, filename in sound_files.items():
            sound_path = self.audio_path / filename
            
            if sound_path.exists():
                # Charger le fichier audio
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(str(sound_path))
                    self.sounds[sound_name].set_volume(self.volume)
                    print(f"  [OK] Loaded {filename}")
                except Exception as e:
                    print(f"  [WARN] Could not load {filename}: {e}")
                    self._generate_fallback_sound(sound_name, sample_rate)
            else:
                # Générer un son procédural style égyptien
                self._generate_fallback_sound(sound_name, sample_rate)
    
    def _generate_fallback_sound(self, sound_name: str, sample_rate: int):
        """Génère un son procédural style oriental/égyptien."""
        
        # Gamme orientale (maqam hijaz) - demi-tons: 1, 3, 1, 2, 1, 3, 1
        # Notes en Hz à partir de La3 (220 Hz)
        maqam_hijaz = [220, 233, 277, 294, 330, 349, 415, 440]
        maqam_bayati = [220, 233, 262, 294, 330, 349, 392, 440]
        
        if sound_name == "shoot":
            # Son de projectile - sifflement oriental court
            self.sounds["shoot"] = self._make_oriental_whoosh(0.12, sample_rate)
        
        elif sound_name == "hit":
            # Impact - percussion sourde (doumbek style)
            self.sounds["hit"] = self._make_doumbek_hit(0.15, sample_rate)
        
        elif sound_name == "death":
            # Mort - descente mélodique orientale
            self.sounds["death"] = self._make_oriental_descent(maqam_hijaz, 0.4, sample_rate)
        
        elif sound_name == "spawn":
            # Spawn - montée mystique
            self.sounds["spawn"] = self._make_mystical_rise(maqam_bayati, 0.25, sample_rate)
        
        elif sound_name == "upgrade":
            # Upgrade - arpège harpe égyptienne
            self.sounds["upgrade"] = self._make_harp_arpeggio(maqam_hijaz, 0.5, sample_rate)
        
        elif sound_name == "event":
            # Événement - gong/cloche mystique
            self.sounds["event"] = self._make_mystical_bell(0.6, sample_rate)
        
        elif sound_name == "victory":
            # Victoire - fanfare triomphale orientale
            self.sounds["victory"] = self._make_victory_fanfare(maqam_hijaz, 0.8, sample_rate)
        
        elif sound_name == "defeat":
            # Défaite - lamentation
            self.sounds["defeat"] = self._make_lament(maqam_bayati, 0.6, sample_rate)
        
        elif sound_name == "select":
            # Sélection - petit son de harpe
            self.sounds["select"] = self._make_harp_pluck(330, 0.15, sample_rate)
        
        else:
            # Son par défaut
            self.sounds[sound_name] = self._make_simple_tone(300, 0.2, sample_rate)
    
    def _make_doumbek_hit(self, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée un son de percussion doumbek/darbouka."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        for i in range(n):
            t = i / sr
            # Envelope percussive rapide
            env = math.exp(-t * 25) * min(1.0, i / (sr * 0.002))
            
            # Basses fréquences (corps du tambour)
            low = math.sin(2 * math.pi * 80 * t) * 0.6
            # Médiums (attaque)
            mid = math.sin(2 * math.pi * 200 * t) * 0.3
            # Noise burst pour l'attaque
            noise = (((i * 1103515245 + 12345) % (2**31)) / (2**31) - 0.5) * 0.4
            noise *= math.exp(-t * 50)
            
            val = int(20000 * env * (low + mid + noise))
            buf[i] = max(-32767, min(32767, val))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_oriental_whoosh(self, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée un sifflement style flèche/projectile."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        for i in range(n):
            t = i / sr
            progress = i / n
            
            # Fréquence descendante
            freq = 800 - 400 * progress
            
            # Envelope
            env = math.sin(math.pi * progress) * min(1.0, i / (sr * 0.005))
            
            val = int(8000 * env * math.sin(2 * math.pi * freq * t))
            buf[i] = max(-32767, min(32767, val))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume * 0.7)
        return sound
    
    def _make_oriental_descent(self, scale: list, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée une descente mélodique orientale."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        notes_desc = list(reversed(scale[:5]))
        note_dur = n // len(notes_desc)
        
        for i in range(n):
            note_idx = min(i // note_dur, len(notes_desc) - 1)
            freq = notes_desc[note_idx]
            
            t = i / sr
            local_t = (i % note_dur) / note_dur
            
            # Envelope avec vibrato oriental
            env = (1 - i/n) * (1 - local_t * 0.3)
            vibrato = 1 + 0.02 * math.sin(2 * math.pi * 6 * t)
            
            val = int(12000 * env * math.sin(2 * math.pi * freq * vibrato * t))
            buf[i] = max(-32767, min(32767, val))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_mystical_rise(self, scale: list, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée une montée mystique."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        notes = scale[:4]
        note_dur = n // len(notes)
        
        for i in range(n):
            note_idx = min(i // note_dur, len(notes) - 1)
            freq = notes[note_idx]
            
            t = i / sr
            progress = i / n
            
            # Envelope montante
            env = progress * math.exp(-(1-progress) * 2) * min(1.0, i / (sr * 0.01))
            
            # Son avec harmoniques
            val = math.sin(2 * math.pi * freq * t)
            val += 0.3 * math.sin(2 * math.pi * freq * 2 * t)
            val += 0.1 * math.sin(2 * math.pi * freq * 3 * t)
            
            buf[i] = max(-32767, min(32767, int(10000 * env * val)))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_harp_arpeggio(self, scale: list, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée un arpège de harpe égyptienne."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        notes = scale[:6]
        note_dur = int(sr * 0.08)
        
        for note_idx, freq in enumerate(notes):
            start = note_idx * note_dur
            
            for i in range(int(sr * 0.3)):
                if start + i >= n:
                    break
                
                t = i / sr
                # Envelope de harpe (attaque rapide, decay long)
                env = math.exp(-t * 8) * min(1.0, i / (sr * 0.002))
                
                # Son de harpe avec harmoniques
                val = math.sin(2 * math.pi * freq * t)
                val += 0.5 * math.sin(2 * math.pi * freq * 2 * t)
                val += 0.25 * math.sin(2 * math.pi * freq * 3 * t)
                
                buf[start + i] = max(-32767, min(32767, 
                    buf[start + i] + int(8000 * env * val)))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_harp_pluck(self, freq: float, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée un son de harpe simple."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        for i in range(n):
            t = i / sr
            env = math.exp(-t * 12) * min(1.0, i / (sr * 0.001))
            
            val = math.sin(2 * math.pi * freq * t)
            val += 0.4 * math.sin(2 * math.pi * freq * 2 * t)
            
            buf[i] = max(-32767, min(32767, int(10000 * env * val)))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume * 0.6)
        return sound
    
    def _make_mystical_bell(self, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée un son de cloche/gong mystique."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        # Fréquences de cloche (inharmoniques)
        freqs = [220, 277, 349, 440, 554]
        
        for i in range(n):
            t = i / sr
            env = math.exp(-t * 3) * min(1.0, i / (sr * 0.005))
            
            val = 0
            for j, f in enumerate(freqs):
                amp = 1.0 / (j + 1)
                val += amp * math.sin(2 * math.pi * f * t)
            
            buf[i] = max(-32767, min(32767, int(8000 * env * val)))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_victory_fanfare(self, scale: list, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée une fanfare de victoire orientale."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        # Mélodie de victoire
        melody = [scale[0], scale[2], scale[4], scale[4], scale[5], scale[7]]
        note_dur = n // len(melody)
        
        for i in range(n):
            note_idx = min(i // note_dur, len(melody) - 1)
            freq = melody[note_idx]
            
            t = i / sr
            local_i = i % note_dur
            local_t = local_i / note_dur
            
            # Envelope avec sustain
            if local_t < 0.1:
                env = local_t / 0.1
            elif local_t > 0.8:
                env = (1 - local_t) / 0.2
            else:
                env = 1.0
            
            env *= (1 - i/(n*1.5))
            
            # Son riche
            val = math.sin(2 * math.pi * freq * t)
            val += 0.5 * math.sin(2 * math.pi * freq * 2 * t)
            val += 0.3 * math.sin(2 * math.pi * freq * 3 * t)
            
            buf[i] = max(-32767, min(32767, int(10000 * env * val)))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_lament(self, scale: list, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée une lamentation de défaite."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        # Descente lente
        melody = [scale[4], scale[3], scale[2], scale[1], scale[0]]
        note_dur = n // len(melody)
        
        for i in range(n):
            note_idx = min(i // note_dur, len(melody) - 1)
            freq = melody[note_idx]
            
            t = i / sr
            progress = i / n
            
            # Vibrato mélancolique
            vibrato = 1 + 0.015 * math.sin(2 * math.pi * 5 * t)
            
            env = (1 - progress) * min(1.0, i / (sr * 0.05))
            
            val = math.sin(2 * math.pi * freq * vibrato * t)
            buf[i] = max(-32767, min(32767, int(12000 * env * val)))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_simple_tone(self, freq: float, duration: float, sr: int) -> pygame.mixer.Sound:
        """Crée un son simple."""
        n = int(sr * duration)
        buf = array.array('h', [0] * n)
        
        for i in range(n):
            t = i / sr
            env = min(1.0, (n - i) / (n * 0.3)) * min(1.0, i / (sr * 0.01))
            val = int(10000 * env * math.sin(2 * math.pi * freq * t))
            buf[i] = max(-32767, min(32767, val))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def play(self, sound_name: str):
        """Joue un son par son nom."""
        if not self.initialized or not self.enabled:
            return
        
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass
    
    def play_music(self, music_file: str = None):
        """Joue la musique de fond."""
        if not self.initialized or not self.music_enabled:
            return
        
        music_path = None
        
        if music_file:
            music_path = self.audio_path / music_file
        else:
            # Chercher music.ogg ou music.wav
            for ext in ["ogg", "wav", "mp3"]:
                candidate = self.audio_path / f"music.{ext}"
                if candidate.exists():
                    music_path = candidate
                    break
        
        if music_path and music_path.exists():
            try:
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # Loop infini
                self.music_playing = True
                print(f"[OK] Playing music: {music_path.name}")
            except Exception as e:
                print(f"[WARN] Could not play music: {e}")
        else:
            print(f"[WARN] No music file found in {self.audio_path}")
    
    def stop_music(self):
        """Arrête la musique."""
        if self.initialized:
            pygame.mixer.music.stop()
            self.music_playing = False
    
    def set_volume(self, vol: float):
        """Définit le volume des effets (0.0 à 1.0)."""
        self.volume = max(0.0, min(1.0, vol))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def set_music_volume(self, vol: float):
        """Définit le volume de la musique (0.0 à 1.0)."""
        self.music_volume = max(0.0, min(1.0, vol))
        if self.initialized:
            pygame.mixer.music.set_volume(self.music_volume)
    
    def toggle(self):
        """Active/désactive les sons."""
        self.enabled = not self.enabled
        return self.enabled
    
    def toggle_music(self):
        """Active/désactive la musique."""
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.stop_music()
        return self.music_enabled


# Instance globale
sound_manager = SoundManager()
