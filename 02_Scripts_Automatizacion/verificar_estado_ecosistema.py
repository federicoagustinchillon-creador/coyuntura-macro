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
    # Antes esta lista apuntaba a nombres de archivo fijos con fecha
    # hardcodeada ("2026-08-21_..."), asi que el dia que el pipeline
    # generaba el entregable del dia siguiente, este auditor seguia
    # revisando (y dando OK sobre) el PDF viejo sin darse cuenta de que
    # habia uno mas nuevo sin auditar. Se busca el PDF mas reciente por
    # fecha de modificacion en cada carpeta en vez de un nombre fijo.
    def _pdf_mas_reciente(carpeta):
        d = os.path.join(BASE_DIR, carpeta)
        if not os.path.isdir(d):
            return None
        candidatos = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(".pdf")]
        return max(candidatos, key=os.path.getmtime) if candidatos else None

    docs = {
        "Monitor Diario (2 Págs)": (_pdf_mas_reciente("04_Informes_Diarios"), 2),
        "Paper Semanal APA 7 (4 Págs)": (_pdf_mas_reciente("05_Informes_Semanales_APA7"), 4),
        # 15 paginas reales, no 14: la Seccion 7 (Microestructura Cambiaria)
        # ocupa 2 paginas fisicas (cuerpo + tabla de futuros CIP) desde
        # antes de esta auditoria; el "14" historico nunca reflejo eso.
        "Informe Mensual Master (15 Págs)": (os.path.join(BASE_DIR, "06_Informes_Mensuales_OERU", "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf"), 15)
    }
    
    print("\n--- AUDITORÍA DE PÁGINAS Y COBERTURA VERTICAL ---")
    for nombre, (ruta_pdf, pags_esperadas) in docs.items():
        if not ruta_pdf or not os.path.exists(ruta_pdf):
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
    # Antes esto solo confirmaba que la carpeta existia y contaba archivos
    # en 07_Reportes_Ejecutivos_PDF -- eso da falsos "OK" cuando el espejo
    # tiene la cantidad correcta de archivos pero con contenido VIEJO (el
    # caso real encontrado: los PDFs de 07 en Drive coincidian en cantidad
    # pero eran de una corrida anterior). Se compara por hash SHA-256
    # archivo por archivo contra el repo principal en las carpetas de
    # entregables reales, y se reporta cualquier carpeta huerfana sin
    # trackear en git (residuos de limpiezas incompletas).
    print("\n--- VERIFICACIÓN DE ESPEJO GOOGLE DRIVE ---")
    if not os.path.isdir(GDRIVE_DIR):
        print("[ADVERTENCIA] Directorio Google Drive no accesible localmente")
        errores.append("Espejo de Google Drive no accesible")
    else:
        print(f"[OK] Directorio Google Drive accesible: {GDRIVE_DIR}")
        import hashlib
        import subprocess as _sp

        def _sha(p):
            h = hashlib.sha256()
            with open(p, "rb") as fh:
                h.update(fh.read())
            return h.hexdigest()

        carpetas_espejo = [
            "01_Bases_Datos", "03_Figuras_HD", "04_Informes_Diarios",
            "05_Informes_Semanales_APA7", "06_Informes_Mensuales_OERU",
            "07_Reportes_Ejecutivos_PDF",
        ]
        divergencias = 0
        for carpeta in carpetas_espejo:
            rdir = os.path.join(BASE_DIR, carpeta)
            ddir = os.path.join(GDRIVE_DIR, carpeta)
            if not os.path.isdir(rdir):
                continue
            for root, dirsub, files in os.walk(rdir):
                if ".git" in dirsub: dirsub.remove(".git")
                for fn in files:
                    rp = os.path.join(root, fn)
                    rel = os.path.relpath(rp, BASE_DIR)
                    dp = os.path.join(GDRIVE_DIR, rel)
                    if not os.path.isfile(dp):
                        divergencias += 1
                        errores.append(f"Drive: falta {rel}")
                        print(f"[ERROR] Drive: falta {rel}")
                    elif _sha(rp) != _sha(dp):
                        divergencias += 1
                        errores.append(f"Drive: contenido distinto en {rel}")
                        print(f"[ERROR] Drive: contenido DISTINTO en {rel} (repo y espejo no coinciden)")
        if divergencias == 0:
            print("[OK] Los entregables del repo y del espejo de Drive coinciden byte a byte.")

        if os.path.isdir(os.path.join(GDRIVE_DIR, ".git")):
            r = _sp.run(["git", "status", "--porcelain", "--ignored"], cwd=GDRIVE_DIR, capture_output=True, text=True)
            huerfanos = [l[3:] for l in r.stdout.splitlines() if l.startswith("??")]
            if huerfanos:
                errores.append(f"Drive: {len(huerfanos)} archivo(s)/carpeta(s) sin trackear (residuo de limpiezas incompletas)")
                print(f"[ALERTA] Drive tiene {len(huerfanos)} entrada(s) sin trackear en git: {huerfanos}")
                print("         -> correr 'git clean -fd' dentro del espejo para eliminarlas.")
            else:
                print("[OK] Espejo de Drive sin residuos sin trackear (git clean -fdn vacio).")

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
