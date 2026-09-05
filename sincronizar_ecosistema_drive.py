# -*- coding: utf-8 -*-
"""
================================================================================
SINCRONIZADOR INTEGRAL DEL ECOSISTEMA MACRO A GOOGLE DRIVE (C: Y G:)
================================================================================
Autor: Federico Agustín Chillón
Afiliación: Facultad de Ciencias Económicas — Universidad Nacional de Cuyo (UNCUYO)
================================================================================
"""

import os
import shutil

def sincronizar_drive():
    src_root = r"C:\Users\fedea\Downloads\coyuntura-macro"
    dst_c = r"C:\Users\fedea\Google Drive\coyuntura-macro"
    dst_g = r"G:\Mi unidad\Federico_Chillon_Master\01_Coyuntura_Macro_y_Mercados"

    dirs_to_sync = [
        "src",
        "03_Figuras_HD",
        "04_Informes_Diarios",
        "05_Informes_Semanales_APA7",
        "06_Informes_Mensuales",
        "07_Reportes_Ejecutivos_PDF",
        "01_Bases_Datos"
    ]

    # 1. Sincronización en Drive C
    if os.path.exists(os.path.dirname(dst_c)):
        os.makedirs(dst_c, exist_ok=True)
        files_c = 0
        bytes_c = 0
        for d in dirs_to_sync:
            src_dir = os.path.join(src_root, d)
            if not os.path.exists(src_dir):
                continue
            for root, dirs, files in os.walk(src_dir):
                if "__pycache__" in root or ".git" in root:
                    continue
                rel = os.path.relpath(root, src_root)
                target_dir = os.path.join(dst_c, rel)
                os.makedirs(target_dir, exist_ok=True)
                for f in files:
                    s_file = os.path.join(root, f)
                    d_file = os.path.join(target_dir, f)
                    if not os.path.exists(d_file) or os.path.getmtime(s_file) > os.path.getmtime(d_file) or os.path.getsize(s_file) != os.path.getsize(d_file):
                        shutil.copy2(s_file, d_file)
                        files_c += 1
                        bytes_c += os.path.getsize(s_file)
        shutil.copy2(os.path.join(src_root, "pipeline_coyuntura_master.py"), os.path.join(dst_c, "pipeline_coyuntura_master.py"))
        shutil.copy2(os.path.join(src_root, "README.md"), os.path.join(dst_c, "README.md"))
        print(f"[Drive C OK] Sincronización completada: {files_c} archivos actualizados ({bytes_c / (1024*1024):.2f} MB)")

    # 2. Sincronización en Drive G
    if os.path.exists(dst_g):
        # Scripts
        scripts_g = os.path.join(dst_g, "Scripts_y_Pipelines")
        os.makedirs(scripts_g, exist_ok=True)
        src_dir = os.path.join(src_root, "src")
        for f in os.listdir(src_dir):
            if f.endswith(".py") or f.endswith(".json"):
                shutil.copy2(os.path.join(src_dir, f), os.path.join(scripts_g, f))
        shutil.copy2(os.path.join(src_root, "pipeline_coyuntura_master.py"), os.path.join(scripts_g, "pipeline_coyuntura_master.py"))
        shutil.copy2(os.path.join(src_root, "README.md"), os.path.join(scripts_g, "README.md"))

        # Figuras HD
        for f_dir in ["Figuras_HD", "03_Figuras_HD"]:
            dest_f = os.path.join(dst_g, f_dir)
            os.makedirs(dest_f, exist_ok=True)
            orig_f = os.path.join(src_root, "03_Figuras_HD")
            for f in os.listdir(orig_f):
                p_orig = os.path.join(orig_f, f)
                if os.path.isfile(p_orig):
                    shutil.copy2(p_orig, os.path.join(dest_f, f))
            dest_sub = os.path.join(dest_f, "editorial_compact")
            os.makedirs(dest_sub, exist_ok=True)
            orig_sub = os.path.join(orig_f, "editorial_compact")
            if os.path.exists(orig_sub):
                for f in os.listdir(orig_sub):
                    p_sub = os.path.join(orig_sub, f)
                    if os.path.isfile(p_sub):
                        shutil.copy2(p_sub, os.path.join(dest_sub, f))

        # PDFs
        p_dia = os.path.join(src_root, "04_Informes_Diarios", "2026-08-25_Monitor_Diario_Mercados.pdf")
        p_sem = os.path.join(src_root, "05_Informes_Semanales_APA7", "2026-08-25_Paper_Macroeconomico_Semanal.pdf")
        p_men = os.path.join(src_root, "06_Informes_Mensuales", "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")

        for d in ["Monitores_Diarios", "04_Informes_Diarios"]:
            os.makedirs(os.path.join(dst_g, d), exist_ok=True)
            shutil.copy2(p_dia, os.path.join(dst_g, d, os.path.basename(p_dia)))

        for d in ["Papers_Semanales", "05_Informes_Semanales_APA7"]:
            os.makedirs(os.path.join(dst_g, d), exist_ok=True)
            shutil.copy2(p_sem, os.path.join(dst_g, d, os.path.basename(p_sem)))

        for d in ["Informes_Mensuales", "06_Informes_Mensuales"]:
            os.makedirs(os.path.join(dst_g, d), exist_ok=True)
            shutil.copy2(p_men, os.path.join(dst_g, d, os.path.basename(p_men)))

        p_ape = os.path.join(src_root, "07_Reportes_Ejecutivos_PDF", "Apendice_Econometrico_y_Validacion_Modelos_Agosto_2026.pdf")

        eje_g = os.path.join(dst_g, "07_Reportes_Ejecutivos_PDF")
        os.makedirs(eje_g, exist_ok=True)
        for p in [p_dia, p_sem, p_men, p_ape]:
            if os.path.exists(p):
                shutil.copy2(p, os.path.join(eje_g, os.path.basename(p)))

        print("[Drive G OK] Sincronización completada en G:\\Mi unidad.")

if __name__ == "__main__":
    sincronizar_drive()
