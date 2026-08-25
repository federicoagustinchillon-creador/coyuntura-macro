# Protocolo de Ejecución Desatendida para Agentes Autónomos (Gemini Spark Runbook)

Este documento es la **fuente única de verdad y guía operativa** para cualquier agente de inteligencia artificial (Gemini Spark, Claude, Antigravity) o script automatizado encargado de actualizar, modelizar y publicar los informes de coyuntura macroeconómica y finanzas.

---

## 1. Filosofía de Creación de Valor, Tono Humano y Diseño Institucional

Para superar el estándar de consultoras como 1816, Eco Go y bancas de inversión, el agente **no debe limitarse a volcar números fríos**. Toda generación debe incorporar tres pilares:

### A. Tono Humano y Storytelling de Mesa de Dinero
- **Sin clichés de IA ni frases vacías:** Prohibido usar frases como *"en este informe exploraremos"*, *"es crucial destacar"*, *"un tapiz complejo"*, *"en conclusión"*.
- **Voz activa y directa:** Ir directo a la tesis central: *"La tasa fija de Lecaps cortas (TEM 2,95%) ofrece un premio real de +95 pb sobre la inflación esperada del REM (2,00%), convalidando el carry trade de corto plazo"*.
- **Tesis de Inversión y Asignación Táctica (Asset Allocation):** Cada sección debe responder claramente a:
  1. ¿Qué está descontando el mercado hoy?
  2. ¿Cuál es el riesgo asimétrico (upside vs. downside)?
  3. ¿Cuál es la ponderación recomendada para tesorerías y carteras (*Overweight / Neutral / Underweight*)?

### B. Elementos Visuales Llamativos de Alto Impacto
- **Tarjetas KPI Superiores:** En cada infografía a 300 DPI, incluir métricas clave con barras de color de acento.
- **Píldoras y Callouts Estratégicos:** Cajas destacadas para *"Tesis Central de la Mesa"* y *"Riesgos y Catalizadores"*.
- **Tablas con Coloración Condicional (*Heat-Maps*):** Gradiente verde/rojo según la magnitud y signo de la variación económica.
- **Semáforos de Decisión:** Indicadores claros de estado (*Carry Trade: Favorable*, *Presión Cambiaria: Baja*, *Curva Soberana: Extensión de Duration*).

---

## 2. Contrato de Datos: `01_Bases_Datos/datos_del_dia.json`

El agente debe consumir y/o actualizar el archivo JSON centralizado bajo el siguiente esquema canónico:

```json
{
  "fecha": "2026-08-21",
  "dolar": {
    "oficial_bna": 1515.00,
    "mayorista": 1485.00,
    "mep": 1532.33,
    "ccl": 1596.59,
    "blue": 1615.00,
    "brecha_ccl_oficial_pct": 5.39
  },
  "tasas_ars": {
    "lecap_corta_tem": 2.95,
    "lecap_larga_tem": 3.40,
    "boncer_tzx27_tir_real": 1.10,
    "breakeven_inflacion_tem": 2.86,
    "inflacion_esperada_rem_tem": 2.00,
    "premio_tasa_fija_pbs": 95
  },
  "inflacion": {
    "indec_general_mom": 2.2,
    "indec_regulados_mom": 3.0,
    "indec_servicios_mom": 2.9,
    "indec_nucleo_mom": 1.9,
    "deie_mendoza_mom": 2.3,
    "canasta_basica_total_mza": 963000,
    "canasta_basica_alimentaria_mza": 433000
  },
  "actividad": {
    "emae_interanual_pct": 3.1,
    "emae_desestacionalizado_mom_pct": 0.6,
    "isarc_mendoza_ia_pct": 3.4,
    "isarc_san_juan_ia_pct": 2.1,
    "isarc_san_luis_ia_pct": 5.8
  },
  "soberano_usd": {
    "al30_tir": 11.20,
    "gd30_tir": 9.80,
    "gd35_tir": 9.65,
    "gd38_tir": 9.70,
    "embi_riesgo_pais_pbs": 506,
    "nelson_siegel": {
      "beta0": 9.40,
      "beta1": 5.60,
      "beta2": -3.20,
      "tau": 2.40,
      "r2": 0.984
    }
  },
  "equity": {
    "merval_ars": 3156332,
    "merval_usd_ccl": 1976.92,
    "var_semanal_pct": 1.30,
    "lideres": [
      {"ticker": "YPFD", "ev_ebitda": 3.8, "margen_ebitda": 32.4, "recom": "SOBREPONDERAR"},
      {"ticker": "PAMP", "ev_ebitda": 4.1, "margen_ebitda": 38.5, "recom": "SOBREPONDERAR"},
      {"ticker": "GGAL", "ev_ebitda": 6.2, "margen_ebitda": 28.5, "recom": "SOBREPONDERAR"}
    ]
  }
}
```

---

## 3. Secuencia de Ejecución en 5 Pasos para el Agente

Cuando el agente sea convocado para actualizar o re-ejecutar el pipeline, debe seguir estrictamente este orden:

```
[PASO 1: Validación de Datos]
  │──> Validar datos_del_dia.json contra src/schema_datos_del_dia.json
  └──> Si faltan campos, aplicar fallback histórico sin arrojar excepciones.

[PASO 2: Generación de Infografías 300 DPI]
  │──> Ejecutar src/generador_graficos_hd.py
  └──> Verificar creación de los 9 archivos PNG en 03_Figuras_HD/

[PASO 3: Compilación de Documentos]
  │──> Nivel 1: src/generador_informe_diario.py (DOCX 2 págs)
  │──> Nivel 2: src/generador_paper_semanal.py (DOCX 4 págs APA 7)
  └──> Nivel 3: src/generador_informe_mensual_reportlab.py (PDF 14 págs ReportLab)

[PASO 4: Exportación Oficial PDF]
  │──> Convertir DOCX a PDF vía win32com.client para diario y semanal
  └──> Consolidar los 3 PDFs en 07_Reportes_Ejecutivos_PDF/

[PASO 5: Auditoría y Sincronización]
  │──> Ejecutar 02_Scripts_Automatizacion/verificar_estado_ecosistema.py
  └──> Sincronizar espejo 1:1 en C:\Users\fedea\Google Drive\coyuntura-macro
```

---

## 4. Auditoría de Integridad y Salida Sin Errores

El agente no debe dar por terminada su tarea sin verificar que `verificar_estado_ecosistema.py` devuelva:
- **Monitor Diario**: 2 páginas exactas (cobertura vertical > 75%).
- **Paper Semanal**: 4 páginas exactas (cobertura vertical > 60%).
- **Informe Mensual Master**: 14 páginas exactas (ReportLab con marcadores interactivos).
- **Google Drive**: Los 3 PDFs presentes y legibles.
- **Resultado final**: `AUDITORÍA FINALIZADA CON ÉXITO: 0 ERRORES`.
