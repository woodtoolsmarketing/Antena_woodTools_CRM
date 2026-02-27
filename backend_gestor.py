import sqlite3
import pandas as pd
import os
import time
import json
from datetime import datetime
import subprocess 

DB_NAME = "estado_whatsapp.db"
JSON_NODE = "vendedores.json"

VENDEDORES_INICIALES = [
    ("40/15", "Nicolas Saad", "11 5752-8427", "Zona 40/15"),
    ("18", "Jorge Blasco", "11 4564-0940", "Zona 18"),
    ("16", "Lucas Cabaña", "11 4564-0831", "Zona 16"),
    ("44/04", "Alan Calvi", "11 5632-1012", "Zona 44/04"),
    ("9", "Ezequiel Calvi", "11 5345-5274", "Zona 9"),
    ("3", "Luis Quevedo", "11 6845-7778", "Zona 3"),
    ("5", "Roberto Golik", "11 6459-1316", "Zona 5"),
    ("0a", "Valentín Taquino", "11 4539-4279", "Recepción A"),
    ("0b", "Carlos Bolec", "11 6563-0406", "Recepción B"),
    ("01/302", "Emmanuel Capalbo", "11 5752-8428", "Zona 1/302")
]

def actualizar_json_node(numero, telefono):
    """Mantiene sincronizado el archivo que lee la Antena Node.js"""
    num_limpio = numero.replace('/', '_') # Node odia las barras
    datos = {}
    if os.path.exists(JSON_NODE):
        with open(JSON_NODE, 'r', encoding='utf-8') as f:
            try: datos = json.load(f)
            except: pass
            
    datos[num_limpio] = telefono.replace(" ", "").replace("-", "")
    
    with open(JSON_NODE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4)

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendedores (
                        numero TEXT PRIMARY KEY, nombre TEXT, telefono TEXT, zona TEXT, estado TEXT DEFAULT '❌')''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS actividad_diaria (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, numero_vendedor TEXT, telefono_cliente TEXT)''')
    
    cursor.execute("SELECT COUNT(*) FROM vendedores")
    if cursor.fetchone()[0] == 0:
        for v in VENDEDORES_INICIALES:
            cursor.execute("INSERT INTO vendedores (numero, nombre, telefono, zona) VALUES (?, ?, ?, ?)", v)
            actualizar_json_node(v[0], v[2]) # Sincroniza los iniciales con Node
    
    cursor.execute("UPDATE vendedores SET estado = '❌'")
    conn.commit()
    conn.close()

def obtener_vendedores_ui():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero, nombre, telefono, estado FROM vendedores ORDER BY nombre")
    datos = cursor.fetchall()
    conn.close()
    return datos

def obtener_conteo_hoy():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM actividad_diaria WHERE fecha = ?", (fecha_hoy,))
    total = cursor.fetchone()[0]
    conn.close()
    return total

def subir_a_github_y_reiniciar(nombre_vendedor):
    mensajes = []
    # 1. Reiniciar la Antena Node.js para que tome el nuevo JSON
    try:
        subprocess.run(["pm2", "restart", "Antena_WoodTools"], check=True, capture_output=True, shell=True)
        mensajes.append("🔄 Antena Node.js reiniciada. Escuchando al nuevo vendedor.")
    except Exception as e:
        mensajes.append("⚠️ No se pudo reiniciar PM2 automáticamente.")

    # 2. Subir a GitHub
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True, shell=True)
        subprocess.run(["git", "commit", "-m", f"Auto-Commit: Añadido vendedor {nombre_vendedor}"], check=True, capture_output=True, shell=True)
        subprocess.run(["git", "push"], check=True, capture_output=True, shell=True)
        mensajes.append("🚀 Cambios subidos a GitHub exitosamente.")
    except Exception as e:
        mensajes.append("⚠️ Falló la subida a Git (revisá la conexión).")
        
    return "\n\n".join(mensajes)

def agregar_vendedor(nombre, numero, telefono, zona):
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("INSERT INTO vendedores (numero, nombre, telefono, zona) VALUES (?, ?, ?, ?)", (numero, nombre, telefono, zona))
        conn.commit()
        
        # Actualizamos el JSON para que Node lo lea
        actualizar_json_node(numero, telefono)
        
        # Reiniciamos la antena y subimos a Git
        resultado_acciones = subir_a_github_y_reiniciar(nombre)
        
        return True, f"¡Vendedor registrado en la base de datos!\n\n{resultado_acciones}"
    except sqlite3.IntegrityError:
        return False, "Ese número de vendedor ya existe en la base de datos."
    finally:
        conn.close()

def eliminar_vendedor(numero):
    """Elimina un vendedor de la BD, del JSON, reinicia PM2 y sube a Git"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Buscamos el nombre para los mensajes
    cursor.execute("SELECT nombre FROM vendedores WHERE numero = ?", (numero,))
    resultado = cursor.fetchone()
    if not resultado:
        conn.close()
        return False, "El vendedor no existe en la base de datos."
    
    nombre_vendedor = resultado[0]
    
    # Lo borramos de SQLite
    cursor.execute("DELETE FROM vendedores WHERE numero = ?", (numero,))
    conn.commit()
    conn.close()

    # Lo borramos del JSON de Node.js
    num_limpio = numero.replace('/', '_')
    if os.path.exists(JSON_NODE):
        with open(JSON_NODE, 'r', encoding='utf-8') as f:
            try: datos = json.load(f)
            except: datos = {}
            
        if num_limpio in datos:
            del datos[num_limpio]
            with open(JSON_NODE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4)

    # Reiniciamos PM2 y subimos a GitHub
    mensajes = []
    try:
        subprocess.run(["pm2", "restart", "Antena_WoodTools"], check=True, capture_output=True, shell=True)
        mensajes.append("🔄 Antena Node.js reiniciada (vendedor removido).")
    except Exception as e:
        mensajes.append("⚠️ No se pudo reiniciar PM2 automáticamente.")

    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True, shell=True)
        subprocess.run(["git", "commit", "-m", f"Auto-Commit: Eliminado vendedor {nombre_vendedor} ({numero})"], check=True, capture_output=True, shell=True)
        subprocess.run(["git", "push"], check=True, capture_output=True, shell=True)
        mensajes.append("🚀 Cambios subidos a GitHub exitosamente.")
    except Exception as e:
        mensajes.append("⚠️ Falló la subida a Git (revisá la conexión).")
        
    return True, f"¡Vendedor {nombre_vendedor} eliminado correctamente!\n\n" + "\n\n".join(mensajes)

def exportar_reporte_excel():
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT 
            a.fecha AS Fecha, 
            v.nombre AS 'Nombre Vendedor',
            a.numero_vendedor AS 'N° Vendedor',
            v.zona AS 'Zona del Vendedor',
            a.telefono_cliente AS 'Celular del Cliente'
        FROM actividad_diaria a
        LEFT JOIN vendedores v ON a.numero_vendedor = v.numero
        ORDER BY a.id DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return False, "Todavía no hay chats registrados para exportar."
        
    nombre_reporte = f"Reporte_Chats_WoodTools_{datetime.now().strftime('%Y%m%d')}.xlsx"
    df.to_excel(nombre_reporte, index=False)
    
    os.startfile(nombre_reporte)
    return True, nombre_reporte