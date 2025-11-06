# LLM Gateway

Pequeño wrapper centralizado para acceder a LLMs desde todos los módulos de SARAi.

Características:
- Singleton `get_gateway()`
- Soporte para providers: `ollama`, `local` (extensible)
- Cache LRU con TTL
- Fallback providers y configuración central desde `.env`

Ejemplo rápido:

```python
from sarai_agi.llm_gateway import get_gateway

gw = get_gateway()
resp = gw.chat([{"role": "user", "content": "Hola mundo"}])
print(resp["text"]) 
```

Ver `config.py` para variables de entorno soportadas.
