"""
SARAi AGI - Web Audit Module

Sistema de auditoría inmutable para búsquedas web y interacciones de voz.
Migrado desde SARAi_v2 v2.11 con adaptaciones para arquitectura modular.

Características:
- Logging inmutable con SHA-256 (búsquedas web)
- Logging con HMAC-SHA256 (interacciones de voz)
- Sidecars verificables (.sha256, .hmac)
- Detección de anomalías automática
- Trigger de Safe Mode si corrupción detectada

Formato de log web:
{
    "timestamp": "2025-11-04T10:30:15.123456",
    "query": "¿Cómo está el clima en Tokio?",
    "source": "cache" | "searxng",
    "snippets_count": 5,
    "snippets_urls": ["url1", "url2", ...],
    "synthesis_used": true,
    "llm_model": "expert_short" | "expert_long",
    "response_preview": "Según los resultados...",
    "safe_mode_active": false,
    "error": null
}

Uso:
    from sarai_agi.memory.web_audit import get_web_audit_logger
    
    logger = get_web_audit_logger()
    logger.log_web_query(
        query="¿Clima en Tokio?",
        search_results=results,
        response="Según las fuentes...",
        llm_model="expert_short"
    )
"""

import hashlib
import hmac
import json
import logging
import os
import threading
from datetime import datetime
from typing import Dict, Optional

# Safe Mode trigger - adaptado para sarai-agi
try:
    from sarai_agi.security.resilience import activate_safe_mode
except ImportError:
    def activate_safe_mode(reason: str):
        """Fallback si security.resilience no disponible"""
        logging.warning(f"Safe Mode trigger (fallback): {reason}")
        os.environ["SARAI_SAFE_MODE"] = "true"


logger = logging.getLogger(__name__)


class WebAuditLogger:
    """
    Logger de auditoría para búsquedas web con firma SHA-256
    
    Cada línea del log se firma con SHA-256 para garantizar integridad.
    El sidecar .sha256 contiene los hashes línea por línea.
    
    Args:
        log_dir: Directorio para logs (default: logs/)
        anomaly_threshold: Número de errores consecutivos que trigger Safe Mode
    """

    def __init__(
        self,
        log_dir: str = "logs",
        anomaly_threshold: int = 5
    ):
        self.log_dir = log_dir
        self.anomaly_threshold = anomaly_threshold
        os.makedirs(log_dir, exist_ok=True)

        # Thread-safe logging
        self.lock = threading.Lock()

        # Counter de errores consecutivos para detección de anomalías
        self.consecutive_errors = 0

    def _get_log_paths(self, log_type: str = "web") -> tuple:
        """
        Retorna (jsonl_path, hash_path) para el día actual
        
        Args:
            log_type: "web" o "voice"
        
        Returns:
            (jsonl_path, hash_path)
        """
        date = datetime.now().strftime("%Y-%m-%d")

        if log_type == "web":
            jsonl_path = os.path.join(self.log_dir, f"web_queries_{date}.jsonl")
            hash_path = f"{jsonl_path}.sha256"
        elif log_type == "voice":
            jsonl_path = os.path.join(self.log_dir, f"voice_interactions_{date}.jsonl")
            hash_path = f"{jsonl_path}.hmac"
        else:
            raise ValueError(f"log_type inválido: {log_type}")

        return jsonl_path, hash_path

    def log_web_query(
        self,
        query: str,
        search_results: Optional[Dict],
        response: Optional[str] = None,
        llm_model: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Registra una búsqueda web con firma SHA-256
        
        Args:
            query: Query del usuario
            search_results: Output de web_cache.get()
            response: Respuesta sintetizada por el LLM (opcional)
            llm_model: Modelo usado para síntesis (opcional)
            error: Mensaje de error si fallo (opcional)
        """
        with self.lock:
            # Construir entrada de log
            entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "source": search_results.get("source") if search_results else "error",
                "snippets_count": len(search_results.get("snippets", [])) if search_results else 0,
                "snippets_urls": [
                    s.get("url") for s in search_results.get("snippets", [])
                ] if search_results else [],
                "synthesis_used": response is not None,
                "llm_model": llm_model,
                "response_preview": response[:200] if response else None,
                "safe_mode_active": False,  # Se actualiza si anomalía
                "error": error
            }

            # DETECCIÓN DE ANOMALÍAS
            if error or (search_results and entry["snippets_count"] == 0 and entry["source"] == "searxng"):
                self.consecutive_errors += 1

                if self.consecutive_errors >= self.anomaly_threshold:
                    logger.error(f"Anomalía detectada: {self.consecutive_errors} errores consecutivos")
                    entry["safe_mode_active"] = True

                    # Trigger Safe Mode
                    activate_safe_mode(f"web_audit_anomaly: {self.consecutive_errors} errores")
            else:
                # Reset counter si búsqueda exitosa
                self.consecutive_errors = 0

            # Serializar a JSON
            log_line = json.dumps(entry, ensure_ascii=False)

            # Escribir log principal
            jsonl_path, sha256_path = self._get_log_paths("web")

            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")

            # Calcular y escribir SHA-256
            line_hash = hashlib.sha256(log_line.encode('utf-8')).hexdigest()

            with open(sha256_path, "a", encoding="utf-8") as f_hash:
                f_hash.write(f"{line_hash}\n")

            logger.debug(f"Web query logged: {query[:60]}... (hash: {line_hash[:8]}...)")

    def log_voice_interaction(
        self,
        input_audio_hash: str,
        detected_lang: Optional[str],
        engine_used: str,
        response_text: str,
        hmac_secret: Optional[str] = None
    ):
        """
        Registra una interacción de voz con firma HMAC-SHA256
        
        Args:
            input_audio_hash: SHA-256 del audio de entrada
            detected_lang: Código de idioma detectado (ISO 639-1)
            engine_used: Motor usado ("omni" | "nllb" | "lfm2")
            response_text: Texto de respuesta generado
            hmac_secret: Clave secreta para HMAC (default desde env)
        """
        with self.lock:
            # Leer secret de env si no se especifica
            if hmac_secret is None:
                hmac_secret = os.getenv("HMAC_SECRET_KEY", "default-secret")

            # Construir entrada de log
            entry = {
                "timestamp": datetime.now().isoformat(),
                "input_audio_sha256": input_audio_hash,
                "detected_lang": detected_lang,
                "engine_used": engine_used,
                "response_text": response_text[:200],  # Preview
                "safe_mode_active": False
            }

            # Serializar a JSON (con sort_keys para reproducibilidad)
            entry_str = json.dumps(entry, ensure_ascii=False, sort_keys=True)

            # Calcular HMAC-SHA256
            signature = hmac.new(
                hmac_secret.encode('utf-8'),
                entry_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Escribir log principal
            jsonl_path, hmac_path = self._get_log_paths("voice")

            with open(jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # Escribir HMAC sidecar
            with open(hmac_path, "a", encoding="utf-8") as f_hmac:
                f_hmac.write(f"{signature}\n")

            logger.debug(f"Voice interaction logged: {engine_used} (hmac: {signature[:8]}...)")

    def verify_integrity(self, log_date: str, log_type: str = "web") -> bool:
        """
        Verifica la integridad de los logs de un día específico
        
        Args:
            log_date: Fecha en formato YYYY-MM-DD
            log_type: "web" o "voice"
        
        Returns:
            True si integridad OK, False si corrupción detectada
        """
        if log_type == "web":
            jsonl_path = os.path.join(self.log_dir, f"web_queries_{log_date}.jsonl")
            hash_path = f"{jsonl_path}.sha256"
        elif log_type == "voice":
            jsonl_path = os.path.join(self.log_dir, f"voice_interactions_{log_date}.jsonl")
            hash_path = f"{jsonl_path}.hmac"
            # Para voice necesitamos el secret
            hmac_secret = os.getenv("HMAC_SECRET_KEY", "default-secret")
        else:
            raise ValueError(f"log_type inválido: {log_type}")

        if not os.path.exists(jsonl_path) or not os.path.exists(hash_path):
            logger.warning(f"Logs para {log_date} no encontrados")
            return True  # No hay nada que verificar

        try:
            with open(jsonl_path, "r", encoding="utf-8") as f, \
                 open(hash_path, "r", encoding="utf-8") as f_hash:

                for line_num, (line, expected_hash) in enumerate(zip(f, f_hash, strict=True), 1):
                    line = line.strip()
                    expected_hash = expected_hash.strip()

                    if log_type == "web":
                        # Verificar SHA-256
                        computed_hash = hashlib.sha256(line.encode('utf-8')).hexdigest()
                    else:
                        # Verificar HMAC-SHA256
                        # Necesitamos re-serializar con sort_keys
                        entry = json.loads(line)
                        entry_str = json.dumps(entry, ensure_ascii=False, sort_keys=True)
                        computed_hash = hmac.new(
                            hmac_secret.encode('utf-8'),
                            entry_str.encode('utf-8'),
                            hashlib.sha256
                        ).hexdigest()

                    if computed_hash != expected_hash:
                        logger.error(
                            f"CORRUPCIÓN DETECTADA en línea {line_num} de {log_date} ({log_type})"
                        )
                        # Trigger Safe Mode
                        activate_safe_mode(f"log_corruption_{log_type}_{log_date}_line_{line_num}")
                        return False

            logger.info(f"Integridad verificada OK: {log_date} ({log_type})")
            return True

        except Exception as e:
            logger.error(f"Error verificando integridad de {log_date}: {e}")
            return False

    def get_stats(self, days: int = 7) -> Dict:
        """
        Obtiene estadísticas de logs de los últimos N días
        
        Args:
            days: Número de días hacia atrás
        
        Returns:
            {
                "total_web_queries": int,
                "total_voice_interactions": int,
                "error_rate": float,
                "avg_snippets_per_query": float
            }
        """
        from datetime import timedelta

        stats = {
            "total_web_queries": 0,
            "total_voice_interactions": 0,
            "error_rate": 0.0,
            "avg_snippets_per_query": 0.0
        }

        total_errors = 0
        total_snippets = 0

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

            # Contar web queries
            web_log = os.path.join(self.log_dir, f"web_queries_{date}.jsonl")
            if os.path.exists(web_log):
                with open(web_log, "r", encoding="utf-8") as f:
                    for line in f:
                        stats["total_web_queries"] += 1
                        entry = json.loads(line)

                        if entry.get("error"):
                            total_errors += 1

                        total_snippets += entry.get("snippets_count", 0)

            # Contar voice interactions
            voice_log = os.path.join(self.log_dir, f"voice_interactions_{date}.jsonl")
            if os.path.exists(voice_log):
                with open(voice_log, "r", encoding="utf-8") as f:
                    for _ in f:
                        stats["total_voice_interactions"] += 1

        # Calcular promedios
        if stats["total_web_queries"] > 0:
            stats["error_rate"] = total_errors / stats["total_web_queries"]
            stats["avg_snippets_per_query"] = total_snippets / stats["total_web_queries"]

        return stats


# Singleton global
_web_audit_logger_instance: Optional[WebAuditLogger] = None


def get_web_audit_logger(log_dir: Optional[str] = None) -> WebAuditLogger:
    """
    Factory function para obtener instancia singleton de WebAuditLogger
    
    Args:
        log_dir: Directorio de logs (default: logs/)
    
    Returns:
        Instancia singleton de WebAuditLogger
    """
    global _web_audit_logger_instance

    if _web_audit_logger_instance is None:
        if log_dir is None:
            log_dir = "logs"

        _web_audit_logger_instance = WebAuditLogger(log_dir=log_dir)

    return _web_audit_logger_instance
