"""
SoundManager - Gestion des sons du jeu.

Utilise pygame.mixer pour jouer des sons.
Génère des sons procéduraux simples si pas de fichiers audio.
"""
import pygame
import math
import array


class SoundManager:
    """Gère les effets sonores du jeu."""
    
    def __init__(self):
        self.initialized = False
        self.enabled = True
        self.volume = 0.5
        self.sounds = {}
        
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.initialized = True
            self._generate_sounds()
            print("[OK] SoundManager initialized")
        except Exception as e:
            print(f"[WARN] Sound init failed: {e}")
            self.initialized = False
    
    def _generate_sounds(self):
        """Génère des sons procéduraux simples."""
        if not self.initialized:
            return
        
        sample_rate = 22050
        
        # Son de tir (bip court aigu)
        self.sounds["shoot"] = self._make_beep(440, 0.08, sample_rate)
        
        # Son de hit (bip grave)
        self.sounds["hit"] = self._make_beep(220, 0.1, sample_rate)
        
        # Son de mort (descente)
        self.sounds["death"] = self._make_sweep(400, 100, 0.2, sample_rate)
        
        # Son de spawn (montée)
        self.sounds["spawn"] = self._make_sweep(200, 400, 0.15, sample_rate)
        
        # Son d'upgrade (arpège)
        self.sounds["upgrade"] = self._make_arpeggio([300, 400, 500], 0.1, sample_rate)
        
        # Son d'événement (attention)
        self.sounds["event"] = self._make_sweep(300, 600, 0.3, sample_rate)
        
        # Son de victoire
        self.sounds["victory"] = self._make_arpeggio([400, 500, 600, 800], 0.15, sample_rate)
        
        # Son de défaite
        self.sounds["defeat"] = self._make_sweep(400, 150, 0.4, sample_rate)
    
    def _make_beep(self, freq: float, duration: float, sample_rate: int) -> pygame.mixer.Sound:
        """Crée un bip simple."""
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            t = i / sample_rate
            # Envelope simple (attaque rapide, decay)
            env = min(1.0, (n_samples - i) / (n_samples * 0.8))
            env *= min(1.0, i / (sample_rate * 0.01))  # Attaque 10ms
            
            val = int(16000 * env * math.sin(2 * math.pi * freq * t))
            buf[i] = max(-32767, min(32767, val))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_sweep(self, freq_start: float, freq_end: float, duration: float, 
                    sample_rate: int) -> pygame.mixer.Sound:
        """Crée un son avec fréquence qui change."""
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            t = i / sample_rate
            progress = i / n_samples
            freq = freq_start + (freq_end - freq_start) * progress
            
            env = min(1.0, (n_samples - i) / (n_samples * 0.3))
            env *= min(1.0, i / (sample_rate * 0.01))
            
            val = int(12000 * env * math.sin(2 * math.pi * freq * t))
            buf[i] = max(-32767, min(32767, val))
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(self.volume)
        return sound
    
    def _make_arpeggio(self, freqs: list, note_duration: float, 
                       sample_rate: int) -> pygame.mixer.Sound:
        """Crée un arpège (suite de notes)."""
        total_samples = int(sample_rate * note_duration * len(freqs))
        buf = array.array('h', [0] * total_samples)
        samples_per_note = int(sample_rate * note_duration)
        
        for note_idx, freq in enumerate(freqs):
            start = note_idx * samples_per_note
            
            for i in range(samples_per_note):
                if start + i >= total_samples:
                    break
                    
                t = i / sample_rate
                env = min(1.0, (samples_per_note - i) / (samples_per_note * 0.5))
                env *= min(1.0, i / (sample_rate * 0.005))
                
                val = int(10000 * env * math.sin(2 * math.pi * freq * t))
                buf[start + i] = max(-32767, min(32767, val))
        
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
    
    def set_volume(self, vol: float):
        """Définit le volume (0.0 à 1.0)."""
        self.volume = max(0.0, min(1.0, vol))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def toggle(self):
        """Active/désactive les sons."""
        self.enabled = not self.enabled
        return self.enabled


# Instance globale
sound_manager = SoundManager()
