# Plan: Conector de feeds en vivo SecondBrain -> datos_del_dia.json

## Objetivo
Cerrar el gap #1 del roadmap (feeds en vivo) conectando `coyuntura-macro` a la
fuente de verdad ya viva en `C:\Users\fedea\SecondBrain\core\macro_coyuntura\
live_macro_views_registry.json`, reemplazando la carga 100% manual del
contrato de datos por una sincronizacion automatica de los campos que
SecondBrain efectivamente cubre.

## Fuente
Archivo local, no-git, actualizado por el pipeline de SecondBrain:
`C:\Users\fedea\SecondBrain\core\macro_coyuntura\live_macro_views_registry.json`

Se lee el archivo directamente (no via protocolo MCP stdio) porque:
- Es la misma fuente que expone la tool `get_live_macro_views`.
- Un script standalone (`python pipeline_coyuntura_master.py`, Task Scheduler)
  no tiene sesion de agente para hablar MCP; el archivo si es accesible.

## Mapeo campo a campo (solo equivalencias exactas, sin conversiones inventadas)

| SecondBrain (`macro_indicators`)     | datos_del_dia.json          | Nota |
|---------------------------------------|------------------------------|------|
| `tipo_de_cambio_oficial`              | `dolar.oficial_bna`          | equivalencia directa |
| `ccl_mercado`                         | `dolar.ccl`                  | equivalencia directa |
| `brecha_cambiaria_pct`                | `dolar.brecha_ccl_oficial_pct` | equivalencia directa |
| `timestamp` (fecha)                   | `fecha`                      | se toma la fecha del sync |

Campos de SecondBrain **sin** equivalencia limpia en el schema actual
(no se mapean para no fabricar conversiones): `reservas_brutas_usd_m`,
`tna_politica_monetaria_pct`, `ipc_mensual_proyectado_pct` (es *proyeccion*,
no dato INDEC realizado -> no debe pisar `inflacion.indec_general_mom`),
`crawl_rate_mensual_pct`, `real_carry_spread_mensual_pct`.

Campos de `datos_del_dia.json` que SecondBrain no cubre y siguen manuales:
`dolar.mayorista/mep/blue`, todo `tasas_ars`, todo `inflacion`, todo
`actividad`, `soberano_usd` (TIRes, Nelson-Siegel), `equity` (Merval,
lideres EV/EBITDA).

`black_litterman_tactical_views` (ALUA.BA, GD30.BA, GGAL.BA con tesis) se
agrega como bloque nuevo opcional (no rompe el schema, que no tiene
`additionalProperties: false`) para que los compiladores de informes puedan
citarlo textualmente en la seccion de Tesis de Inversion, sin fabricar
campos que el schema de equity si exige (`ev_ebitda`, `margen_ebitda`).

## Implementacion

1. `src/sync_secondbrain_macro.py`
   - Lee el registry de SecondBrain (ruta configurable via env var
     `SECONDBRAIN_REGISTRY_PATH`, default a la ruta real).
   - Si el archivo no existe: log de advertencia y salida sin tocar
     `datos_del_dia.json` (no rompe el pipeline si SecondBrain no esta
     disponible en esa maquina).
   - Carga `datos_del_dia.json`, aplica solo el mapeo de la tabla, agrega
     `black_litterman_tactical_views`, actualiza `fecha`.
   - Valida el resultado contra `src/schema_datos_del_dia.json` antes de
     escribir (reusa la logica de `agent_runner.validar_datos_del_dia`).
   - Imprime un resumen: que campos se actualizaron con dato real, cuales
     siguen manuales.

2. `pipeline_coyuntura_master.py`
   - Nuevo Paso 0, antes de `construir_base_datos_macro`: llama a
     `sincronizar_desde_secondbrain()`.

## Fuera de alcance (tareas separadas, no se tocan en este cambio)
- Reescribir `actualizador_datos.py` para eliminar los datos sinteticos
  (`np.random`) del Excel — violacion de grounding gate detectada, se deja
  documentada para una tarea dedicada.
- Feeds de BYMA/Matba-Rofex/BCRA/INDEC para los campos que SecondBrain no
  cubre.
