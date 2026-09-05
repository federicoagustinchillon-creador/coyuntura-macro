"""
================================================================================
PIPELINE MAESTRO DE COMPILACIÓN EDITORIAL (REPORTLAB MASTER SUITE)
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo
Compila los 3 entregables institucionales con el estándar visual de Goldman Sachs GIR:
1. Monitor Diario de Mercados Financieros (2 Páginas Exactas)
2. Paper Macroeconómico Semanal APA 7 (4 Páginas Exactas)
3. Informe Mensual de Coyuntura Macroeconómica & Regional (14 Páginas Exactas)
================================================================================
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

from generador_informe_diario_reportlab import generar_monitor_diario_reportlab
from generador_paper_semanal_reportlab import generar_paper_semanal_reportlab
from generador_informe_mensual_reportlab import generar_informe_mensual_reportlab
from generador_graficos_echarts import generar_todos_los_graficos_echarts

def ejecutar_compilacion_maestra():
    print("=================================================================")
    print("COMPILANDO LA SUITE MAESTRA DE INFORMES REPORTLAB (TIER-1)")
    print("=================================================================")
    
    print("\n[0/3] Compilando Suite de Figuras ECharts 5 Headless (Tier-1)...")
    generar_todos_los_graficos_echarts()
    
    print("\n[1/3] Generando Monitor Diario (2 Páginas Exactas)...")
    p_diario = generar_monitor_diario_reportlab()
    print(f"      [OK] Generado: {p_diario}")
    
    print("\n[2/3] Generando Paper Semanal APA 7 (4 Páginas Exactas)...")
    p_semanal = generar_paper_semanal_reportlab()
    print(f"      [OK] Generado: {p_semanal}")
    
    print("\n[3/3] Generando Informe Mensual Master (15 Páginas Exactas)...")
    p_mensual = generar_informe_mensual_reportlab()
    print(f"      [OK] Generado: {p_mensual}")
    
    print("\n=================================================================")
    print("LOS 3 ENTREGABLES FUERON COMPILADOS EXITOSAMENTE CON REPORTLAB")
    print("=================================================================")
    return p_diario, p_semanal, p_mensual

if __name__ == "__main__":
    ejecutar_compilacion_maestra()
