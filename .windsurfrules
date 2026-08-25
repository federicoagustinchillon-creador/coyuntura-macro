# Universal Agent Kernel & Autonomous Multi-Agent Protocol

Este archivo define las directivas invariantes y el protocolo de orquestación autónoma para todos los agentes de IA (**Antigravity**, **Claude Code**, **Cursor**, **Aider**, **Windsurf**).

---

## 1. Regla de Oro: Enrutamiento Autónomo por Dominio (Modular Skills)
Los agentes deben delegar y consultar autónomamente a las **Skills especializadas** sin esperar que el usuario lo solicite:
- **Tareas Cuantitativas & HERC**: Consultar `herc-quant-engine-auditor` y `backtest-overfitting-pbo-guard`.
- **Macro & Vistas Black-Litterman**: Consultar `SecondBrain/core/macro_coyuntura/live_macro_views_registry.json`.
- **Diseño & UI/UX**: Seguir estándar Bloomberg/Linear de `impeccable-design-and-uiux-architect` (cero emojis, números tabulares).
- **Entregables Tangibles**: Usar plantillas en `SecondBrain/templates/golden_blueprints/` (PPTX, XLSX, LaTeX, HTML).
- **Automatización & n8n**: Consultar `n8n-workflow-and-autonomous-pipeline-orchestrator`.
- **Memoria de Errores & Regresiones**: Consultar `SecondBrain/core/episodic_memory/agent_lessons_learned.json`.

---

## 2. Protocolo Linus Torvalds: Cero Tolerancia a Código Perezoso
- **Prohibido**: Stubs `# TODO`, código simulado, valores fabricados o podar bloques de manejo de errores al refactorizar.
- **Obligatorio**: Tipado estricto (`typing`), docstrings matemáticos y validación completa con `pytest`.
- **Grounding Gate**: Toda métrica citada debe provenir de archivos reales (`outputs/`, `src/`, `SecondBrain/`).

---

## 3. Disciplina de Contexto: Ruteo de 3 Vías
- **Vía 1 (1-2 archivos)**: Ejecución directa mediante diffs quirúrgicos (`replace_file_content`).
- **Vía 2 (Exploración >3 archivos)**: Delegar lectura a subagente `research` aislado (`tier: flash`) para no saturar la ventana principal.
- **Vía 3 (Arquitectura / Nuevos Modelos)**: Activar **Planning Mode / Spec-Kit** (`implementation_plan.md`) antes de codear.

---

## 4. Higiene de Git y Auditoría Pre-Commit
- **Commit Inmediato**: Todo entregable tangible generado (.pdf, .html, .xlsx, .pptx) DEBE comitearse en el mismo turno.
- **Verificación Obligatoria**: Antes de cerrar el turno, ejecutar siempre `python tools/pre_commit_guard.py`.
