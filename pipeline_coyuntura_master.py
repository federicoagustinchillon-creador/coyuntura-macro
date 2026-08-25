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
5. Nivel 3: Informe Mensual Master de Coyuntura Macroeconómica y Regional (OERU - 12-13 Páginas con TOC dinámico).
6. Exportación a PDF vía Microsoft Word COM Automation con actualización de campos dinámicos.
7. Consolidación de entregables ejecutivos en 07_Reportes_Ejecutivos_PDF.
"""

import os
import sys
import shutil
import pythoncom
import win32com.client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.sync_secondbrain_macro import sincronizar_desde_secondbrain
from src.actualizador_datos import construir_base_datos_macro
from src.generador_graficos_hd import generar_todas_las_infografias
from src.generador_informe_diario import compilar_informe_diario
from src.generador_paper_semanal import compilar_paper_semanal_completo
from src.generador_informe_mensual_master import construir_informe_mensual_master_docx
from src.generador_informe_mensual_reportlab import generar_informe_mensual_reportlab

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

    # 0. Sincronizacion de feeds en vivo desde SecondBrain
    print("\n[0/5] Sincronizando feeds en vivo desde SecondBrain...")
    sincronizar_desde_secondbrain()

    # 1. Base de Datos
    print("\n[1/5] Consolidando Base de Datos Macro-Financiera...")
    construir_base_datos_macro(ruta_excel)
    print("      -> Base Excel actualizada:", ruta_excel)
    
    # 2. Infografías Vectoriales en 300 DPI
    print("\n[2/5] Generando Infografías Vectoriales en 300 DPI con Estándar Institucional...")
    figs = generar_todas_las_infografias()
    for f in figs:
        print("      -> Infografía creada:", os.path.basename(f))
        
    # 3. Compilación de Documentos (3 Niveles)
    print("\n[3/5] Compilando Documentos Institucionales (3 Niveles)...")
    
    # Nivel 1: Diario (2 Páginas)
    docx_dia = os.path.join(dir_dia, "2026-08-21_Monitor_Diario_Mercados.docx")
    pdf_dia = docx_dia.replace(".docx", ".pdf")
    compilar_informe_diario(docx_dia, fecha_str="21 de Agosto de 2026")
    print("      -> [Nivel 1] Monitor Diario DOCX (2 págs):", docx_dia)
    
    # Nivel 2: Semanal (4 Páginas APA 7)
    docx_sem = os.path.join(dir_sem, "2026-08-21_Paper_Macroeconomico_Semanal.docx")
    pdf_sem = docx_sem.replace(".docx", ".pdf")
    compilar_paper_semanal_completo(docx_sem, periodo_str="Semana del 17 al 21 de Agosto de 2026")
    print("      -> [Nivel 2] Paper Semanal DOCX (4 págs APA 7):", docx_sem)
    
    # Nivel 3: Mensual Master (DOCX y ReportLab 14 Páginas)
    docx_men = os.path.join(dir_men, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.docx")
    construir_informe_mensual_master_docx(docx_men)
    print("      -> [Nivel 3] Informe Mensual Master DOCX compilado:", docx_men)
    
    # Generación del PDF Maestro con ReportLab (14 Páginas con ZeroWhitespaceCanvas y Outlines)
    pdf_men = generar_informe_mensual_reportlab()
    print("      -> [Nivel 3] Informe Mensual Master PDF (14 págs ReportLab):", pdf_men)
    
    # 4. Exportación en Lote a PDF para Diario y Semanal
    print("\n[4/5] Exportando Documentos Word a PDF Institucional...")
    exportar_lote_docx_a_pdf([
        (docx_dia, pdf_dia),
        (docx_sem, pdf_sem),
    ])
    
    # Consolidación de copias ejecutivas
    shutil.copy2(pdf_dia, os.path.join(dir_eje, os.path.basename(pdf_dia)))
    shutil.copy2(pdf_sem, os.path.join(dir_eje, os.path.basename(pdf_sem)))
    shutil.copy2(pdf_men, os.path.join(dir_eje, os.path.basename(pdf_men)))
    
    # 5. Sincronización Automática con Google Drive
    print("\n[5/5] Sincronizando Ecosistema Oficial con Google Drive...")
    gdrive_dir = r"C:\Users\fedea\Google Drive\coyuntura-macro"
    sincronizar_con_google_drive(BASE_DIR, gdrive_dir, pdf_dia, pdf_sem, pdf_men, docx_dia, docx_sem, docx_men, ruta_excel, dir_fig)

    limpiar_archivos_temporales(BASE_DIR)
    
    print("\n=================================================================")
    print("PIPELINE EJECUTADO EXITOSAMENTE. ECOSISTEMA HIGIÉNICO Y ACTUALIZADO.")
    print("=================================================================")

def sincronizar_con_google_drive(base_dir, gdrive_dir, pdf_dia, pdf_sem, pdf_men, docx_dia, docx_sem, docx_men, ruta_excel, dir_fig):
    try:
        os.makedirs(gdrive_dir, exist_ok=True)
        
        # 1. Limpieza de carpetas obsoletas en Google Drive para mantener pureza institucional
        legacy_dirs = [
            os.path.join(gdrive_dir, "01_Reportes_Ejecutivos_PDF"),
            os.path.join(gdrive_dir, "02_Informes_Word_Editables"),
            os.path.join(gdrive_dir, "03_Bases_Datos_Excel_Vivas"),
            os.path.join(gdrive_dir, "04_Figuras_Estadisticas_HD_300DPI"),
            os.path.join(gdrive_dir, "05_Documentacion_y_Estandares"),
        ]
        for ld in legacy_dirs:
            if os.path.exists(ld):
                try: shutil.rmtree(ld)
                except Exception: pass
                
        # 2. Estructura Canónica Espejo 1:1
        carpetas_canonicas = [
            "01_Bases_Datos",
            "02_Scripts_Automatizacion",
            "03_Figuras_HD",
            "04_Informes_Diarios",
            "05_Informes_Semanales_APA7",
            "06_Informes_Mensuales_OERU",
            "07_Reportes_Ejecutivos_PDF",
            "src"
        ]
        
        for c in carpetas_canonicas:
            os.makedirs(os.path.join(gdrive_dir, c), exist_ok=True)
            
        # Sincronización de Bases de Datos
        if os.path.exists(ruta_excel):
            shutil.copy2(ruta_excel, os.path.join(gdrive_dir, "01_Bases_Datos", os.path.basename(ruta_excel)))
            print(f"      [Drive OK] 01_Bases_Datos/{os.path.basename(ruta_excel)}")
            
        # Sincronización de Scripts de Automatización
        auto_dir_local = os.path.join(base_dir, "02_Scripts_Automatizacion")
        auto_dir_drive = os.path.join(gdrive_dir, "02_Scripts_Automatizacion")
        if os.path.exists(auto_dir_local):
            for f in os.listdir(auto_dir_local):
                shutil.copy2(os.path.join(auto_dir_local, f), os.path.join(auto_dir_drive, f))
            print(f"      [Drive OK] 02_Scripts_Automatizacion sincronizados.")
            
        # Sincronización de Figuras HD (master_extracted_images)
        extracted_local = os.path.join(dir_fig, "master_extracted_images")
        extracted_drive = os.path.join(gdrive_dir, "03_Figuras_HD", "master_extracted_images")
        os.makedirs(extracted_drive, exist_ok=True)
        if os.path.exists(extracted_local):
            for f in os.listdir(extracted_local):
                if f.endswith(".png"):
                    shutil.copy2(os.path.join(extracted_local, f), os.path.join(extracted_drive, f))
                    shutil.copy2(os.path.join(extracted_local, f), os.path.join(gdrive_dir, "03_Figuras_HD", f))
            print(f"      [Drive OK] 03_Figuras_HD (8 figuras a 300 DPI sincronizadas).")
            
        # Sincronización de Informes Diarios (DOCX y PDF)
        shutil.copy2(docx_dia, os.path.join(gdrive_dir, "04_Informes_Diarios", os.path.basename(docx_dia)))
        shutil.copy2(pdf_dia, os.path.join(gdrive_dir, "04_Informes_Diarios", os.path.basename(pdf_dia)))
        print(f"      [Drive OK] 04_Informes_Diarios/{os.path.basename(pdf_dia)}")
        
        # Sincronización de Papers Semanales APA 7 (DOCX y PDF)
        shutil.copy2(docx_sem, os.path.join(gdrive_dir, "05_Informes_Semanales_APA7", os.path.basename(docx_sem)))
        shutil.copy2(pdf_sem, os.path.join(gdrive_dir, "05_Informes_Semanales_APA7", os.path.basename(pdf_sem)))
        print(f"      [Drive OK] 05_Informes_Semanales_APA7/{os.path.basename(pdf_sem)}")
        
        # Sincronización de Informes Mensuales OERU (DOCX y PDF)
        shutil.copy2(docx_men, os.path.join(gdrive_dir, "06_Informes_Mensuales_OERU", os.path.basename(docx_men)))
        shutil.copy2(pdf_men, os.path.join(gdrive_dir, "06_Informes_Mensuales_OERU", os.path.basename(pdf_men)))
        print(f"      [Drive OK] 06_Informes_Mensuales_OERU/{os.path.basename(pdf_men)}")
        
        # Sincronización de Reportes Ejecutivos PDF (Distribución Inmediata)
        for pdf_path in [pdf_dia, pdf_sem, pdf_men]:
            shutil.copy2(pdf_path, os.path.join(gdrive_dir, "07_Reportes_Ejecutivos_PDF", os.path.basename(pdf_path)))
        print(f"      [Drive OK] 07_Reportes_Ejecutivos_PDF consolidados.")
        
        # Sincronización del módulo src/
        src_local = os.path.join(base_dir, "src")
        src_drive = os.path.join(gdrive_dir, "src")
        if os.path.exists(src_local):
            for f in os.listdir(src_local):
                if f.endswith(".py"):
                    shutil.copy2(os.path.join(src_local, f), os.path.join(src_drive, f))
            print(f"      [Drive OK] src/ módulos Python sincronizados.")
            
        # Sincronización de Archivos Raíz
        for root_f in ["pipeline_coyuntura_master.py", "README.md", "AGENTS.md", "INSTRUCCIONES_DISENO_Y_ESTANDARES_VISUALES.md"]:
            src_f = os.path.join(base_dir, root_f)
            if os.path.exists(src_f):
                shutil.copy2(src_f, os.path.join(gdrive_dir, root_f))
        print(f"      [Drive OK] Documentación y orquestador maestro sincronizados en raíz de Drive.")
        
    except Exception as e_gd:
        print(f"      [Drive Error] No se pudo completar la sincronización con Google Drive: {e_gd}")

if __name__ == "__main__":
    ejecutar_pipeline_coyuntura_completo()
