# Plan: Conector de feeds en vivo -> datos_del_dia.json (historico)

> **SUPERADO (2026-08-25).** Este documento registraba la primera iteracion
> del conector de feeds en vivo. Esa version fue reemplazada el mismo dia
> tras encontrarse una discrepancia de ~45% entre el registro macro interno
> y la fuente oficial (BCRA). La arquitectura vigente ya no vive en este
> documento -- ver los docstrings de `src/fetch_datos_reales.py` y
> `src/sync_datos_del_dia.py`, que son la fuente de verdad actualizada y se
> mantienen junto al codigo en vez de en un doc separado que se desactualiza.

## Resumen de lo que cambio

- **Version 1 (mañana):** un registro macro interno local era la fuente de
  cambiario/CCL/brecha, mapeado campo a campo a `datos_del_dia.json`.
- **Hallazgo:** el registro no coincidia con la fuente oficial (BCRA
  publicaba tipo de cambio oficial ~1531 el mismo dia que el registro
  interno informaba ~1055).
- **Version 2 (tarde):** BCRA (`api.bcra.gob.ar` v4.0) + `yfinance` pasan a
  ser la fuente primaria verificable para cambiario/tasas/Merval.
- **Version 3 (misma tarde):** el registro interno se corrigio en su propia
  fuente y ahora tagea cada campo con su procedencia real
  (`<campo>__source = "LIVE:..."` o `"STALE_FALLBACK:..."`). Con esa
  trazabilidad vuelve a ser la fuente primaria para cambiario/tasas/vistas
  tacticas -- pero solo se confia en un campo si su propio tag dice LIVE.
  BCRA/yfinance quedan como respaldo automatico para lo que no venga en
  vivo en una corrida puntual, y como unica fuente del indice Merval.

## Fuera de alcance (tareas separadas, no se tocan en este cambio)
- Reescribir `actualizador_datos.py` para eliminar los datos sinteticos
  (`np.random`) del Excel -- violacion de grounding gate detectada, se deja
  documentada para una tarea dedicada.
- Feeds de BYMA/Matba-Rofex/INDEC para los campos que ninguna fuente
  automatica cubre todavia (`dolar.mep/blue`, `tasas_ars`, `inflacion`,
  `actividad`, `soberano_usd`, multiplos de `equity`).
