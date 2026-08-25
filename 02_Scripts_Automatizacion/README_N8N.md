# Guía de Automatización y Orquestación con n8n

Este módulo contiene la definición lista para producción del workflow de **n8n** que orquesta la ejecución desatendida del ecosistema de coyuntura macroeconómica.

---

## 1. Arquitectura del Flujo

```
[Cron Matutino 09:00 ART] ──┐
                             ├──> [Ejecutar Agent Runner] ──> [Parsear KPIs] ──┬──> [Telegram Alert]
[Webhook INDEC / BCRA]   ──┘                                                  └──> [Slack Alert]
```

1. **Disparadores (Triggers)**:
   - **Cron Matutino:** Ejecuta de lunes a viernes a las 09:00 AM (hora de Argentina, 12:00 UTC) antes de la apertura de mercados.
   - **Webhook de Eventos:** Endpoint POST `/webhook/coyuntura-macro-trigger` para ejecuciones bajo demanda tras comunicados de prensa del INDEC o licitaciones del Tesoro.
2. **Ejecución del Núcleo:** Invoca `src/agent_runner.py`, que valida contratos JSON, compila las 9 infografías a 300 DPI y genera los 3 PDFs ejecutivos (Diario, Semanal APA 7 y Mensual ReportLab).
3. **Sincronización:** Actualiza en tiempo real el directorio local y el espejo en `C:\Users\fedea\Google Drive\coyuntura-macro`.
4. **Notificaciones Multicanal:** Envía un resumen formateado de variables clave (CCL, Brecha, TEM Lecap vs. REM, Riesgo País, EMAE, S&P Merval) a canales de Telegram y Slack.

---

## 2. Instrucciones de Importación en n8n

1. Abrir la interfaz de n8n (local o cloud: `http://localhost:5678`).
2. Ir a **Workflows** $\rightarrow$ **Import from File...**
3. Seleccionar el archivo `02_Scripts_Automatizacion/n8n_coyuntura_workflow.json`.
4. Configurar las credenciales deseadas (Telegram Bot Token / Slack Webhook URL).
5. Activar el switch **Active** en la esquina superior derecha.

---

## 3. Disparo Manual vía Webhook (cURL / PowerShell)

```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/coyuntura-macro-trigger" -Method Post
```
