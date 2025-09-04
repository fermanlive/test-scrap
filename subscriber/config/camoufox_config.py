"""
Configuración simplificada de Camoufox - Solo perfil FAST.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class CamoufoxConfig:
    """Configuración simple para Camoufox - Perfil FAST."""
    
    # Configuración básica
    headless: bool = True
    viewport_width: int = 1366
    viewport_height: int = 768
    locale: str = "es-UY"
    timezone_id: str = "America/Montevideo"
    
    # Configuración anti-detección básica
    enable_stealth: bool = False
    enable_anti_detection: bool = True
    enable_fingerprint_protection: bool = False
    
    # Configuración de rendimiento
    user_agent_rotation: bool = False
    clear_cookies_on_start: bool = False
    clear_storage_on_start: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir configuración a diccionario."""
        return {
            "headless": self.headless,
            "viewport": {"width": self.viewport_width, "height": self.viewport_height},
            "locale": self.locale,
            "timezone_id": self.timezone_id,
            "enable_stealth": self.enable_stealth,
            "enable_anti_detection": self.enable_anti_detection,
            "enable_fingerprint_protection": self.enable_fingerprint_protection,
            "user_agent_rotation": self.user_agent_rotation,
            "clear_cookies_on_start": self.clear_cookies_on_start,
            "clear_storage_on_start": self.clear_storage_on_start,
        }


def get_fast_config() -> CamoufoxConfig:
    """Obtener configuración FAST de Camoufox."""
    return CamoufoxConfig()


# Configuración por defecto
DEFAULT_CONFIG = get_fast_config()
