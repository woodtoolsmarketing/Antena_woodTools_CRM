import sqlite3
import pandas as pd
import os
import time
import json
from datetime import datetime
import subprocess 

DB_NAME = "estado_whatsapp.db"
JSON_NODE = "vendedores.json"

# Números limpios y IDs actualizados a 0-A y 0-B
VENDEDORES_INICIALES = [
    ("40/15", "Nicolas Saad", "1157528427", "Zona 40/15"),
    ("18", "Jorge Blasco", "1145640940", "Zona 18"),
    ("16", "Lucas Cabaña", "1145640831", "Zona 16"),
    ("44/04", "Alan Calvi", "1156321012", "Zona 44/04"),
    ("9", "Ezequiel Calvi", "1153455274", "Zona 9"),
    ("3", "Luis Quevedo", "1168457778", "Zona 3"),
    ("5", "Roberto Golik", "1164591316", "Zona 5"),
    ("0-A", "Valentín Taquino", "1145394279", "Recepción A"),
    ("0-B", "Carlos Bolec", "1165630406", "Recepción B"),
    ("01/302", "Emmanuel Capalbo", "1157528428", "Zona 1/302")
]

def actualizar_json_node(numero, telefono):
    num_limpio = numero.replace('/', '_') 
    datos = {}
    if os.path.exists(JSON_NODE):
        with open(JSON_NODE, 'r', encoding='utf-8') as f:
            try: datos = json.load(f)
            except: pass
            
    # Limpiamos los caracteres acá también por las dudas
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
            actualizar_json_node(v[0], v[2]) 
    
    # Formatea los estados de versiones anteriores al nuevo tic
    cursor.execute("UPDATE vendedores SET estado = '❌'")
    conn.commit()
    conn.close()

def obtener_vendedores_ui():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT numero, nombre, telefono, estado, zona FROM vendedores ORDER BY nombre")
    datos = cursor.fetchall()
    conn.close()
    # Cambiar 🟢 viejo por ✅ para compatibilidad
    datos_limpios = []
    for d in datos:
        estado = '✅' if d[3] == '🟢' else d[3]
        datos_limpios.append((d[0], d[1], d[2], estado, d[4]))
    return datos_limpios

def obtener_conteo_hoy():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM actividad_diaria WHERE fecha = ?", (fecha_hoy,))
    total = cursor.fetchone()[0]
    conn.close()
    return total

def obtener_actividad_vendedor_hoy(numero_vendedor):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM actividad_diaria WHERE fecha = ? AND numero_vendedor = ?", (fecha_hoy, numero_vendedor))
    total = cursor.fetchone()[0]
    conn.close()
    return total

def subir_a_github_y_reiniciar(nombre_vendedor, accion="Añadido"):
    mensajes = []
    try:
        subprocess.run(["pm2", "restart", "Antena_WoodTools"], check=True, capture_output=True, shell=True)
        mensajes.append("🔄 Antena Node.js reiniciada. Aplicando cambios...")
    except Exception as e:
        mensajes.append("⚠️ No se pudo reiniciar PM2 automáticamente.")

    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True, shell=True)
        subprocess.run(["git", "commit", "-m", f"Auto-Commit: {accion} vendedor {nombre_vendedor}"], check=True, capture_output=True, shell=True)
        subprocess.run(["git", "push"], check=True, capture_output=True, shell=True)
        mensajes.append("🚀 Cambios subidos a GitHub exitosamente.")
    except Exception as e:
        mensajes.append("⚠️ Falló la subida a Git (revisá la conexión).")
        
    return "\n\n".join(mensajes)

def agregar_vendedor(nombre, numero, telefono, zona):
    # Limpiamos el teléfono antes de guardar
    tel_limpio = telefono.replace(" ", "").replace("-", "")
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute("INSERT INTO vendedores (numero, nombre, telefono, zona) VALUES (?, ?, ?, ?)", (numero, nombre, tel_limpio, zona))
        conn.commit()
        actualizar_json_node(numero, tel_limpio)
        resultado_acciones = subir_a_github_y_reiniciar(nombre, "Añadido")
        return True, f"¡Vendedor registrado en la base de datos!\n\n{resultado_acciones}"
    except sqlite3.IntegrityError:
        return False, "Ese número de vendedor ya existe en la base de datos."
    finally:
        conn.close()

def editar_vendedor(numero_original, nombre, numero_nuevo, telefono, zona):
    tel_limpio = telefono.replace(" ", "").replace("-", "")
    conn = sqlite3.connect(DB_NAME)
    try:
        # Si le cambió el número ID, chequeamos que el nuevo no exista
        if numero_original != numero_nuevo:
            cursor = conn.cursor()
            cursor.execute("SELECT numero FROM vendedores WHERE numero = ?", (numero_nuevo,))
            if cursor.fetchone():
                return False, f"El número de vendedor {numero_nuevo} ya está en uso."
                
        # Actualizamos la base de datos
        conn.execute("UPDATE vendedores SET numero = ?, nombre = ?, telefono = ?, zona = ? WHERE numero = ?", 
                     (numero_nuevo, nombre, tel_limpio, zona, numero_original))
                     
        # Si cambió el número ID, actualizamos el historial para no perder chats pasados
        if numero_original != numero_nuevo:
            conn.execute("UPDATE actividad_diaria SET numero_vendedor = ? WHERE numero_vendedor = ?", (numero_nuevo, numero_original))
            
            # Borramos el viejo del JSON
            num_viejo_limpio = numero_original.replace('/', '_')
            if os.path.exists(JSON_NODE):
                with open(JSON_NODE, 'r', encoding='utf-8') as f:
                    try: datos = json.load(f)
                    except: datos = {}
                if num_viejo_limpio in datos:
                    del datos[num_viejo_limpio]
                    with open(JSON_NODE, 'w', encoding='utf-8') as f:
                        json.dump(datos, f, indent=4)
                        
        conn.commit()
        
        # Agregamos/Actualizamos el JSON
        actualizar_json_node(numero_nuevo, tel_limpio)
        
        resultado = subir_a_github_y_reiniciar(nombre, "Editado")
        return True, f"¡Vendedor editado correctamente!\n\n{resultado}"
    except Exception as e:
        return False, f"Error al editar: {e}"
    finally:
        conn.close()

def eliminar_vendedor(numero):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM vendedores WHERE numero = ?", (numero,))
    resultado = cursor.fetchone()
    if not resultado:
        conn.close()
        return False, "El vendedor no existe en la base de datos."
    
    nombre_vendedor = resultado[0]
    cursor.execute("DELETE FROM vendedores WHERE numero = ?", (numero,))
    conn.commit()
    conn.close()

    num_limpio = numero.replace('/', '_')
    if os.path.exists(JSON_NODE):
        with open(JSON_NODE, 'r', encoding='utf-8') as f:
            try: datos = json.load(f)
            except: datos = {}
        if num_limpio in datos:
            del datos[num_limpio]
            with open(JSON_NODE, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=4)

    mensajes = subir_a_github_y_reiniciar(nombre_vendedor, "Eliminado")
    return True, f"¡Vendedor {nombre_vendedor} eliminado correctamente!\n\n{mensajes}"

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