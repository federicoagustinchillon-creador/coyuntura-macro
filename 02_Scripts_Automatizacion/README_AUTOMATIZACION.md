# PROTOCOLO DE AUTOMATIZACIÓN Y OPERACIONES DESATENDIDAS
## Ecosistema de Coyuntura Macroeconómica y Finanzas Cuantitativas
**Autor:** Federico Agustín Chillón  
**Institución:** Facultad de Ciencias Económicas — UNCUYO / OERU  

---

### 1. Arquitectura de Ejecución Desatendida
El pipeline maestro `pipeline_coyuntura_master.py` orquesta la totalidad del ciclo operativo macro-financiero:
1. **Actualización de Bases de Datos:** Validación y construcción de `01_Bases_Datos/Base_Datos_Macro_Financiera.xlsx` con 5 solapas vivas.
2. **Generación Gráfica HD (300 DPI):** Renderizado de las 8 figuras estadísticas panorámicas vectoriales 16:9 con paleta institucional Oxford Navy / Deep Wine.
3. **Compilación de Reportes Word (3 Niveles):**
   - **Nivel 1 (Diario):** Monitor Flash de Mercados (2 páginas exactas, densidad > 80%).
   - **Nivel 2 (Semanal):** Paper Académico APA 7 (4 páginas exactas, modelos Taylor / Nelson-Siegel / CIP).
   - **Nivel 3 (Mensual):** Informe Master OERU (12 páginas exactas, TOC dinámico, Scorecard macro, 8 capítulos y monitor global).
4. **Exportación Automatizada a PDF:** Conversión desatendida mediante Microsoft Word COM Automation (`win32com.client`).
5. **Sincronización Espejo con Google Drive:** Replicación 1:1 en `C:\Users\fedea\Google Drive\coyuntura-macro`.

---

### 2. Comandos y Runners Rápidos
- **Ejecución Completa del Pipeline:**
  ```bat
  02_Scripts_Automatizacion\ejecutar_pipeline_completo.bat
  ```
  o mediante Python:
  ```bash
  python pipeline_coyuntura_master.py
  ```
- **Auditoría de Integridad y Cobertura:**
  ```bash
  python 02_Scripts_Automatizacion/verificar_estado_ecosistema.py
  ```

---

### 3. Programación de Tareas en Windows (Task Scheduler)
Para automatizar la ejecución diaria en Windows:
- **Acción:** Iniciar un programa
- **Programa o script:** `C:\Users\fedea\Downloads\coyuntura-macro\02_Scripts_Automatizacion\ejecutar_pipeline_completo.bat`
- **Iniciar en:** `C:\Users\fedea\Downloads\coyuntura-macro`
- **Frecuencia recomendada:** Días hábiles a las 18:30 ART (cierre de ByMA y publicación de estadísticas BCRA).
