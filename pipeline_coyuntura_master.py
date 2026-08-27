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
        
    # 3. Compilación de Documentos (3 Niveles)
    print("\n[3/5] Compilando Documentos Institucionales (3 Niveles)...")
    
    # Nivel 1: Diario (2 Páginas) -- fecha_str no se pasa: el generador ya la
    # deriva de datos_del_dia.json internamente (src/generador_informe_diario._fecha_larga);
    # el nombre de archivo usa la misma fecha_ciclo para que ambos coincidan siempre.
    docx_dia = os.path.join(dir_dia, f"{fecha_ciclo}_Monitor_Diario_Mercados.docx")
    pdf_dia = docx_dia.replace(".docx", ".pdf")
    compilar_informe_diario(docx_dia)
    print("      -> [Nivel 1] Monitor Diario DOCX (2 págs):", docx_dia)

    # Nivel 2: Semanal (4 Páginas APA 7) -- periodo_str no se pasa: el generador
    # ya calcula el rango Lunes-Viernes correspondiente via
    # src/generador_paper_semanal._calcular_periodo_semanal(fecha).
    docx_sem = os.path.join(dir_sem, f"{fecha_ciclo}_Paper_Macroeconomico_Semanal.docx")
    pdf_sem = docx_sem.replace(".docx", ".pdf")
    compilar_paper_semanal_completo(docx_sem)
    print("      -> [Nivel 2] Paper Semanal DOCX (4 págs APA 7):", docx_sem)
    
    # Nivel 3: Mensual Master (DOCX y ReportLab 15 Páginas)
    docx_men = os.path.join(dir_men, "Informe_Coyuntura_Mensual_Agosto_2026_Federico_Chillon_Master.docx")
    construir_informe_mensual_master_docx(docx_men)
    print("      -> [Nivel 3] Informe Mensual Master DOCX compilado:", docx_men)

    # Generación del PDF Maestro con ReportLab (15 Páginas con ZeroWhitespaceCanvas y Outlines)
    pdf_men = generar_informe_mensual_reportlab()
    print("      -> [Nivel 3] Informe Mensual Master PDF (15 págs ReportLab):", pdf_men)
    
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
    sincronizar_con_google_drive(BASE_DIR, gdrive_dir, fecha_ciclo)

    limpiar_archivos_temporales(BASE_DIR)

    print("\n=================================================================")
    print("PIPELINE EJECUTADO EXITOSAMENTE. ECOSISTEMA HIGIÉNICO Y ACTUALIZADO.")
    print("=================================================================")

def sincronizar_con_google_drive(base_dir, gdrive_dir, fecha_ciclo):
    """Antes esta funcion copiaba archivos con shutil.copy2 directo a
    gdrive_dir -- pero gdrive_dir es un clon git (mismo remoto que este
    repo), sincronizado el resto del tiempo via 'git fetch + reset --hard
    origin/main'. Las dos rutas mezcladas dejaban el working tree del clon
    en Drive con cambios sin commitear que un 'reset --hard' posterior
    descartaba en silencio -- esa mezcla es la causa raiz de que 07_Reportes_Ejecutivos_PDF
    y el propio Drive quedaran desactualizados varias corridas seguidas. A
    partir de aqui la unica via es git: se commitea y pushea el repo
    principal, y el clon de Drive se resetea a ese mismo commit. Si no hay
    remoto configurado (repo local sin GitHub) se aborta con un mensaje
    claro en vez de fallar a mitad de camino."""
    def _git(args, cwd, check=True):
        r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
        if check and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} (en {cwd}) fallo:\n{r.stdout}\n{r.stderr}")
        return r

    try:
        _git(["rev-parse", "--is-inside-work-tree"], base_dir)
    except Exception:
        print("      [Drive Error] El repo principal no es un working tree git -- se omite la sincronizacion.")
        return

    status = _git(["status", "--porcelain"], base_dir).stdout
    if status.strip():
        _git(["add", "-A"], base_dir)
        msg = f"chore(pipeline): entregables del ciclo {fecha_ciclo} (diario, semanal, mensual + figuras)"
        _git(["commit", "-m", msg], base_dir)
        print(f"      [Git OK] Commit creado en el repo principal: {msg}")
        try:
            _git(["push", "origin", "HEAD"], base_dir)
            print("      [Git OK] Push a origin completado.")
        except Exception as e_push:
            print(f"      [Git Error] No se pudo pushear a origin (el commit local si quedo hecho): {e_push}")
    else:
        print("      [Git OK] Working tree del repo principal ya estaba limpio -- nada nuevo que commitear.")

    if not os.path.isdir(os.path.join(gdrive_dir, ".git")):
        print(f"      [Drive Error] {gdrive_dir} no es un clon git -- no se puede sincronizar via git. Clonarlo manualmente una vez.")
        return

    try:
        _git(["fetch", "origin"], gdrive_dir)
        _git(["reset", "--hard", "origin/main"], gdrive_dir)
        _git(["clean", "-fd"], gdrive_dir)
        head = _git(["rev-parse", "--short", "HEAD"], gdrive_dir).stdout.strip()
        print(f"      [Drive OK] Espejo 1:1 sincronizado con origin/main (HEAD={head}), sin residuos sin trackear.")
    except Exception as e_gd:
        print(f"      [Drive Error] No se pudo completar 'git fetch/reset/clean' en el espejo: {e_gd}")

if __name__ == "__main__":
    ejecutar_pipeline_coyuntura_completo()
