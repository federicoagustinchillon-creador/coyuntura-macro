"""
PIPELINE MAESTRO DE AUTOMATIZACIÓN INTEGRAL DE COYUNTURA MACROECONÓMICA
=======================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — UNCUYO / OERU

Orquesta la ejecución desatendida del ecosistema macro-financiero institucional:
1. Validación de bases de datos macroeconómicas y financieras (Excel).
2. Generación de figuras estadísticas vectoriales en alta resolución (300 DPI) con paleta Oxford Navy / Deep Wine.
3. Nivel 1: Monitor Diario de Mercados & Coyuntura (Flash 2 Páginas).
4. Nivel 2: Paper Semanal de Investigación Macroeconómica (APA 7 - 4 Páginas).
5. Nivel 3: Informe Mensual Master de Coyuntura Macroeconómica y Regional (OERU - 15 Páginas con TOC dinámico).
6. Exportación a PDF vía Microsoft Word COM Automation con actualización de campos dinámicos.
7. Consolidación de entregables ejecutivos en 07_Reportes_Ejecutivos_PDF.
"""

import os
import sys
import shutil
import subprocess
import pythoncom
import win32com.client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from datetime import datetime

from src.sync_datos_del_dia import sincronizar_todo
from src.fetch_tcr_bilateral import guardar_cache as guardar_cache_tcr
from src.actualizador_datos import construir_base_datos_macro
from src.generador_graficos_hd import generar_todas_las_infografias
from src.generador_informe_diario import compilar_informe_diario
from src.generador_paper_semanal import compilar_paper_semanal_completo
from src.generador_informe_mensual_master import construir_informe_mensual_master_docx
from src.generador_informe_diario_reportlab import generar_monitor_diario_reportlab
from src.generador_paper_semanal_reportlab import generar_paper_semanal_reportlab
from src.generador_informe_mensual_reportlab import generar_informe_mensual_reportlab
from src.contexto_informe import cargar_contexto

def limpiar_archivos_temporales(base_dir):
    """Elimina previews, locks y archivos temporales para mantener la máxima higiene."""
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.startswith('~$'):
                try: os.remove(os.path.join(root, f))
                except: pass


def exportar_lote_docx_a_pdf(pares_docx_pdf):
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx('Word.Application')
    word.Visible = False
    word.DisplayAlerts = 0
    try:
        for ruta_docx, ruta_pdf in pares_docx_pdf:
            if os.path.exists(ruta_docx):
                doc_w = word.Documents.Open(os.path.abspath(ruta_docx), ReadOnly=False)
                try:
                    doc_w.Fields.Update()
                    for toc in doc_w.TablesOfContents:
                        toc.Update()
                except Exception as e_toc:
                    pass
                doc_w.SaveAs(os.path.abspath(ruta_pdf), FileFormat=17) # 17 = wdFormatPDF
                doc_w.Close(SaveChanges=True)
                print(f"      [OK] PDF exportado: {os.path.basename(ruta_pdf)}")
    finally:
        word.Quit()
        pythoncom.CoUninitialize()


def ejecutar_pipeline_coyuntura_completo():
    print("=================================================================")
    print("INICIANDO PIPELINE MAESTRO DE COYUNTURA MACROECONÓMICA Y FINANZAS")
    print("=================================================================")
    
    limpiar_archivos_temporales(BASE_DIR)
    
    dir_bd = os.path.join(BASE_DIR, "01_Bases_Datos")
    dir_fig = os.path.join(BASE_DIR, "03_Figuras_HD")
    dir_dia = os.path.join(BASE_DIR, "04_Informes_Diarios")
    dir_sem = os.path.join(BASE_DIR, "05_Informes_Semanales_APA7")
    dir_men = os.path.join(BASE_DIR, "06_Informes_Mensuales_OERU")
    dir_eje = os.path.join(BASE_DIR, "07_Reportes_Ejecutivos_PDF")
    
    for d in [dir_bd, dir_fig, dir_dia, dir_sem, dir_men, dir_eje]:
        os.makedirs(d, exist_ok=True)
        
    ruta_excel = os.path.join(dir_bd, "Base_Datos_Macro_Financiera.xlsx")

    # 0. Sincronizacion de feeds en vivo: registro macro interno + BCRA/yfinance de respaldo
    print("\n[0/5] Sincronizando feeds en vivo...")
    sincronizar_todo()

    # 0.b Tipo de cambio real bilateral (atraso/competitividad cambiaria):
    # 3 fuentes externas (BCRA, INDEC, BLS) con paginacion -- se cachea una
    # vez por corrida, no en cada poll del dashboard. Envuelto en try/except:
    # si alguna API externa esta caida, no debe tumbar el pipeline entero;
    # el informe usa el ultimo cache valido en vez de fallar.
    print("\n[0.b/5] Recalculando Tipo de Cambio Real bilateral (BCRA + INDEC + BLS)...")
    try:
        tcr_resultado = guardar_cache_tcr()
        print(f"      -> TCR bilateral actualizado: {tcr_resultado['ultimo']}")
    except Exception as e_tcr:
        print(f"      [TCR Error] No se pudo actualizar (se usa el ultimo cache disponible): {e_tcr}")

    # 0.c Fecha de referencia unica para los nombres de archivo de este ciclo:
    # se lee de datos_del_dia.json (misma fuente que ya usan internamente
    # compilar_informe_diario/compilar_paper_semanal_completo para el texto
    # de fecha del cuerpo) en vez de un literal fijo -- antes este script
    # hardcodeaba "2026-08-21" en el nombre de archivo Y en el fecha_str/
    # periodo_str pasados a los generadores, asi que cada corrida
    # sobreescribia siempre el mismo PDF del 21-ago en vez de crear el
    # entregable del dia real, y 07_Reportes_Ejecutivos_PDF quedaba
    # desactualizado apenas pasaba un dia. Si el JSON no tiene "fecha"
    # (corrida en un repo recien clonado sin sincronizar), se cae a la
    # fecha de hoy como ultimo recurso, nunca a un valor de ejemplo.
    fecha_ciclo = cargar_contexto(incluir_series_lentas=False).get("fecha") or datetime.now().strftime("%Y-%m-%d")
    print(f"\n[0.c/5] Fecha de referencia del ciclo (datos_del_dia.json): {fecha_ciclo}")

    # 1. Base de Datos
    print("\n[1/5] Consolidando Base de Datos Macro-Financiera...")
    construir_base_datos_macro(ruta_excel)
    print("      -> Base Excel actualizada:", ruta_excel)
    
    # 2. Infografías Vectoriales en 300 DPI
    print("\n[2/5] Generando Infografías Vectoriales en 300 DPI con Estándar Institucional...")
    figs = generar_todas_las_infografias()
    for f in figs:
        print("      -> Infografía creada:", os.path.basename(f))
        
    # 3. Compilación de Documentos (3 Niveles - Suite ReportLab Tier-1)
    print("\n[3/5] Compilando Documentos Institucionales ReportLab (3 Niveles)...")
    
    # Nivel 1: Diario (2 Páginas ReportLab)
    pdf_dia = generar_monitor_diario_reportlab()
    print("      -> [Nivel 1] Monitor Diario PDF (2 págs ReportLab):", pdf_dia)

    # Nivel 2: Semanal (4 Páginas APA 7 ReportLab)
    pdf_sem = generar_paper_semanal_reportlab()
    print("      -> [Nivel 2] Paper Semanal PDF (4 págs APA 7 ReportLab):", pdf_sem)
    
    # Nivel 3: Mensual Master (15 Páginas ReportLab)
    pdf_men = generar_informe_mensual_reportlab()
    print("      -> [Nivel 3] Informe Mensual Master PDF (15 págs ReportLab):", pdf_men)
    
    # 4. Compilación Complementaria de Archivos DOCX
    print("\n[4/5] Compilando Versiones DOCX Complementarias para Archivo...")
    docx_dia = os.path.join(dir_dia, f"{fecha_ciclo}_Monitor_Diario_Mercados.docx")
    docx_sem = os.path.join(dir_sem, f"{fecha_ciclo}_Paper_Macroeconomico_Semanal.docx")
    docx_men = os.path.join(dir_men, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.docx")
    try:
        compilar_informe_diario(docx_dia)
        compilar_paper_semanal_completo(docx_sem)
        construir_informe_mensual_master_docx(docx_men)
        print("      -> Versiones DOCX compiladas exitosamente.")
    except Exception as e_docx:
        print(f"      [Aviso DOCX] {e_docx}")
    
    # Consolidación de copias ejecutivas ReportLab en 07_Reportes_Ejecutivos_PDF
    shutil.copy2(pdf_dia, os.path.join(dir_eje, os.path.basename(pdf_dia)))
    shutil.copy2(pdf_sem, os.path.join(dir_eje, os.path.basename(pdf_sem)))
    shutil.copy2(pdf_men, os.path.join(dir_eje, os.path.basename(pdf_men)))
    
    # 5. Sincronización Automática con Google Drive (C: y G:)
    print("\n[5/5] Sincronizando Ecosistema Oficial con Google Drive (C: y G:)...")
    sincronizar_con_google_drive(BASE_DIR, fecha_ciclo)

    limpiar_archivos_temporales(BASE_DIR)

    print("\n=================================================================")
    print("PIPELINE EJECUTADO EXITOSAMENTE. ECOSISTEMA HIGIÉNICO Y ACTUALIZADO.")
    print("=================================================================")

def sincronizar_con_google_drive(base_dir, fecha_ciclo):
    """Sincroniza el ecosistema hacia C:\\Users\\fedea\\Google Drive\\coyuntura-macro
    y G:\\Mi unidad\\Federico_Chillon_Master\\01_Coyuntura_Macro_y_Mercados,
    erradicando plantillas viejas, graficos antiguos y archivos de conflicto."""
    gdrive_c = r"C:\Users\fedea\Google Drive\coyuntura-macro"
    gdrive_g = r"G:\Mi unidad\Federico_Chillon_Master\01_Coyuntura_Macro_y_Mercados"

    # Git commit y push local
    def _git(args, cwd, check=True):
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
        if check and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} fallo:\n{r.stdout}\n{r.stderr}")
        return r

    try:
        status = _git(["status", "--porcelain"], base_dir, check=False).stdout
        if status.strip():
            _git(["add", "-A"], base_dir, check=False)
            msg = f"chore(pipeline): ciclo {fecha_ciclo} (suite reportlab 3 niveles + figuras hd)"
            _git(["commit", "-m", msg], base_dir, check=False)
            _git(["push", "origin", "HEAD"], base_dir, check=False)
            print("      [Git OK] Commit y push local completados.")
    except Exception as e_git:
        print(f"      [Git Aviso] {e_git}")

    # Sincronizar C:
    if os.path.exists(gdrive_c):
        try:
            # Limpiar conflictos
            for root, dirs, files in os.walk(gdrive_c):
                for f in files:
                    if " (1)." in f or " (2)." in f:
                        try: os.remove(os.path.join(root, f))
                        except: pass
            # Espejar carpetas críticas
            for sub in ["src", "03_Figuras_HD", "04_Informes_Diarios", "05_Informes_Semanales_APA7", "06_Informes_Mensuales_OERU", "07_Reportes_Ejecutivos_PDF"]:
                s_orig = os.path.join(base_dir, sub)
                s_dest = os.path.join(gdrive_c, sub)
                if os.path.exists(s_orig):
                    os.makedirs(s_dest, exist_ok=True)
                    for item in os.listdir(s_orig):
                        p_item = os.path.join(s_orig, item)
                        if os.path.isfile(p_item):
                            shutil.copy2(p_item, os.path.join(s_dest, item))
            shutil.copy2(os.path.join(base_dir, "pipeline_coyuntura_master.py"), os.path.join(gdrive_c, "pipeline_coyuntura_master.py"))
            print("      [Drive C OK] Espejado 1:1 completado en Drive C.")
        except Exception as e_c:
            print(f"      [Drive C Aviso] {e_c}")

    # Sincronizar G:
    if os.path.exists(gdrive_g):
        try:
            # Limpiar conflictos
            for root, dirs, files in os.walk(gdrive_g):
                for f in files:
                    if " (1)." in f or " (2)." in f:
                        try: os.remove(os.path.join(root, f))
                        except: pass
            # Scripts y Pipelines
            scripts_g = os.path.join(gdrive_g, "Scripts_y_Pipelines")
            os.makedirs(scripts_g, exist_ok=True)
            src_dir = os.path.join(base_dir, "src")
            for f in os.listdir(src_dir):
                if f.endswith(".py") or f.endswith(".json"):
                    shutil.copy2(os.path.join(src_dir, f), os.path.join(scripts_g, f))
            shutil.copy2(os.path.join(base_dir, "pipeline_coyuntura_master.py"), os.path.join(scripts_g, "pipeline_coyuntura_master.py"))

            # Figuras HD
            for f_dir in ["Figuras_HD", "03_Figuras_HD"]:
                dest_f = os.path.join(gdrive_g, f_dir)
                os.makedirs(dest_f, exist_ok=True)
                orig_f = os.path.join(base_dir, "03_Figuras_HD")
                for f in os.listdir(orig_f):
                    p_orig = os.path.join(orig_f, f)
                    if os.path.isfile(p_orig):
                        shutil.copy2(p_orig, os.path.join(dest_f, f))
                # subcarpeta master_extracted_images
                dest_sub = os.path.join(dest_f, "master_extracted_images")
                os.makedirs(dest_sub, exist_ok=True)
                orig_sub = os.path.join(orig_f, "master_extracted_images")
                if os.path.exists(orig_sub):
                    for f in os.listdir(orig_sub):
                        p_sub = os.path.join(orig_sub, f)
                        if os.path.isfile(p_sub):
                            shutil.copy2(p_sub, os.path.join(dest_sub, f))

            # PDFs
            p_dia = os.path.join(base_dir, "04_Informes_Diarios", f"{fecha_ciclo}_Monitor_Diario_Mercados.pdf")
            p_sem = os.path.join(base_dir, "05_Informes_Semanales_APA7", f"{fecha_ciclo}_Paper_Macroeconomico_Semanal.pdf")
            p_men = os.path.join(base_dir, "06_Informes_Mensuales_OERU", "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.pdf")

            if os.path.exists(p_dia):
                for d in ["Monitores_Diarios", "04_Informes_Diarios"]:
                    os.makedirs(os.path.join(gdrive_g, d), exist_ok=True)
                    shutil.copy2(p_dia, os.path.join(gdrive_g, d, os.path.basename(p_dia)))
                shutil.copy2(p_dia, os.path.join(gdrive_g, "2026-08-31_Monitor_Diario_Mercados.pdf"))

            if os.path.exists(p_sem):
                for d in ["Papers_Semanales", "05_Informes_Semanales_APA7"]:
                    os.makedirs(os.path.join(gdrive_g, d), exist_ok=True)
                    shutil.copy2(p_sem, os.path.join(gdrive_g, d, os.path.basename(p_sem)))
                shutil.copy2(p_sem, os.path.join(gdrive_g, "2026-08-28_Paper_Macroeconomico_Semanal.pdf"))

            if os.path.exists(p_men):
                for d in ["Informes_Mensuales", "06_Informes_Mensuales_OERU"]:
                    os.makedirs(os.path.join(gdrive_g, d), exist_ok=True)
                    shutil.copy2(p_men, os.path.join(gdrive_g, d, os.path.basename(p_men)))

            eje_g = os.path.join(gdrive_g, "07_Reportes_Ejecutivos_PDF")
            os.makedirs(eje_g, exist_ok=True)
            for p in [p_dia, p_sem, p_men]:
                if os.path.exists(p):
                    shutil.copy2(p, os.path.join(eje_g, os.path.basename(p)))
            print("      [Drive G OK] Entregables y scripts sincronizados en Drive G.")
        except Exception as e_g:
            print(f"      [Drive G Aviso] {e_g}")

if __name__ == "__main__":
    ejecutar_pipeline_coyuntura_completo()
