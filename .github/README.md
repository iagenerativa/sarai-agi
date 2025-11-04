# GitHub Configuration for SARAi_AGI

Este directorio contiene la configuración de GitHub para el repositorio SARAi_AGI.

## 📁 Estructura

```
.github/
├── workflows/
│   └── ci.yml                    # CI/CD pipeline (Python 3.10/3.11/3.12)
├── ISSUE_TEMPLATE/
│   ├── bug_report.md            # Plantilla para reportar bugs
│   └── feature_request.md       # Plantilla para solicitar features
├── pull_request_template.md     # Plantilla para PRs
├── FUNDING.yml                   # Información de funding (opcional)
└── README.md                     # Este archivo
```

## 🔄 CI/CD Pipeline

El workflow `ci.yml` ejecuta automáticamente en cada push y PR:

- **Matrix testing**: Python 3.10, 3.11, 3.12
- **Steps**:
  1. Install dependencies
  2. Lint (ruff, cuando esté configurado)
  3. Run tests (pytest)
  4. Version check

## 🐛 Issue Templates

### Bug Report
Usa esta plantilla para reportar bugs. Incluye:
- Descripción del bug
- Pasos para reproducir
- Comportamiento esperado vs actual
- Entorno (OS, Python, versión)
- Logs y screenshots

### Feature Request
Usa esta plantilla para proponer nuevas funcionalidades. Incluye:
- Descripción de la feature
- Problema que resuelve
- Solución propuesta
- Impacto estimado (CRITICAL/HIGH/MEDIUM/LOW)

## 📝 Pull Request Template

Template estándar para PRs que requiere:
- Descripción de cambios
- Tipo de cambio (bug fix, feature, breaking change, etc.)
- Checklist completo (code review, tests, docs, changelog)
- Métricas de calidad (tests passing, coverage, lint)

## 💰 Funding

El archivo `FUNDING.yml` permite configurar botones de sponsorship en GitHub.

---

**Repository:** [github.com/iagenerativa/sarai-agi](https://github.com/iagenerativa/sarai-agi)
