import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
from PIL import Image, ImageTk
import backend_gestor 
import threading

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
        self.root.geometry("1100x650") 
        
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
        style.theme_use("clam") 
        style.configure("Treeview", 
                        background=self.bg_panel, 
                        foreground=self.fg_blanco, 
                        fieldbackground=self.bg_panel,
                        rowheight=30,
                        bordercolor="#233554", lightcolor="#233554", darkcolor="#233554") 
        style.configure("Treeview.Heading", 
                        background=self.bg_header, 
                        foreground=self.fg_blanco, 
                        font=("Arial", 11, "bold"))
        style.map('Treeview', background=[('selected', '#233554')]) 

        # --- CABECERA SUPERIOR ---
        frame_top = tk.Frame(root, bg=self.bg_header, pady=15)
        frame_top.pack(fill="x")
        
        tk.Label(frame_top, text="📊 CRM WHATSAPP MANAGER", fg=self.fg_blanco, bg=self.bg_header, font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT, padx=20)

        # Botón para métricas de Emmanuel
        btn_metricas = tk.Button(frame_top, text="📈 Métricas Ads (Emmanuel)", command=self.abrir_ventana_metricas, bg="#FF9800", fg="white", font=("Segoe UI", 10, "bold"), cursor="hand2")
        btn_metricas.pack(side=tk.RIGHT, padx=20)

        try:
            ruta_png = resource_path(os.path.join("Imagenes", "logo.png"))
            imagen_original = Image.open(ruta_png)
            imagen_redimensionada = imagen_original.resize((45, 45), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(imagen_redimensionada)
            tk.Label(frame_top, image=self.logo_img, bg=self.bg_header).pack(side=tk.RIGHT, padx=10)
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
        self.tree.bind("<<TreeviewSelect>>", self.al_seleccionar_vendedor)

        # Panel Derecho (Actividad del Vendedor)
        self.frame_detalle = tk.Frame(frame_cuerpo, bg=self.bg_panel, width=300, highlightbackground="#233554", highlightthickness=1)
        self.frame_detalle.pack(side="right", fill="y", padx=(20, 0))
        self.frame_detalle.pack_propagate(False) 
        
        tk.Label(self.frame_detalle, text="Actividad del Vendedor", font=("Segoe UI", 12, "bold"), bg=self.bg_panel, fg=self.fg_blanco).pack(pady=(15, 5))
        tk.Frame(self.frame_detalle, height=1, bg="#233554").pack(fill="x", padx=10, pady=5) 

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

        self.vendedor_seleccionado_id = None
        self.vendedor_zona_oculta = {} 

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
        
        if estado_icono == '✅' or estado_icono == '🟢':
            self.lbl_det_estado.config(text="Estado: Activo", fg=self.color_verde)
            self.lbl_det_error.config(text="")
        else:
            self.lbl_det_estado.config(text="Estado: Error de conexión", fg=self.color_rojo)
            self.lbl_det_error.config(text="(Revisar servidor o WhatsApp del celular)")
            
        chats = backend_gestor.obtener_actividad_vendedor_hoy(self.vendedor_seleccionado_id)
        self.lbl_det_chats.config(text=f"Conversaciones iniciadas hoy:\n{chats}")

    def refrescar_datos(self):
        seleccion_actual = self.tree.selection()
        id_a_reseleccionar = self.tree.item(seleccion_actual[0])['values'][0] if seleccion_actual else self.vendedor_seleccionado_id

        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        vendedores = backend_gestor.obtener_vendedores_ui()
        self.vendedor_zona_oculta.clear()
        
        for fila in vendedores:
            num, nom, tel, est, zona = fila
            self.vendedor_zona_oculta[str(num)] = zona 
            item_id = self.tree.insert("", "end", values=(num, nom, tel, est))
            
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

    # =========================================================
    # NUEVA VENTANA DE MÉTRICAS PARA PUBLICIDADES (EMMANUEL)
    # =========================================================
    def abrir_ventana_metricas(self):
        vent = tk.Toplevel(self.root)
        vent.title("Métricas de Publicidad - Vendedor 01/302 (Emmanuel)")
        vent.geometry("900x600")
        vent.configure(bg=self.bg_base)
        
        lbl_titulo = tk.Label(vent, text="📊 Análisis de Chats por Publicidad (Emmanuel)", fg=self.fg_blanco, bg=self.bg_base, font=("Segoe UI", 16, "bold"))
        lbl_titulo.pack(pady=10)
        
        frame_contenido = tk.Frame(vent, bg=self.bg_base)
        frame_contenido.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Panel izquierdo (Lista de Fechas)
        frame_izq = tk.Frame(frame_contenido, bg=self.bg_panel, width=250)
        frame_izq.pack(side="left", fill="y", padx=(0, 10))
        
        tk.Label(frame_izq, text="Días de Campaña", bg=self.bg_panel, fg=self.fg_blanco, font=("Arial", 12, "bold")).pack(pady=10)
        
        listbox_fechas = tk.Listbox(frame_izq, bg=self.bg_base, fg=self.fg_blanco, font=("Arial", 11), selectbackground="#3498db")
        listbox_fechas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Panel derecho (Gráfico de Barras Nativas)
        frame_der = tk.Frame(frame_contenido, bg=self.bg_panel)
        frame_der.pack(side="right", fill="both", expand=True)
        
        lbl_info = tk.Label(frame_der, text="Seleccioná un día en la lista de la izquierda", bg=self.bg_panel, fg=self.fg_gris, font=("Arial", 12, "italic"))
        lbl_info.pack(pady=10)
        
        canvas_grafico = tk.Canvas(frame_der, bg=self.bg_panel, highlightthickness=0)
        canvas_grafico.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Etiqueta de estado
        lbl_estado = tk.Label(vent, text="Conectando con Google Sheets para traer las métricas...", fg="#f1c40f", bg=self.bg_base, font=("Arial", 10, "italic"))
        lbl_estado.pack(side="bottom", pady=5)
        
        self.datos_metricas_guardadas = {}
        
        def cargar_datos():
            def hilo_descarga():
                datos, msj = backend_gestor.obtener_metricas_publicidad_emmanuel()
                if datos is None:
                    vent.after(0, lambda: lbl_estado.config(text=f"Error de conexión: {msj}", fg=self.color_rojo))
                elif not datos:
                    vent.after(0, lambda: lbl_estado.config(text=msj, fg=self.color_verde))
                else:
                    self.datos_metricas_guardadas = datos
                    vent.after(0, poblar_listbox)
                    
            threading.Thread(target=hilo_descarga, daemon=True).start()
            
        def poblar_listbox():
            lbl_estado.config(text="✅ Datos de prospectos descargados correctamente.", fg=self.color_verde)
            listbox_fechas.delete(0, tk.END)
            for fecha, info in self.datos_metricas_guardadas.items():
                listbox_fechas.insert(tk.END, f"{fecha} ({info['total']} chats)")
                
        def al_seleccionar_fecha(evt):
            seleccion = listbox_fechas.curselection()
            if not seleccion: return
            
            index = seleccion[0]
            texto_item = listbox_fechas.get(index)
            fecha_sel = texto_item.split(" ")[0] 
            
            data_dia = self.datos_metricas_guardadas[fecha_sel]
            lbl_info.config(text=f"Actividad del {fecha_sel} - Total: {data_dia['total']} chats vía Publicidad", fg=self.color_verde, font=("Arial", 12, "bold"))
            
            dibujar_grafico_barras(canvas_grafico, data_dia['franjas'], fecha_sel)
            
        listbox_fechas.bind("<<ListboxSelect>>", al_seleccionar_fecha)
        
        def dibujar_grafico_barras(canvas, franjas, fecha):
            canvas.delete("all")
            canvas.update_idletasks() # Forzar cálculo de dimensiones
            
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width < 100: width = 600
            if height < 100: height = 400
            
            pad_x = 60
            pad_y = 50
            
            # Ejes X e Y
            canvas.create_line(pad_x, pad_y, pad_x, height - pad_y, fill=self.fg_blanco, width=2)
            canvas.create_line(pad_x, height - pad_y, width - pad_x + 20, height - pad_y, fill=self.fg_blanco, width=2)
            
            etiquetas = list(franjas.keys())
            valores = list(franjas.values())
            max_val = max(valores) if max(valores) > 0 else 10
            
            bar_width = ((width - 2 * pad_x) / len(etiquetas)) * 0.7
            espacio = (width - 2 * pad_x) / len(etiquetas)
            
            # Dibujar barras
            for i, (etiq, val) in enumerate(franjas.items()):
                x0 = pad_x + (i * espacio) + (espacio - bar_width) / 2
                y0 = height - pad_y
                x1 = x0 + bar_width
                
                # Altura de la barra proporcional al máximo valor del día
                h_bar = (val / max_val) * (height - 2 * pad_y)
                y1 = y0 - h_bar
                
                # Resaltar la franja con más interacción
                color_barra = self.color_verde if val == max_val and val > 0 else "#3498db"
                
                canvas.create_rectangle(x0, y0, x1, y1, fill=color_barra, outline=self.fg_blanco)
                
                # Número encima de la barra
                canvas.create_text(x0 + bar_width/2, y1 - 15, text=str(val), fill=self.fg_blanco, font=("Arial", 11, "bold"))
                
                # Etiqueta de hora (dividida en dos líneas para que entre)
                lbl_etiq = etiq.replace(" - ", "\n")
                canvas.create_text(x0 + bar_width/2, y0 + 20, text=lbl_etiq, fill=self.fg_gris, font=("Arial", 9))
                
            # Eje Y (referencias de cantidad lateral)
            pasos = 5
            for i in range(pasos + 1):
                valor_y = int(max_val * (i / pasos))
                pos_y = height - pad_y - (valor_y / max_val) * (height - 2 * pad_y)
                
                canvas.create_text(pad_x - 20, pos_y, text=str(valor_y), fill=self.fg_gris, font=("Arial", 10))
                # Línea guía horizontal punteada
                canvas.create_line(pad_x, pos_y, width - pad_x, pos_y, fill="#233554", dash=(4,4))
                
        # Arrancar carga al abrir la ventana
        cargar_datos()

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