import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from PIL import Image, ImageTk
import backend_gestor 

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GestorWoodToolsUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CRM Whatsapp Manager - WoodTools")
        self.root.geometry("1100x650") # Más ancho para que entre el panel lateral
        
        # --- COLORES DEL TEMA DARK NAVY ---
        self.bg_base = "#0A192F"      # Azul oscuro de fondo
        self.bg_panel = "#112240"     # Azul intermedio para paneles
        self.bg_header = "#020C1B"    # Azul casi negro para cabeceras
        self.fg_blanco = "#E6F1FF"    # Texto principal blanco brillante
        self.fg_gris = "#8892B0"      # Texto secundario grisáceo
        self.color_verde = "#00FF41"  # Verde lima brillante para "Activo"
        self.color_rojo = "#FF3333"   # Rojo para "Errores"
        
        self.root.configure(bg=self.bg_base)
        
        try:
            ruta_ico = resource_path(os.path.join("Imagenes", "logo.ico"))
            self.root.iconbitmap(ruta_ico)
        except Exception:
            pass

        backend_gestor.inicializar_db()

        # --- ESTILO DE LA TABLA (Con divisiones) ---
        style = ttk.Style()
        style.theme_use("clam") # Clam permite modificar bordes y colores fácilmente
        style.configure("Treeview", 
                        background=self.bg_panel, 
                        foreground=self.fg_blanco, 
                        fieldbackground=self.bg_panel,
                        rowheight=30,
                        bordercolor="#233554", lightcolor="#233554", darkcolor="#233554") # Lineas divisorias
        style.configure("Treeview.Heading", 
                        background=self.bg_header, 
                        foreground=self.fg_blanco, 
                        font=("Arial", 11, "bold"))
        style.map('Treeview', background=[('selected', '#233554')]) # Color al seleccionar

        # --- CABECERA SUPERIOR ---
        frame_top = tk.Frame(root, bg=self.bg_header, pady=15)
        frame_top.pack(fill="x")
        tk.Label(frame_top, text="📊 CRM WHATSAPP MANAGER - WOODTOOLS", fg=self.fg_blanco, bg=self.bg_header, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=20)

        try:
            ruta_png = resource_path(os.path.join("Imagenes", "logo.png"))
            imagen_original = Image.open(ruta_png)
            imagen_redimensionada = imagen_original.resize((45, 45), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(imagen_redimensionada)
            tk.Label(frame_top, image=self.logo_img, bg=self.bg_header).pack(side=tk.RIGHT, padx=20)
        except Exception:
            pass

        # Actividad General del Día
        self.lbl_actividad = tk.Label(root, text="Chats totales iniciados hoy: 0", font=("Arial", 13, "bold"), fg=self.color_verde, bg=self.bg_base)
        self.lbl_actividad.pack(pady=10)

        # --- ESTRUCTURA PRINCIPAL (Izquierda: Tabla / Derecha: Detalles) ---
        frame_cuerpo = tk.Frame(root, bg=self.bg_base)
        frame_cuerpo.pack(fill="both", expand=True, padx=20, pady=5)

        # Panel Izquierdo (Tabla)
        frame_tabla = tk.Frame(frame_cuerpo, bg=self.bg_base)
        frame_tabla.pack(side="left", fill="both", expand=True)

        columnas = ("Num", "Nombre", "Celular", "Estado")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=12)
        self.tree.heading("Num", text="N° Vendedor")
        self.tree.column("Num", width=80, anchor="center")
        self.tree.heading("Nombre", text="Nombre y Apellido")
        self.tree.column("Nombre", width=200)
        self.tree.heading("Celular", text="Celular")
        self.tree.column("Celular", width=120, anchor="center")
        self.tree.heading("Estado", text="Estado")
        self.tree.column("Estado", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True)
        # Evento: Cuando selecciona un vendedor, actualiza el panel lateral
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar_vendedor)

        # Panel Derecho (Actividad del Vendedor)
        self.frame_detalle = tk.Frame(frame_cuerpo, bg=self.bg_panel, width=300, highlightbackground="#233554", highlightthickness=1)
        self.frame_detalle.pack(side="right", fill="y", padx=(20, 0))
        self.frame_detalle.pack_propagate(False) # Evita que se encoja
        
        tk.Label(self.frame_detalle, text="Actividad del Vendedor", font=("Segoe UI", 12, "bold"), bg=self.bg_panel, fg=self.fg_blanco).pack(pady=(15, 5))
        tk.Frame(self.frame_detalle, height=1, bg="#233554").pack(fill="x", padx=10, pady=5) # Linea divisoria

        self.lbl_det_nombre = tk.Label(self.frame_detalle, text="Seleccione un vendedor", font=("Arial", 11, "bold"), bg=self.bg_panel, fg=self.fg_blanco, wraplength=280)
        self.lbl_det_nombre.pack(pady=10)
        
        self.lbl_det_estado = tk.Label(self.frame_detalle, text="Estado: --", font=("Arial", 14, "bold"), bg=self.bg_panel, fg=self.fg_gris)
        self.lbl_det_estado.pack(pady=5)
        
        self.lbl_det_error = tk.Label(self.frame_detalle, text="", font=("Arial", 9), bg=self.bg_panel, fg=self.color_rojo, wraplength=280)
        self.lbl_det_error.pack()

        self.lbl_det_chats = tk.Label(self.frame_detalle, text="Conversaciones hoy:\n0", font=("Arial", 11), bg=self.bg_panel, fg=self.fg_blanco, justify="center")
        self.lbl_det_chats.pack(pady=20)

        # --- BOTONES DE ACCIÓN INFERIORES ---
        frame_botones = tk.Frame(root, bg=self.bg_base, pady=15)
        frame_botones.pack()

        tk.Button(frame_botones, text="➕ Agregar", command=self.abrir_ventana_agregar, bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="✏️ Editar Info", command=self.abrir_ventana_editar, bg="#8e44ad", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="🗑️ Eliminar", command=self.comando_eliminar, bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="📥 Exportar Excel", command=self.comando_exportar, bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="🔄 Actualizar", command=self.refrescar_datos, bg="#e67e22", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # Variable para recordar qué ID estaba seleccionado
        self.vendedor_seleccionado_id = None
        self.vendedor_zona_oculta = {} # Diccionario para guardar la zona (que no se ve en la tabla)

        self.refrescar_datos()

    def al_seleccionar_vendedor(self, event):
        seleccion = self.tree.selection()
        if not seleccion:
            self.vendedor_seleccionado_id = None
            self.lbl_det_nombre.config(text="Seleccione un vendedor", fg=self.fg_gris)
            self.lbl_det_estado.config(text="Estado: --", fg=self.fg_gris)
            self.lbl_det_error.config(text="")
            self.lbl_det_chats.config(text="Conversaciones hoy:\n0")
            return
        
        item = self.tree.item(seleccion[0])
        self.vendedor_seleccionado_id = str(item['values'][0])
        nombre = item['values'][1]
        estado_icono = item['values'][3]
        
        self.lbl_det_nombre.config(text=f"{nombre}\n(N° {self.vendedor_seleccionado_id})", fg=self.fg_blanco)
        
        # Lógica de colores y estados
        if estado_icono == '✅' or estado_icono == '🟢':
            self.lbl_det_estado.config(text="Estado: Activo", fg=self.color_verde)
            self.lbl_det_error.config(text="")
        else:
            self.lbl_det_estado.config(text="Estado: Error de conexión", fg=self.color_rojo)
            self.lbl_det_error.config(text="(Revisar servidor o WhatsApp del celular)")
            
        # Buscar chats individuales
        chats = backend_gestor.obtener_actividad_vendedor_hoy(self.vendedor_seleccionado_id)
        self.lbl_det_chats.config(text=f"Conversaciones iniciadas hoy:\n{chats}")

    def refrescar_datos(self):
        # Guardar la selección actual antes de borrar
        seleccion_actual = self.tree.selection()
        id_a_reseleccionar = self.tree.item(seleccion_actual[0])['values'][0] if seleccion_actual else self.vendedor_seleccionado_id

        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        vendedores = backend_gestor.obtener_vendedores_ui()
        self.vendedor_zona_oculta.clear()
        
        for fila in vendedores:
            # fila viene: (numero, nombre, telefono, estado, zona)
            num, nom, tel, est, zona = fila
            self.vendedor_zona_oculta[str(num)] = zona # Guardamos la zona en secreto para cuando quiera editar
            item_id = self.tree.insert("", "end", values=(num, nom, tel, est))
            
            # Si era el que estaba seleccionado, lo volvemos a marcar
            if str(num) == str(id_a_reseleccionar):
                self.tree.selection_set(item_id)
            
        total_hoy = backend_gestor.obtener_conteo_hoy()
        self.lbl_actividad.config(text=f"Chats totales iniciados hoy: {total_hoy}")
        
        self.root.after(5000, self.refrescar_datos)

    def abrir_ventana_agregar(self):
        self._abrir_ventana_formulario("Agregar Nuevo Vendedor", es_edicion=False)

    def abrir_ventana_editar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return messagebox.showwarning("Atención", "Seleccioná un vendedor de la tabla para editarlo.")
        self._abrir_ventana_formulario("Editar Información", es_edicion=True, item_seleccionado=self.tree.item(seleccion[0]))

    def _abrir_ventana_formulario(self, titulo, es_edicion=False, item_seleccionado=None):
        vent = tk.Toplevel(self.root)
        vent.title(titulo)
        vent.geometry("380x360")
        vent.configure(padx=20, pady=20, bg=self.bg_base)
        
        # Estilo de labels para popup
        def lbl(txt):
            l = tk.Label(vent, text=txt, bg=self.bg_base, fg=self.fg_blanco, font=("Arial", 10, "bold"))
            l.pack(anchor="w")
            return l

        lbl("Nombre y Apellido:")
        e_nombre = tk.Entry(vent, width=40, font=("Arial", 10)); e_nombre.pack(pady=5)

        lbl("Número de Vendedor (Ej: 14 o 0-A):")
        e_num = tk.Entry(vent, width=40, font=("Arial", 10)); e_num.pack(pady=5)

        lbl("Número Telefónico (Se limpiará solo):")
        e_tel = tk.Entry(vent, width=40, font=("Arial", 10)); e_tel.pack(pady=5)

        lbl("Zona (Solo para el Excel):")
        e_zona = tk.Entry(vent, width=40, font=("Arial", 10)); e_zona.pack(pady=5)

        num_original = ""
        
        if es_edicion and item_seleccionado:
            num_original = str(item_seleccionado['values'][0])
            e_num.insert(0, num_original)
            e_nombre.insert(0, item_seleccionado['values'][1])
            e_tel.insert(0, str(item_seleccionado['values'][2]))
            e_zona.insert(0, self.vendedor_zona_oculta.get(num_original, ""))

        def intentar_guardar():
            nom, num, tel, zona = e_nombre.get(), e_num.get(), e_tel.get(), e_zona.get()
            if not all([nom, num, tel, zona]): 
                return messagebox.showwarning("Faltan datos", "Por favor, completá todos los campos.", parent=vent)
            
            btn_guardar.config(text="Procesando Integración... Esperá...", state="disabled", bg="#95a5a6")
            vent.update() 
            
            if es_edicion:
                exito, msj = backend_gestor.editar_vendedor(num_original, nom, num, tel, zona)
            else:
                exito, msj = backend_gestor.agregar_vendedor(nom, num, tel, zona)
            
            if exito:
                messagebox.showinfo("Operación Exitosa", msj, parent=self.root)
                vent.destroy()
                self.refrescar_datos()
            else:
                messagebox.showerror("Error", msj, parent=vent)
                btn_guardar.config(text="Guardar e Integrar Vendedor", state="normal", bg="#2ecc71")

        btn_guardar = tk.Button(vent, text="Guardar e Integrar Vendedor", command=intentar_guardar, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), pady=5)
        btn_guardar.pack(pady=20)

    def comando_eliminar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return messagebox.showwarning("Atención", "Por favor, hacé clic en un vendedor de la lista para seleccionarlo.")
        
        item = self.tree.item(seleccion[0])
        numero_vendedor = str(item['values'][0])
        nombre_vendedor = item['values'][1]
        
        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro que querés eliminar a {nombre_vendedor} (N° {numero_vendedor})?\n\nEsto lo borrará del sistema y reiniciará la antena de WhatsApp.")
        
        if confirmacion:
            exito, msj = backend_gestor.eliminar_vendedor(numero_vendedor)
            if exito:
                messagebox.showinfo("Éxito", msj)
                self.refrescar_datos()
            else:
                messagebox.showerror("Error", msj)

    def comando_exportar(self):
        exito, msj = backend_gestor.exportar_reporte_excel()
        if not exito:
            messagebox.showinfo("Atención", msj)

if __name__ == "__main__":
    try:
        import ctypes
        myappid = 'woodtools.crm.whatsapp.manager.1.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass 
    
    ventana_principal = tk.Tk()
    app = GestorWoodToolsUI(ventana_principal)
    ventana_principal.mainloop()