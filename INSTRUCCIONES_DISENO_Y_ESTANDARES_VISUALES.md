# MANUAL DE DISEÑO INSTITUCIONAL, MAQUETACIÓN Y ESTÁNDARES VISUALES
## Sistema de Publicaciones Económicas de Federico Agustín Chillón
**Cs. Económicas UNCUYO · Investigación Cuantitativa Independiente**

---

### 1. Filosofía Editorial y Anti-Slop Estricto
1. **Sobriedad de Banca de Inversión / INDEC**: Prohibición total de elementos decorativos innecesarios, emojis, marcos fluorescentes, degradados estridentes o terminología no institucional.
2. **Español Financiero Formal**: Prohibición de anglicismos superfluos (`Overweight` $\to$ **Sobreponderar**, `Neutral` $\to$ **Neutral / Mantener**, `Underweight` $\to$ **Subponderar / Reducir**, `Carry trade` $\to$ **Arbitraje de Tasa / Carry Trade**).
3. **Densidad Analítica sin Relleno**: Cada página debe ser autosuficiente (*Single-Topic Page Architecture*), combinando:
   - Título H1 formal y riguroso.
   - Dos párrafos sustantivos de fundamentación econométrica y coyuntura (sin texto de relleno ni frases genéricas de IA).
   - Tabla institucional formateada con anchos de columna dedicados y alineaciones numéricas exactas.
   - Figura estadística en Ultra-HD (300 DPI) con diseño estilo INDEC / ByMA.

---

### 2. Tokens Cromáticos Institucionales

| Token | Código HEX | RGB | Uso Institucional |
| :--- | :--- | :--- | :--- |
| **Oxford Navy** | `#0C2340` | `(12, 35, 64)` | Encabezados H1, bordes rectores, títulos de tarjetas, curvas base, bandas de tabla. |
| **Deep Wine / Borgoña** | `#722F37` | `(114, 47, 55)` | Encabezados H2, variaciones negativas, alertas de riesgo, curvas Bonares. |
| **Forest Green / Esmeralda** | `#0D5C46` | `(13, 92, 70)` | Variaciones positivas, recomendaciones de sobreponderación, tasa Lefi. |
| **Warm Amber / Ocre** | `#B45309` | `(180, 83, 9)` | Posición neutral, curvas reales Boncer, dólar MEP/CCL, alertas moderadas. |
| **Slate Charcoal** | `#0F172A` | `(15, 23, 42)` | Texto principal, métricas en negrita, datos primarios de series. |
| **Slate Gray / Muted** | `#64748B` | `(100, 116, 139)` | Textos secundarios, fuentes, notas al pie, encabezados de página. |
| **Surface Off-White** | `#F8FAFC` | `(248, 250, 252)` | Fondo de tarjetas KPI, filas alternadas de tablas. |
| **Border Slate** | `#CBD5E1` | `(203, 213, 225)` | Bordes sutiles de contenedores y grillas de gráficos. |

---

### 3. Reglas de Maquetación en Microsoft Word COM / python-docx

1. **Portada Full-Bleed al Borde Físico de Hoja**:
   - Sección 1: `w:pgMar` forzado en XML a `0` absoluto (`top=0, bottom=0, left=0, right=0, header=0, footer=0`).
   - Imagen de portada a `8.5 x 11.0 in` con espaciado de párrafo exacto a `0.1 pt`.
2. **Cuerpo del Informe (Páginas 2 a 12)**:
   - Márgenes: Superior e Inferior `0.40 in`, Izquierdo y Derecho `0.55 in`.
   - Distancia de Encabezado/Pie: `0.20 in`.
   - Salto de página explícito al final de cada capítulo para garantizar exactamente 12 páginas.
3. **Página 3 (Resumen Ejecutivo & Scorecard)**:
   - Cuadrantes de desempeño 2x2 en contenedores con bordes sutiles (`#CBD5E1`, 8 dxa) y fondos suaves (`#F8FAFC`, `#F0FDF4`, `#FFFBEB`, `#EFF6FF`).
   - Cero solapamiento de líneas con texto: márgenes internos de celda con `top=16, bottom=16, left=24, right=24 dxa`.
   - Distribución vertical equilibrada que llena la página de margen a margen.

---

### 4. Estándares de Renderizado de Figuras Estadísticas (300 DPI)

* **Resolución**: `2048 x 1536 px` (equivalente a 300 DPI para impresión editorial).
* **Composición**: Contenedor institucional con tarjeta redondeada (radio 28 px), píldora de fecha superior, 3 KPI cards de cabecera con bandas de color, panel gráfico principal de alta densidad y pie con fuente oficial y logotipo.
* **Etiquetas de Datos**: 100% de los puntos relevantes, barras y aperturas deben contener sus etiquetas numéricas formateadas (`+14,2%`, `$1.596,59`, `35,4%`, etc.).
