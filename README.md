# Pipeline de Investigación Macroeconómica Cuantitativa y Mercado de Capitales

Sistema integral y automatizado de ingesta de datos, modelización econométrica y publicación periódica (diaria, semanal y mensual) de informes de coyuntura macroeconómica argentina y regional para comités de inversión, mesas de dinero y el ámbito académico.

**Autor:** Federico Agustín Chillón  
**Afiliación:** Investigación Cuantitativa Independiente · Ciencias Económicas — Universidad Nacional de Cuyo  

**➜ [Ver el dashboard en vivo](https://federicoagustinchillon-creador.github.io/coyuntura-macro/)** -- demo pública sin necesidad de clonar el repositorio ni instalar nada (ver sección 4).

---

## 1. Arquitectura Modular del Repositorio

```
coyuntura-macro/
│
├── pipeline_coyuntura_master.py               # Orquestador integral de ejecución desatendida
├── AGENTS.md                                  # Protocolo mandatorio de ejecución y sincronización
├── README.md                                  # Documentación técnica, metodológica y operativa
│
├── src/                                       # Módulos de procesamiento analítico y compilación editorial
│   ├── actualizador_datos.py                  # Ingesta, consolidación y cálculo de tasas reales (Fisher)
│   ├── generador_graficos_echarts.py          # Renderizado Tier-1 con Apache ECharts 5 Headless (Chromium a 300 DPI)
│   ├── generador_informe_diario_reportlab.py  # Monitor Flash Diario (2 páginas exactas, cobertura 100%, figuras duales)
│   ├── generador_paper_semanal_reportlab.py   # Paper Semanal Académico APA 7 (4 páginas exactas, tablas de 10 filas, Nelson-Siegel)
│   ├── generador_informe_mensual_reportlab.py # Informe Mensual Master (16 páginas exactas, portada Wall Street Tear-Sheet, Tablero Integral, 11 paneles)
│   ├── generador_apendice_econometrico.py     # Apéndice Cuantitativo & Gobernanza Empírica (modelos de curvas, Fisher, Nelson-Siegel, PCA)
│   ├── compilador_informes.py                 # Orquestador de la suite ReportLab con pre-compilación gráfica ECharts 5
│   └── contexto_informe.py                    # Carga y estructuración del contexto macrofinanciero dinámico
│
├── 01_Bases_Datos/                            # Base de datos centralizada
│   └── Base_Datos_Macro_Financiera.xlsx       # 5 solapas: Cambiario, Curva USD, Pesos, BCRA, Inflación
│
├── 02_Scripts_Automatizacion/                 # Scripts de tareas programadas y auditoría
│   ├── ejecutar_pipeline_completo.bat         # Batch runner para Windows Task Scheduler
│   └── verificar_estado_ecosistema.py         # Auditor automático de páginas, figuras y cobertura vertical
│
├── 03_Figuras_HD/                             # 11 Infografías editoriales duales en 300 DPI (estándar Management Solutions / FT)
│   ├── chart_editorial_emae.png               # Panel dual: Evolución EMAE Desest. + Variación Interanual Sectorial
│   ├── chart_editorial_ipc.png                # Panel dual: Dispersión por Categorías + Trayectoria Desinflacionaria INDEC
│   ├── chart_editorial_canastas.png           # Panel dual: Evolución Canastas CBT/CBA + Comparativa Regional
│   ├── chart_editorial_cuyo.png               # Panel dual: Producción Vitivinícola + Despachos y Extracción de Hidrocarburos Cuyo
│   ├── chart_editorial_regional_cuyo.png      # Panel dual: Índice Sintético ISARC + Dispersión Sectorial Provincial
│   ├── chart_editorial_monetary.png           # Panel dual: Pasivos Remunerados BCRA/PBI + Base Monetaria Ampliada
│   ├── chart_editorial_rates.png              # Panel dual: Curva Lecaps Spot TEM + Breakeven Inflacionario vs. Boncer CER
│   ├── chart_editorial_sovereign.png          # Panel dual: Curva Soberana Spot Nelson-Siegel USD + Estructura Forward f(t)
│   ├── chart_editorial_fx.png                 # Panel dual: Cotizaciones Spot CCL/MEP + Curva Teórica de Futuros Matba-Rofex CIP
│   ├── chart_editorial_tcr.png                # Panel dual: Tipo de Cambio Real Multilateral (TCRM) + Bilateral con Socios
│   └── chart_editorial_equity.png             # Panel dual: Desempeño S&P Merval + Dispersión Retorno/Volatilidad ByMA
│
├── 04_Informes_Diarios/                       # Monitor Flash Diario de Mercados (2 páginas exactas)
│   └── 2026-08-25_Monitor_Diario_Mercados.pdf
│
├── 05_Informes_Semanales_APA7/                # Papers semanales de investigación macro (4 páginas exactas APA 7)
│   └── 2026-08-25_Paper_Macroeconomico_Semanal.pdf
│
├── 06_Informes_Mensuales/                     # Informes mensuales de investigación (16 páginas exactas ReportLab)
│   └── Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf
│
├── 07_Reportes_Ejecutivos_PDF/                # Documentos ejecutivos consolidados listos para comités
│   ├── Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf
│   ├── Apendice_Econometrico_y_Validacion_Modelos_Agosto_2026.pdf
│   ├── 2026-08-25_Monitor_Diario_Mercados.pdf
│   └── 2026-08-25_Paper_Macroeconomico_Semanal.pdf
│
└── sincronizar_ecosistema_drive.py            # Sincronizador automático a Google Drive (C:\Users\fedea\Google Drive\coyuntura-macro)
```

---

## 2. Metodología y Modelización Econométrica

### A. Estructura Temporal de Tasas de Interés (Nelson-Siegel, 1987)
Para la curva soberana en moneda extranjera (Globales Ley NY vs. Bonares Ley Local), se implementa el ajuste paramétrico no lineal:
$$y(t) = \beta_0 + \beta_1 \left( \frac{1 - e^{-t/\tau}}{t/\tau} \right) + \beta_2 \left( \frac{1 - e^{-t/\tau}}{t/\tau} - e^{-t/\tau} \right)$$
Donde $\beta_0$ modela el nivel asintótico de largo plazo, $\beta_1$ la pendiente y $\beta_2$ la curvatura de mediano plazo, calibrado con factor de decaimiento $\tau = 2,40$ ($R^2 = 0,984$, $\text{RMSE} = 14\text{ bps}$).

La tasa forward instantánea implícita se deriva analíticamente como:
$$f(t) = \beta_0 + \beta_1 e^{-t/\tau} + \beta_2 \frac{t}{\tau} e^{-t/\tau}$$

### B. Ecuación de Fisher y Breakeven de Inflación Ex-Ante en Pesos
$$r_{real} = \frac{1 + \text{TEM}_{lecap}}{1 + \pi_{REM}^{esperada}} - 1$$
Permite cuantificar la prima real positiva capturada por la deuda a tasa fija frente al consenso de analistas del Relevamiento de Expectativas de Mercado (REM).

### C. Sensibilidad y Convexidad de Precios de Títulos Públicos (Taylor)
$$\frac{\Delta P}{P} \approx -D_{mod} \cdot \Delta y + \frac{1}{2} C \cdot (\Delta y)^2$$
Permite estimar la asimetría de retornos totales en USD ante compresiones o ampliaciones del riesgo país (EMBI+).

### D. Tasa Implícita en Futuros Cambiarios (Matba-Rofex)
$$\text{TNA}_{impl\acute{\imath}cita} = \left( \frac{F_T - S_0}{S_0} \right) \cdot \frac{365}{T}$$

### E. Índice Sintético de Actividad Regional de Cuyo (ISARC)
Índice compuesto ponderado por sector (vitivinicultura, minería/hidrocarburos, cemento y empleo registrado) para evaluar la heterogeneidad productiva entre Mendoza, San Juan y San Luis:
$$\text{ISARC}_{i,t} = \sum_{k=1}^K w_k \cdot I_{i,k,t}$$

### F. Tipo de Cambio Real Bilateral (Atraso/Competitividad Cambiaria)
Distinto de la brecha cambiaria (prima de mercado paralelo por cepo): mide la desalineación del tipo de cambio frente al poder de compra relativo entre Argentina y Estados Unidos, indexado a 100 en diciembre de 2016 (misma base que el IPC nacional vigente del INDEC):
$$\text{TCR}_{indice}(t) = 100 \cdot \frac{TCN(t)}{TCN(t_0)} \cdot \frac{P_{EEUU}(t)/P_{EEUU}(t_0)}{P_{ARG}(t)/P_{ARG}(t_0)}$$
### G. Fragilidad y Co-Movimiento Sistémico (Kritzman & Li, 2010)
Para monitorear el riesgo de contagio multiactivo sin relying en correlaciones lineales simples:
$$\text{Absorption Ratio} = \frac{\sum_{j=1}^k \lambda_j}{\sum_{i=1}^N \lambda_i}, \quad d_t^2 = (y_t - \mu)' \Sigma^{-1} (y_t - \mu)$$
Donde $d_t^2$ representa la distancia de Mahalanobis frente a la distribución histórica conjunta de rendimientos, alertando desacoples de liquidez.

### H. Demanda Monetaria y Equilibrio de Pasivos (Cagan / Baumol-Tobin)
$$\ln(M/P)_t = \alpha_0 - \eta \, i_t + \gamma \, y_t + \varepsilon_t$$
Formaliza la elasticidad de la demanda de dinero frente a la tasa nominal de política monetaria ($i_t$) y la extinción de pasivos remunerados del BCRA.

---

## 3. Arquitectura Editorial Institucional (Estándar Management Solutions / Wall Street Sell-Side)

Para garantizar un estándar visual y analítico a la altura de Goldman Sachs GIR, Fondo Monetario Internacional, Bank for International Settlements y las publicaciones macroeconómicas de *Management Solutions*, se erradicó por completo el "card-itis" (cajas rectangulares de relleno, banners plásticos y bordes coloreados), adoptando una disciplina de diseño cuantitativo de 5 capas:

1. **Portada Wall Street Tear-Sheet en 2 Columnas Asimétricas:** Mástil institucional formal, titular hero cuantitativo, diagnóstico ejecutivo macroeconómico denso a la izquierda (330 pt) contrapuesto con la matriz de asignación táctica y el scorecard de mercado a la derecha (192 pt).
2. **Tablas Estructuradas de Indicadores de 10-12 Filas:** Cabecera azul marino Oxford (`#0B2545`), filas alternadas (`#F8FAFC` y blanco), columna de proyecciones diferenciada y variaciones porcentuales coloreadas en verde/rojo según el impacto macroeconómico.
3. **Prosa Analítica en Palatino Linotype:** Párrafos en tipografía Palatino Linotype (8.7 pt / leading 12.4 pt) con alineación ragged-right (`TA_LEFT`) en viñetas de 3–4 líneas para erradicar ríos de texto forzado, viñetas triangulares institucionales (`▸`) en azul institucional (`#0284C7`), conceptos clave en negrita y sin cajas cerradas.
4. **Figuras Editoriales ECharts 5 con Barras Rectangulares y Valor Analítico Agregado:** 11 figuras de panel dual calibradas a 532 pt de ancho con borde capilar `#CBD5E1`. Eliminación de bordes redondeados (`borderRadius: 0`), colores profundos (Verde Esmeralda `#047857`, Rojo Burdó `#B91C1C`, Oxford Navy `#0B2545`), etiquetas numéricas directas con halo blanco anticolisión, líneas de referencia histórica (Media EMAE 147,8 pts, Pauta Crawling 2,0% m/m, Banda Paridad Fundamental TCRM 95–105) y visibilidad garantizada del último dato (`showMaxLabel: True`).
5. **Arquitectura de 4 Arquetipos Editoriales Rítmicos (Páginas 4 a 14):**
   - **Arquetipo Scorecard (Págs. 4 y 8):** Pestaña temática de bloque, tabla comparativa con micro-barras de variación y bloques analíticos temáticos precedidos por viñetas triangulares (`▸`).
   - **Arquetipo Desglose Multicontable (Págs. 5, 7, 9 y 13):** Lead-in con filetes horizontales finos, gran matriz contable agrupada y 3 párrafos de alta densidad.
   - **Arquetipo Monitor Social (Pág. 6):** Doble tarjeta ejecutiva superior de canastas (CBA Indigencia vs. CBT Pobreza) y matriz salarial RIPTE.
   - **Arquetipo Asimétrico Wall Street (Págs. 10 y 12):** 2 columnas (60% narrativa analítica / 40% scorecard táctico vertical y catalizadores) con figura al pie.
   - **Arquetipo TopChart Inversor (Págs. 11 y 14):** Ruptura de monotonía con figura analítica en el tercio superior, seguida de matriz de valuación activo por activo y conclusiones de cartera.
   - **Pestañas Marginales Laterales (Lateral Thumb Tabs):** Marcadores visuales en el margen izquierdo según el bloque macroeconómico (Bloque I Verde `#047857`, Bloque II Azul `#0284C7`, Bloque III Marrón `#9A3412`, Bloque IV Gris `#475569`).
6. **Presupuesto Vertical Estricto (Page Budget):** Cobertura entre 80% y 91% en cada página, eliminando huecos muertos al pie. Conteos inmutables:
   - **Informe Mensual:** 15 páginas exactas (Portada Tear-Sheet, Índice, Resumen Ejecutivo, 11 Capítulos temáticos con arquetipos dinámicos y Flash Normativo/Metodología).
   - **Paper Semanal APA 7:** 4 páginas exactas (Portada académica y resumen, Arbitraje de Tasas, Nelson-Siegel y Microestructura FX con referencias bibliográficas).
   - **Monitor Diario:** 2 páginas exactas (Diagnóstico y Microestructura Cambiaria spot/Rofex + Curvas Soberanas, Tasas y Asignación Táctica).

---

## 4. Instrucciones de Ejecución y Sincronización Automática

Para ejecutar el pipeline completo de forma desatendida y sincronizada:

- **Desde consola Python / PowerShell:**
  ```powershell
  python pipeline_coyuntura_master.py
  ```

- **Desde Runner Automático (Windows Task Scheduler / Batch):**
  ```bat
  02_Scripts_Automatizacion\ejecutar_pipeline_completo.bat
  ```

- **Sincronización Inmediata a Google Drive:**
  ```powershell
  python sincronizar_ecosistema_drive.py
  ```

El pipeline ejecuta automáticamente la validación de bases, renderizado de las 11 figuras editoriales compactas a 300 DPI, compilación de los 3 niveles de informes en ReportLab (15, 4 y 2 páginas exactas), y exportación de entregables tanto en disco local como en el repositorio espejo de Google Drive (`C:\Users\fedea\Google Drive\coyuntura-macro`).

---

## 5. Feeds en Vivo y Dashboard Web de Acompañamiento

Para el consumo entre informes (lunes a jueves), ademas del ciclo editorial
de PDFs, el ecosistema expone:

- **Conector de feeds en vivo** (`src/sync_datos_del_dia.py`): antes de
  cada corrida del pipeline (Paso 0), sincroniza `01_Bases_Datos/
  datos_del_dia.json` contra fuentes oficiales verificables -- BCRA
  (`api.bcra.gob.ar`) para cambiario/tasas y `yfinance` para el indice
  Merval, con un registro macro interno como capa adicional para vistas
  tacticas de inversion. Solo se toman campos con equivalencia exacta y
  trazabilidad de fuente; el resto del contrato sigue siendo carga manual
  por diseno. Ver `implementation_plan.md` para el detalle campo a campo.

- **Dashboard web** (`dashboard/`): terminal fintech (FastAPI + Tailwind +
  Alpine.js + Apache ECharts) que sirve en vivo el contenido vigente de
  `datos_del_dia.json`, re-sincronizando en cada request. Arranque local:
  ```powershell
  pip install -r dashboard/requirements.txt
  uvicorn dashboard.api:app --reload --port 8420
  ```
  Luego abrir `http://127.0.0.1:8420`. Los campos con borde verde en las
  tarjetas KPI indican dato vivo verificado contra su fuente oficial; el
  resto es carga manual.

- **Demo pública estática** (`docs/`, servida por GitHub Pages en
  [federicoagustinchillon-creador.github.io/coyuntura-macro](https://federicoagustinchillon-creador.github.io/coyuntura-macro/)):
  para quien entra al repositorio desde GitHub y no va a clonar ni instalar
  nada, una version de solo lectura del mismo dashboard. No corre FastAPI
  (GitHub Pages es hosting estatico puro) -- carga una instantanea publicada
  (`docs/snapshot.json` + `docs/historico.json`, generados por
  `dashboard/build_static_export.py`) y, ademas, trae **oficial, mayorista y
  CCL en vivo de verdad** con el boton "Actualizar cotizaciones ahora": BCRA
  y DolarAPI habilitan CORS publico, asi que el navegador les pega
  directo, sin backend intermedio. El indice Merval (yfinance) no expone un
  endpoint asi, asi que se muestra fijo a la fecha de la instantanea en vez
  de prometer algo que la arquitectura estatica no puede cumplir.

  Para refrescar la instantanea publicada antes de compartir el link:
  ```powershell
  python dashboard/build_static_export.py
  git add docs/ && git commit -m "chore(docs): refresca instantanea publica" && git push
  ```

  *Habilitacion (una sola vez, manual):* en GitHub, `Settings → Pages →
  Source: Deploy from a branch → Branch: main, carpeta /docs`. Sin este
  paso el link de arriba todavia no responde.
