"""
Configuración de monitoreo para el sistema de scraping.
"""

import os

# Configuración de monitoreo
MONITORING_CONFIG = {
    "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
    "metrics_interval": int(os.getenv("METRICS_INTERVAL", "60")),
    "performance_thresholds": {
        "max_extraction_time": int(os.getenv("MAX_EXTRACTION_TIME", "300")),
        "min_success_rate": float(os.getenv("MIN_SUCCESS_RATE", "80.0")),
        "max_error_rate": float(os.getenv("MAX_ERROR_RATE", "20.0"))
    }
}
