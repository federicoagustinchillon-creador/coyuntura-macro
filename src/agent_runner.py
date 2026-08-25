"""
================================================================================
ORQUESTADOR Y VALIDADOR DE CONTRATOS PARA AGENTES (AGENT RUNNER)
================================================================================
Autor: Federico Agustín Chillón
Facultad de Ciencias Económicas — UNCUYO
================================================================================
"""

import os
import sys
import json
import argparse
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SCHEMA_PATH = os.path.join(BASE_DIR, "src", "schema_datos_del_dia.json")
DATA_PATH = os.path.join(BASE_DIR, "01_Bases_Datos", "datos_del_dia.json")

def validar_datos_del_dia():
    print("[1/3] Validando contrato de datos (schema_datos_del_dia.json)...")
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Archivo de datos ausente: {DATA_PATH}")
        return False
    if not os.path.exists(SCHEMA_PATH):
        print(f"[ERROR] Esquema ausente: {SCHEMA_PATH}")
        return False
        
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    # Validación básica de estructura requerida
    for req in schema.get("required", []):
        if req not in data:
            print(f"[ERROR] Clave requerida ausente en datos_del_dia: {req}")
            return False
            
    print(f"      [OK] Contrato validado exitosamente para la fecha: {data.get('fecha')}")
    return True

def ejecutar_pipeline_desatendido():
    print("\n[2/3] Invocando pipeline maestro de coyuntura...")
    cmd = [sys.executable, os.path.join(BASE_DIR, "pipeline_coyuntura_master.py")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("[ERROR] El pipeline maestro falló:")
        print(res.stderr)
        return False
    print("      [OK] Pipeline ejecutado exitosamente.")
    return True

def auditar_salida():
    print("\n[3/3] Auditando entregables con verificar_estado_ecosistema.py...")
    cmd = [sys.executable, os.path.join(BASE_DIR, "02_Scripts_Automatizacion", "verificar_estado_ecosistema.py")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    return res.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Runner oficial para agentes de IA (Gemini Spark / Claude / n8n)")
    parser.add_argument("--dry-run", action="store_true", help="Valida el contrato sin compilar documentos")
    args = parser.parse_args()
    
    print("=================================================================")
    print("EJECUTANDO AGENT RUNNER — ECOSISTEMA DE COYUNTURA MACRO")
    print("=================================================================")
    
    if not validar_datos_del_dia():
        sys.exit(1)
        
    if args.dry_run:
        print("\n[DRY RUN] Validación completada con éxito. No se compilaron documentos.")
        sys.exit(0)
        
    if not ejecutar_pipeline_desatendido():
        sys.exit(1)
        
    if not auditar_salida():
        print("\n[FALLO] La auditoría de cobertura vertical o integridad reportó errores.")
        sys.exit(1)
        
    print("\n=================================================================")
    print("AGENT RUNNER COMPLETADO: 0 ERRORES. REPOSITORIO Y DRIVE ACTUALIZADOS.")
    print("=================================================================")
    sys.exit(0)

if __name__ == "__main__":
    main()
