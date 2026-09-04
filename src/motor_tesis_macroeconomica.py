# -*- coding: utf-8 -*-
"""
================================================================================
MOTOR ECONOMETRICO DE TESIS MACROECONOMICA & ASIGNACION TACTICA DINAMICA
================================================================================
Autor: Federico Agustin Chillon
Filiacion: Facultad de Ciencias Economicas -- Universidad Nacional de Cuyo (UNCUYO)

Genera diagnosticos, dictamenes de politica, senales de arbitraje y carteras
tacticas 100% dinamicas segun las condiciones cuantitativas de la economia real,
regimen monetario, mercado cambiario y deuda soberana.
================================================================================
"""

def _fmt_dec(v, dec=1, signo=False):
    if v is None:
        return "s/d"
    p = "+" if signo and v >= 0 else ""
    return f"{p}{v:.{dec}f}".replace(".", ",")

def _fmt_dinero(v, dec=2):
    if v is None:
        return "0,00"
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_tesis_completa(ctx):
    dolar = ctx.get("dolar", {})
    tasas = ctx.get("tasas_ars", {})
    inflacion = ctx.get("inflacion", {})
    actividad = ctx.get("actividad", {})
    soberano = ctx.get("soberano_usd", {})
    ns = soberano.get("nelson_siegel", {})
    dolar_futuro = ctx.get("dolar_futuro_implicito", {})
    riesgo_sist = ctx.get("riesgo_sistemico", {})

    # 1. Extraccion de metricas
    ipc_gral = inflacion.get("indec_general_mom", 2.2)
    ipc_core = inflacion.get("indec_nucleo_mom", 1.9)
    ipc_reg = inflacion.get("indec_regulados_mom", 3.0)
    deie_mza = inflacion.get("deie_mendoza_mom", 2.3)

    lecap_corta = tasas.get("lecap_corta_tem", 2.95)
    rem_1m = tasas.get("inflacion_esperada_rem_tem", 2.00)
    tasa_real_exante = round(lecap_corta - rem_1m, 2)
    breakeven_1y = tasas.get("breakeven_inflacion_tem", 2.86)
    premio_tf_pb = tasas.get("premio_tasa_fija_pbs", int(round((breakeven_1y - rem_1m) * 100)))

    ccl = dolar.get("ccl", 1600.20)
    brecha_ccl = dolar.get("brecha_ccl_oficial_pct", 4.52)
    cip_30d = dolar_futuro["curva"][0]["futuro_implicito"] if dolar_futuro and dolar_futuro.get("curva") else 1556.12
    cip_tna = dolar_futuro["curva"][0]["tna_implicita_pct"] if dolar_futuro and dolar_futuro.get("curva") else 35.4

    embi = soberano.get("embi_riesgo_pais_pbs", 506)
    beta0 = ns.get("beta0", 9.4)

    emae_ia = actividad.get("emae_interanual_pct", 3.1)
    emae_mom = actividad.get("emae_desestacionalizado_mom_pct", 0.6)
    isarc_mdz = actividad.get("isarc_mendoza_ia_pct", 3.4)
    isarc_sl = actividad.get("isarc_san_luis_ia_pct", 5.8)

    ar_val = riesgo_sist.get("absorption_ratio_pct", 42.6)
    turb_val = riesgo_sist.get("turbulencia_dt", 2.05)
    regimen = riesgo_sist.get("regimen", "Normal")

    # 2. Diagnósticos Dinámicos de 4 Pilares
    brecha_tarifaria = round(ipc_reg - ipc_core, 2)
    if ipc_core <= 2.0 and ipc_gral <= 2.5:
        if brecha_tarifaria > 0.5:
            diag_inflacion = (
                f"El registro de inflación de <b>{_fmt_dec(ipc_gral)}% m/m</b> (con núcleo disciplinada en <b>{_fmt_dec(ipc_core)}%</b> "
                f"y DEIE Mendoza en <b>{_fmt_dec(deie_mza)}%</b>) ratifica la convergencia del ancla nominal, donde la brecha "
                f"de regulados vs. núcleo (+{_fmt_dec(brecha_tarifaria)} p.p.) absorbe el reacomodamiento de precios relativos sin desanclar expectativas"
            )
        else:
            diag_inflacion = (
                f"La desaceleración homogénea del IPC (general <b>{_fmt_dec(ipc_gral)}% m/m</b>, núcleo <b>{_fmt_dec(ipc_core)}%</b>) "
                f"confirma el éxito de la disciplina fiscal-monetaria en el quiebre de la inercia inflacionaria"
            )
    elif ipc_core > 2.5:
        diag_inflacion = (
            f"El IPC general en <b>{_fmt_dec(ipc_gral)}% m/m</b> con una núcleo persistente en <b>{_fmt_dec(ipc_core)}%</b> "
            f"evidencia rigidez a la baja en el componente no transable, demandando sostener una postura contractiva"
        )
    else:
        diag_inflacion = (
            f"El registro inflacionario de <b>{_fmt_dec(ipc_gral)}% m/m</b> refleja una desaceleración moderada en transición hacia la meta de convergencia"
        )

    if tasa_real_exante >= 0.8:
        diag_tasa = (
            f"esto sumado a una tasa real ex-ante contractiva de <b>+{_fmt_dec(tasa_real_exante)}% mensual</b> en Lecaps cortas "
            f"(TEM {_fmt_dec(lecap_corta)}% vs. REM {_fmt_dec(rem_1m)}%), esteriliza la liquidez excedente y asegura un atractivo "
            f"premio por carry trade en pesos (+{premio_tf_pb} pb s/REM a 1 año)"
        )
    elif tasa_real_exante > 0.2:
        diag_tasa = (
            f"esto combinado con una tasa real ex-ante positiva de <b>+{_fmt_dec(tasa_real_exante)}% mensual</b>, "
            f"sostiene la demanda de saldos monetarios reales mitigando el traspaso hacia moneda extranjera"
        )
    else:
        diag_tasa = (
            f"lo que, ante una tasa real ex-ante neutral/acotada de <b>{_fmt_dec(tasa_real_exante, signo=True)}% mensual</b>, "
            f"eleva la sensibilidad de los portafolios a la rotación hacia instrumentos indexados o dolarizados"
        )

    if brecha_ccl <= 6.0:
        diag_fx = (
            f"En el frente cambiario, una brecha contenida en <b>{_fmt_dec(brecha_ccl)}%</b> (CCL en <b>${_fmt_dinero(ccl, 2)}</b>) "
            f"y una curva forward CIP a 30d en <b>${_fmt_dinero(cip_30d, 2)}</b> ({_fmt_dec(cip_tna)}% TNA) señalan estabilidad cambiaria "
            f"y descartan presiones devaluatorias de corto plazo"
        )
    elif brecha_ccl <= 15.0:
        diag_fx = (
            f"En el plano externo, la brecha cambiaria en <b>{_fmt_dec(brecha_ccl)}%</b> (CCL ${_fmt_dinero(ccl, 2)}) opera dentro de márgenes "
            f"administrables por el esquema de crawling peg e intervención en futuros"
        )
    else:
        diag_fx = (
            f"En el mercado de cambios, la ampliación de la brecha al <b>{_fmt_dec(brecha_ccl)}%</b> activa alertas tácticas sobre la acumulación "
            f"de reservas netas del BCRA e incentiva coberturas sintéticas"
        )

    if embi <= 550 and beta0 <= 10.0:
        diag_soberano = (
            f"esto sumado a la compresión del riesgo país a <b>{embi} pb</b> y una tasa asintótica Nelson-Siegel de <b>{_fmt_dec(beta0)}%</b>, "
            f"valida la normalización de la curva soberana hard dollar y habilita ganancias de capital sustanciales por compresión de spreads "
            f"y efecto convexidad en los tramos medios y largos (GD35/GD38)"
        )
    elif embi <= 800:
        diag_soberano = (
            f"esto complementado con un riesgo país en <b>{embi} pb</b>, refleja una revalorización del crédito soberano con potencial "
            f"de compresión condicionado a la consolidación del superávit fiscal"
        )
    else:
        diag_soberano = (
            f"mientras un riesgo país elevado en <b>{embi} pb</b> exige mantener sesgo defensivo con foco exclusivo en instrumentos colateralizados"
        )

    if emae_ia >= 2.0:
        diag_actividad = (
            f"En la economía real, el crecimiento del EMAE (<b>+{_fmt_dec(emae_ia)}% i.a.</b> y <b>+{_fmt_dec(emae_mom)}% m/m</b>) "
            f"traccionado por la región Cuyo (Mendoza <b>+{_fmt_dec(isarc_mdz)}%</b>, San Luis <b>+{_fmt_dec(isarc_sl)}%</b>) "
            f"ratifica la recuperación cíclica en un régimen de absorción sistémica del <b>{_fmt_dec(ar_val)}%</b> y turbulencia "
            f"financiera contenida de <b>{_fmt_dec(turb_val, dec=2)}</b> (régimen <b>{regimen}</b>)"
        )
    elif emae_ia >= 0.0:
        diag_actividad = (
            f"En el sector real, el EMAE (<b>+{_fmt_dec(emae_ia)}% i.a.</b>) muestra estabilización en el nivel de actividad, "
            f"operando bajo régimen de turbulencia <b>{regimen}</b> ({_fmt_dec(turb_val, dec=2)} vs. umbral 11,07)"
        )
    else:
        diag_actividad = (
            f"En el ciclo de actividad, la contracción del EMAE (<b>{_fmt_dec(emae_ia)}% i.a.</b>) refleja el costo transitorio "
            f"del reordenamiento de precios relativos"
        )

    tesis_prosa_completa = f"{diag_inflacion}; {diag_tasa}. {diag_fx}; {diag_soberano}. {diag_actividad}."

    # 3. Asignación Táctica Algorítmica
    if tasa_real_exante >= 0.7 and embi <= 600 and brecha_ccl <= 8.0:
        w_lecap, w_global, w_boncer, w_bopreal, w_equity = 40, 30, 15, 10, 5
        r_lecap = "carry trade a tasa fija en TEM 3,0% con tasa real contractiva"
        r_global = "GD35/GD38 por compresión de riesgo país hacia 450 pb y convexidad favorable"
        r_boncer = "TZX27 como cobertura simétrica ante desvíos de breakeven"
        r_bopreal = "Bopreal Serie 3 para flujo corriente en USD"
        r_equity = "Renta Variable energética (YPFD/PAMP) con múltiplos EV/EBITDA < 4,5x"
    elif tasa_real_exante >= 0.4 and embi <= 800:
        w_lecap, w_global, w_boncer, w_bopreal, w_equity = 35, 25, 20, 10, 10
        r_lecap = "tramo corto Lecap para preservación de capital real"
        r_global = "Globales medios GD30/GD35 por rendimiento corriente en USD"
        r_boncer = "cobertura CER indexada"
        r_bopreal = "Bopreal para cobertura cambiaria"
        r_equity = "acciones líderes del Merval"
    elif brecha_ccl > 12.0 or tasa_real_exante < 0.2:
        w_lecap, w_global, w_boncer, w_bopreal, w_equity = 15, 45, 25, 15, 0
        r_lecap = "Lecaps ultra-cortas por liquidez inmediata"
        r_global = "Globales USD en tramo corto para cobertura patrimonial"
        r_boncer = "Boncer CER para preservación del poder adquisitivo"
        r_bopreal = "Bopreales en USD"
        r_equity = "sin exposición táctica en renta variable por volatilidad sistémica"
    else:
        w_lecap, w_global, w_boncer, w_bopreal, w_equity = 25, 35, 25, 15, 0
        r_lecap = "Lecap corta de alta liquidez"
        r_global = "deuda soberana en moneda dura"
        r_boncer = "indexación CER"
        r_bopreal = "flujo en dólares"
        r_equity = "neutral"

    asig_prosa_completa = (
        f"<b>Asignación Táctica Ponderada:</b> <b>{w_lecap}% en Lecaps cortas</b> ({r_lecap}), "
        f"<b>{w_global}% en Globales USD</b> ({r_global}), "
        f"<b>{w_boncer}% en Boncer</b> ({r_boncer}), "
        f"<b>{w_bopreal}% en Bopreal</b> ({r_bopreal})"
    )
    if w_equity > 0:
        asig_prosa_completa += f" y <b>{w_equity}% en Renta Variable</b> ({r_equity})."
    else:
        asig_prosa_completa += "."

    return {
        "tesis_prosa": tesis_prosa_completa,
        "asig_prosa": asig_prosa_completa,
        "pesos": {"lecap": w_lecap, "globales": w_global, "boncer": w_boncer, "bopreal": w_bopreal, "equity": w_equity}
    }
