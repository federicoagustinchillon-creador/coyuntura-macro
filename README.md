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
│   ├── generador_graficos_hd.py               # Renderizado de 10 infografías vectoriales a 300 DPI (diseño Tufte / FT)
│   ├── generador_informe_diario_reportlab.py  # Monitor Flash Diario (2 páginas exactas, doble columna y pull-quote)
│   ├── generador_paper_semanal_reportlab.py   # Paper Semanal Académico (4 páginas exactas APA 7, Nelson-Siegel, escenarios)
│   ├── generador_informe_mensual_reportlab.py # Informe Mensual Master (15 páginas exactas, 5 componentes editoriales superiores)
│   └── contexto_informe.py                    # Carga y estructuración del contexto macrofinanciero dinámico
│
├── 01_Bases_Datos/                            # Base de datos centralizada
│   └── Base_Datos_Macro_Financiera.xlsx       # 5 solapas: Cambiario, Curva USD, Pesos, BCRA, Inflación
│
├── 02_Scripts_Automatizacion/                 # Scripts de tareas programadas y auditoría
│   ├── ejecutar_pipeline_completo.bat         # Batch runner para Windows Task Scheduler
│   └── verificar_estado_ecosistema.py         # Auditor automático de páginas, figuras y cobertura vertical
│
├── 03_Figuras_HD/                             # 10 Infografías vectoriales en 300 DPI con diseño de banca privada
│   ├── chart_indec_emae_master.png            # Serie histórica 32 meses EMAE + Desest. + Tendencia-Ciclo
│   ├── chart_indec_1_rates.png                # Curva Lecaps vs. Boncer CER + Breakeven vs. REM
│   ├── chart_indec_2_ipc.png                  # Dispersión minorista/mayorista + Convergencia 2026
│   ├── chart_indec_3_cuyo.png                 # Vino fraccionado/granel + Petróleo convencional/Vaca Muerta Mza
│   ├── chart_indec_3b_regional_cuyo.png       # ISARC Mendoza/San Juan/San Luis + Var. i.a. sectorial
│   ├── chart_indec_4_monetary.png             # Pasivos monetarios Base/Lefi/Pases + Regla de Taylor
│   ├── chart_indec_5_sovereign.png            # Curva spot Nelson-Siegel Bonares/Globales + Forward f(t)
│   ├── chart_indec_6_fx.png                   # Cotizaciones y brechas spot + Futuros Matba-Rofex con prob. salto
│   ├── chart_indec_7_equity.png               # Renta variable líder + Radar EV/EBITDA vs. Margen
│   └── chart_indec_8_tcr.png                  # Tipo de Cambio Real Bilateral Argentina-EEUU (base 2016=100)
│
├── 04_Informes_Diarios/                       # Monitor Flash Diario de Mercados (2 páginas exactas)
│   └── 2026-08-25_Monitor_Diario_Mercados.pdf
│
├── 05_Informes_Semanales_APA7/                # Papers semanales de investigación macro (4 páginas exactas APA 7)
│   └── 2026-08-25_Paper_Macroeconomico_Semanal.pdf
│
├── 06_Informes_Mensuales_OERU/                # Informes mensuales de investigación (15 páginas exactas ReportLab)
│   └── Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf
│
└── 07_Reportes_Ejecutivos_PDF/                # Documentos ejecutivos consolidados listos para comités
    ├── 2026-08-25_Monitor_Diario_Mercados.pdf
    ├── 2026-08-25_Paper_Macroeconomico_Semanal.pdf
    └── Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf
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

## 3. Arquitectura Editorial Institucional (Estándar Wall Street / BIS)

Para garantizar un estándar visual y analítico a la altura de Goldman Sachs GIR, Fondo Monetario Internacional y Bank for International Settlements, se erradicó por completo la redundancia de cuadrículas de relleno ("tablitis"), reemplazándolas por 5 técnicas editoriales superiores calibradas al presupuesto vertical de página:

1. **Prosa Analítica en Doble Columna Asimétrica:** Descomposición causal de variables contrapuesta con implicancias operativas para tesorerías y carteras.
2. **Tesis Cuantitativa con Lead-ins en Negrita y Filete Capilar:** Factores críticos y catalizadores sectoriales estructurados jerárquicamente con borde lateral Oxford Navy (`#0B2545`).
3. **Matrices de Escenarios Condicionales Calibrados:** Proyecciones a 90/180 días con asignación de probabilidades paramétricas (Escenario Base, Tensión y Salida/Convergencia) y directrices tácticas.
4. **Formulaciones Matemáticas de Primeros Principios:** Bloques LaTeX embebidos para fundamentos teóricos rigurosos (Nelson-Siegel, Fisher Breakeven, Paridad CIP, Cagan/Baumol-Tobin, Mahalanobis).
5. **Pull-Quotes de Impacto Editorial:** Dictámenes ejecutivos de autor enmarcados por filetes capilares institucionales.

---

## 4. Instrucciones de Ejecución y Automatización Desatendida

Para ejecutar el pipeline completo de forma desatendida y sincronizada:

- **Desde consola Python / PowerShell:**
  ```powershell
  python pipeline_coyuntura_master.py
  ```

- **Desde Runner Automático (Windows Task Scheduler / Batch):**
  ```bat
  02_Scripts_Automatizacion\ejecutar_pipeline_completo.bat
  ```

- **Auditoría Automática de Integridad y Cobertura:**
  ```powershell
  python 02_Scripts_Automatizacion/verificar_estado_ecosistema.py
  ```

El pipeline ejecutará automáticamente la validación de bases, renderizado de las 10 infografías vectoriales a 300 DPI con diseño Tufte / FT, compilación de los 3 niveles de informes en ReportLab (Mensual de 15 páginas exactas, Semanal de 4 páginas y Diario de 2 páginas), exportación oficial de entregables ejecutivos tanto localmente como en el espejo canónico de Google Drive (`C:\Users\fedea\Google Drive\coyuntura-macro`).

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
