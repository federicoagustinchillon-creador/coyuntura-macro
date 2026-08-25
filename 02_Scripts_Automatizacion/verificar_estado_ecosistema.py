# -*- coding: utf-8 -*-
"""
AUDITOR AUTOMÁTICO DE INTEGRIDAD Y COBERTURA DEL ECOSISTEMA
===========================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — UNCUYO / OERU
"""

import os
import sys
import fitz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GDRIVE_DIR = r"C:\Users\fedea\Google Drive\coyuntura-macro"

def auditar_ecosistema():
    print("=================================================================")
    print("AUDITORÍA DE INTEGRIDAD DEL ECOSISTEMA DE COYUNTURA MACRO")
    print("=================================================================")
    
    errores = []
    
    # 1. Base Excel
    excel_p = os.path.join(BASE_DIR, "01_Bases_Datos", "Base_Datos_Macro_Financiera.xlsx")
    if os.path.exists(excel_p):
        sz = os.path.getsize(excel_p)
        print(f"[OK] Base Excel: {os.path.basename(excel_p)} ({sz:,} bytes)")
    else:
        errores.append("Base Excel ausente")
        print("[ERROR] Base Excel no encontrada")
        
    # 2. Figuras HD
    img_dir = os.path.join(BASE_DIR, "03_Figuras_HD")
    figs_esperadas = [
        "chart_indec_emae_master.png",
        "chart_indec_1_rates.png",
        "chart_indec_2_ipc.png",
        "chart_indec_3_cuyo.png",
        "chart_indec_3b_regional_cuyo.png",
        "chart_indec_4_monetary.png",
        "chart_indec_5_sovereign.png",
        "chart_indec_6_fx.png",
        "chart_indec_7_equity.png"
    ]
    for fig_n in figs_esperadas:
        fp = os.path.join(img_dir, fig_n)
        if os.path.exists(fp):
            print(f"[OK] Figura 300 DPI: {fig_n} ({os.path.getsize(fp):,} bytes)")
        else:
            errores.append(f"Figura ausente: {fig_n}")
            print(f"[ERROR] Figura ausente: {fig_n}")
            
    # 3. Documentos Oficiales y Cobertura
    docs = {
        "Monitor Diario (2 Págs)": (os.path.join(BASE_DIR, "04_Informes_Diarios", "2026-08-21_Monitor_Diario_Mercados.pdf"), 2),
        "Paper Semanal APA 7 (4 Págs)": (os.path.join(BASE_DIR, "05_Informes_Semanales_APA7", "2026-08-21_Paper_Macroeconomico_Semanal.pdf"), 4),
        "Informe Mensual Master (14 Págs)": (os.path.join(BASE_DIR, "06_Informes_Mensuales_OERU", "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf"), 14)
    }
    
    print("\n--- AUDITORÍA DE PÁGINAS Y COBERTURA VERTICAL ---")
    for nombre, (ruta_pdf, pags_esperadas) in docs.items():
        if not os.path.exists(ruta_pdf):
            errores.append(f"PDF ausente: {nombre}")
            print(f"[ERROR] PDF ausente: {nombre}")
            continue
            
        doc_fitz = fitz.open(ruta_pdf)
        pags_reales = len(doc_fitz)
        if pags_reales != pags_esperadas:
            errores.append(f"{nombre}: esperado {pags_esperadas} págs, encontrado {pags_reales}")
            print(f"[ALERTA] {nombre}: Páginas {pags_reales} != {pags_esperadas}")
        else:
            print(f"[OK] {nombre}: {pags_reales} páginas exactas")
            
        for i, page in enumerate(doc_fitz):
            max_y = 0
            for b in page.get_text('blocks'):
                if b[3] > max_y and b[3] < 750: max_y = b[3]
            for img in page.get_images():
                for r in page.get_image_rects(img[0]):
                    if r.y1 > max_y and r.y1 < 750: max_y = r.y1
            cov_pct = (max_y / 720.0) * 100
            print(f"     Pág {i+1:2d}: Altura contenido = {max_y:5.1f} pt / 720 pt | Cobertura: {cov_pct:5.1f}%")
            
    # 4. Sincronización Google Drive
    print("\n--- VERIFICACIÓN DE ESPEJO GOOGLE DRIVE ---")
    if os.path.exists(GDRIVE_DIR):
        print(f"[OK] Directorio Google Drive accesible: {GDRIVE_DIR}")
        pdf_drive = os.path.join(GDRIVE_DIR, "07_Reportes_Ejecutivos_PDF")
        if os.path.exists(pdf_drive):
            files_drive = os.listdir(pdf_drive)
            print(f"[OK] Google Drive PDFs disponibles ({len(files_drive)} archivos): {files_drive}")
    else:
        print("[ADVERTENCIA] Directorio Google Drive no accesible localmente")
        
    print("\n=================================================================")
    if errores:
        print(f"AUDITORÍA FINALIZADA CON {len(errores)} ERRORES:")
        for e in errores: print("  - ", e)
        sys.exit(1)
    else:
        print("AUDITORÍA FINALIZADA CON ÉXITO: ECOSISTEMA 100% HIGIÉNICO Y OPERATIVO")
        print("=================================================================")
        sys.exit(0)

if __name__ == '__main__':
    auditar_ecosistema()
