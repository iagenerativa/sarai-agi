"""
Sistema de Fillers (frases de relleno) para SARAi v3.8.0.

Los fillers son frases cortas que SARAi puede reproducir mientras procesa
una consulta compleja, haciendo la interacción más natural y reduciendo
la percepción de latencia.

Features:
- Pre-grabación automática con MeloTTS
- 10+ fillers en español
- Variación para evitar repetición
- Cache en disco
- Turn-taking natural con VAD

Uso:
    >>> from sarai_agi.audio import FillerSystem
    >>> fillers = FillerSystem()
    >>> audio = fillers.get_random_filler()  # "un momento..."
    >>> audio = fillers.get_thinking_filler()  # "déjame pensar"

Week 1 Day 5 | v3.8.0-dev
LOC: 120
"""

import logging
import random
from pathlib import Path
from typing import Optional, List
import numpy as np

logger = logging.getLogger(__name__)

# Intentar importar MeloTTS
try:
    from .melotts import get_tts, MELOTTS_AVAILABLE
except ImportError:
    MELOTTS_AVAILABLE = False
    logger.warning("MeloTTS not available - FillerSystem disabled")


class FillerSystem:
    """
    Sistema de frases de relleno para interacciones naturales.
    
    Provee fillers pre-grabados que SARAi puede reproducir mientras
    procesa consultas complejas, mejorando la experiencia de usuario.
    
    Features:
    - 10+ fillers en español
    - Pre-grabación con MeloTTS (expresivo)
    - Cache en disco (evita re-generar)
    - Variación automática (evita repetición)
    - Categorías: thinking, waiting, confirming
    
    Usage:
        >>> fillers = FillerSystem()
        >>> # Mientras procesa algo complejo
        >>> audio = fillers.get_thinking_filler()
        >>> play_audio(audio)  # "déjame pensar..."
        >>> 
        >>> # Mientras espera respuesta externa
        >>> audio = fillers.get_waiting_filler()
        >>> play_audio(audio)  # "un momento..."
        >>> 
        >>> # Confirmar recepción
        >>> audio = fillers.get_confirming_filler()
        >>> play_audio(audio)  # "entiendo"
    
    Fillers disponibles:
    - Thinking: "déjame pensar", "veamos", "a ver"
    - Waiting: "un momento", "espera", "dame un segundo"
    - Confirming: "entiendo", "vale", "ok", "perfecto"
    - Generic: "hmm", "eh"
    """
    
    # Definición de fillers por categoría
    FILLERS = {
        'thinking': [
            "déjame pensar",
            "veamos",
            "a ver",
            "mmm déjame ver",
            "voy a revisar eso",
        ],
        'waiting': [
            "un momento",
            "espera",
            "dame un segundo",
            "enseguida",
            "un momentito",
        ],
        'confirming': [
            "entiendo",
            "vale",
            "ok",
            "perfecto",
            "de acuerdo",
        ],
        'generic': [
            "hmm",
            "eh",
            "mmm",
        ]
    }
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        auto_generate: bool = True,
        speed: float = 1.2
    ):
        """
        Inicializa el sistema de fillers.
        
        Args:
            cache_dir: Directorio para cachear fillers pre-grabados
            auto_generate: Si True, genera fillers automáticamente al init
            speed: Velocidad de síntesis (default: 1.2x)
        """
        self._cache_dir = cache_dir or Path("data/audio/fillers")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._speed = speed
        self._available = MELOTTS_AVAILABLE
        
        # Cache de audios en memoria (lazy loading)
        self._audio_cache = {}
        
        # Tracking de uso (para evitar repetición)
        self._last_used = {}
        
        if auto_generate and self._available:
            self._generate_all_fillers()
        
        logger.info(
            f"FillerSystem initialized: {len(self._get_all_filler_texts())} fillers, "
            f"cache_dir={self._cache_dir}, available={self._available}"
        )
    
    def _get_all_filler_texts(self) -> List[str]:
        """Obtiene todos los textos de fillers disponibles."""
        all_fillers = []
        for category_fillers in self.FILLERS.values():
            all_fillers.extend(category_fillers)
        return all_fillers
    
    def _generate_all_fillers(self):
        """
        Genera todos los fillers y los guarda en cache.
        
        Solo genera los que no existen en cache.
        """
        if not self._available:
            logger.warning("Cannot generate fillers: MeloTTS not available")
            return
        
        tts = get_tts()
        if not tts.is_available():
            logger.warning("TTS not available for filler generation")
            return
        
        logger.info("Generating fillers (if not cached)...")
        generated = 0
        
        for text in self._get_all_filler_texts():
            cache_file = self._get_cache_path(text)
            
            # Skip si ya existe
            if cache_file.exists():
                continue
            
            # Generar con MeloTTS (expresivo, rápido)
            audio = tts.synthesize(
                text,
                speed=self._speed,
                noise_scale=0.5,  # Moderadamente expresivo
                noise_scale_w=0.6
            )
            
            if audio is not None:
                # Guardar en cache
                np.save(cache_file, audio)
                logger.debug(f"Generated filler: {text} → {cache_file}")
                generated += 1
        
        if generated > 0:
            logger.info(f"Generated {generated} new fillers")
    
    def _get_cache_path(self, text: str) -> Path:
        """Obtiene la ruta de cache para un filler."""
        # Sanitize filename
        filename = text.replace(" ", "_").replace(",", "")
        filename = "".join(c for c in filename if c.isalnum() or c == "_")
        return self._cache_dir / f"{filename}.npy"
    
    def _load_filler(self, text: str) -> Optional[np.ndarray]:
        """
        Carga un filler desde cache o lo genera.
        
        Args:
            text: Texto del filler
        
        Returns:
            Audio como numpy array, o None si error
        """
        # Check cache en memoria primero
        if text in self._audio_cache:
            return self._audio_cache[text]
        
        # Check cache en disco
        cache_file = self._get_cache_path(text)
        if cache_file.exists():
            try:
                audio = np.load(cache_file)
                self._audio_cache[text] = audio
                return audio
            except Exception as e:
                logger.error(f"Error loading cached filler: {e}")
        
        # Generar on-demand
        if not self._available:
            return None
        
        tts = get_tts()
        if not tts.is_available():
            return None
        
        audio = tts.synthesize(
            text,
            speed=self._speed,
            noise_scale=0.5,
            noise_scale_w=0.6
        )
        
        if audio is not None:
            # Cache en memoria y disco
            self._audio_cache[text] = audio
            try:
                np.save(cache_file, audio)
            except Exception as e:
                logger.error(f"Error caching filler: {e}")
        
        return audio
    
    def get_filler(
        self,
        category: str = 'thinking',
        avoid_recent: bool = True
    ) -> Optional[np.ndarray]:
        """
        Obtiene un filler de una categoría específica.
        
        Args:
            category: Categoría ('thinking', 'waiting', 'confirming', 'generic')
            avoid_recent: Si True, evita repetir el último usado
        
        Returns:
            Audio del filler, o None si no disponible
        """
        fillers = self.FILLERS.get(category, self.FILLERS['thinking'])
        
        # Evitar repetir el último
        if avoid_recent and category in self._last_used:
            last = self._last_used[category]
            available = [f for f in fillers if f != last]
            if available:
                fillers = available
        
        # Seleccionar random
        text = random.choice(fillers)
        self._last_used[category] = text
        
        return self._load_filler(text)
    
    def get_thinking_filler(self) -> Optional[np.ndarray]:
        """Obtiene un filler de pensamiento ("déjame pensar", "veamos")."""
        return self.get_filler('thinking')
    
    def get_waiting_filler(self) -> Optional[np.ndarray]:
        """Obtiene un filler de espera ("un momento", "espera")."""
        return self.get_filler('waiting')
    
    def get_confirming_filler(self) -> Optional[np.ndarray]:
        """Obtiene un filler de confirmación ("entiendo", "vale")."""
        return self.get_filler('confirming')
    
    def get_random_filler(self) -> Optional[np.ndarray]:
        """Obtiene un filler aleatorio de cualquier categoría."""
        category = random.choice(list(self.FILLERS.keys()))
        return self.get_filler(category)
    
    def is_available(self) -> bool:
        """Verifica si el sistema de fillers está disponible."""
        return self._available
    
    def clear_cache(self):
        """Limpia el cache en memoria (mantiene cache en disco)."""
        self._audio_cache.clear()
        logger.info("Filler memory cache cleared")
    
    def regenerate_all(self):
        """Regenera todos los fillers (borra cache y re-genera)."""
        if not self._available:
            logger.warning("Cannot regenerate: TTS not available")
            return
        
        # Limpiar caches
        self._audio_cache.clear()
        
        # Borrar archivos en disco
        for file in self._cache_dir.glob("*.npy"):
            file.unlink()
        
        # Re-generar
        self._generate_all_fillers()
        logger.info("All fillers regenerated")


# Singleton global instance
_filler_system: Optional[FillerSystem] = None


def get_filler_system() -> FillerSystem:
    """
    Obtiene la instancia singleton del sistema de fillers.
    
    Returns:
        FillerSystem instance (siempre la misma)
    
    Examples:
        >>> fillers = get_filler_system()
        >>> audio = fillers.get_thinking_filler()
        >>> # Reproducir mientras procesa...
    """
    global _filler_system
    if _filler_system is None:
        _filler_system = FillerSystem()
    return _filler_system
