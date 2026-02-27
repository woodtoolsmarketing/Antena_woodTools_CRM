import tkinter as tk
from tkinter import ttk, messagebox
import backend_gestor 

class GestorWoodToolsUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de informes de Whatsapp WoodTools")
        self.root.geometry("850x600") # Lo hice un poquitito más ancho para que entren los 4 botones cómodos
        self.root.configure(bg="#f4f6f9")
        
        # Preparamos la base de datos y el JSON si no existen
        backend_gestor.inicializar_db()

        # Cabecera
        frame_top = tk.Frame(root, bg="#2c3e50", pady=15)
        frame_top.pack(fill="x")
        tk.Label(frame_top, text="📊 Panel de Control - WhatsApp WoodTools", fg="white", bg="#2c3e50", font=("Arial", 16, "bold")).pack()

        # Actividad del Día
        self.lbl_actividad = tk.Label(root, text="Chats iniciados hoy: 0", font=("Arial", 14, "bold"), fg="#27ae60", bg="#f4f6f9")
        self.lbl_actividad.pack(pady=10)

        # Tabla de Vendedores
        frame_tabla = tk.Frame(root, padx=20)
        frame_tabla.pack(fill="both", expand=True)

        columnas = ("Num", "Nombre", "Celular", "Estado")
        self.tree = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=12)
        self.tree.heading("Num", text="N° Vendedor")
        self.tree.column("Num", width=80, anchor="center")
        self.tree.heading("Nombre", text="Nombre y Apellido")
        self.tree.column("Nombre", width=250)
        self.tree.heading("Celular", text="Celular")
        self.tree.column("Celular", width=150, anchor="center")
        self.tree.heading("Estado", text="Estado")
        self.tree.column("Estado", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        # Botones de Acción
        frame_botones = tk.Frame(root, bg="#f4f6f9", pady=15)
        frame_botones.pack()

        tk.Button(frame_botones, text="➕ Agregar Nuevo", command=self.abrir_ventana_agregar, bg="#3498db", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="🗑️ Eliminar Seleccionado", command=self.comando_eliminar, bg="#e74c3c", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="📥 Exportar Excel", command=self.comando_exportar, bg="#27ae60", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(frame_botones, text="🔄 Actualizar", command=self.refrescar_datos, bg="#e67e22", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        # Primer carga de datos y bucle de auto-refresco
        self.refrescar_datos()

    def refrescar_datos(self):
        # 1. Limpiamos la tabla
        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        # 2. Le pedimos al backend la info y la dibujamos
        vendedores = backend_gestor.obtener_vendedores_ui()
        for fila in vendedores:
            self.tree.insert("", "end", values=fila)
            
        # 3. Le pedimos al backend el total de hoy
        total_hoy = backend_gestor.obtener_conteo_hoy()
        self.lbl_actividad.config(text=f"Chats iniciados hoy: {total_hoy}")
        
        # 4. Programamos para que se repita solo en 5 segundos
        self.root.after(5000, self.refrescar_datos)

    def abrir_ventana_agregar(self):
        vent = tk.Toplevel(self.root)
        vent.title("Agregar Vendedor")
        vent.geometry("350x300")
        vent.configure(padx=20, pady=20)

        tk.Label(vent, text="Nombre y Apellido:").pack(anchor="w")
        e_nombre = tk.Entry(vent, width=40); e_nombre.pack(pady=5)

        tk.Label(vent, text="Número de Vendedor (Ej: 14):").pack(anchor="w")
        e_num = tk.Entry(vent, width=40); e_num.pack(pady=5)

        tk.Label(vent, text="Número Telefónico:").pack(anchor="w")
        e_tel = tk.Entry(vent, width=40); e_tel.pack(pady=5)

        tk.Label(vent, text="Zona (Solo para el Excel):").pack(anchor="w")
        e_zona = tk.Entry(vent, width=40); e_zona.pack(pady=5)

        def intentar_guardar():
            nom, num, tel, zona = e_nombre.get(), e_num.get(), e_tel.get(), e_zona.get()
            
            if not all([nom, num, tel, zona]): 
                return messagebox.showwarning("Faltan datos", "Por favor, completá todos los campos.")
            
            btn_guardar.config(text="Procesando Integración... Esperá...", state="disabled")
            vent.update() 
            
            exito, msj = backend_gestor.agregar_vendedor(nom, num, tel, zona)
            
            if exito:
                messagebox.showinfo("Operación Exitosa", msj)
                vent.destroy()
                self.refrescar_datos()
            else:
                messagebox.showerror("Error", msj)
                btn_guardar.config(text="Guardar e Integrar Vendedor", state="normal")

        btn_guardar = tk.Button(vent, text="Guardar e Integrar Vendedor", command=intentar_guardar, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"))
        btn_guardar.pack(pady=15)

    def comando_eliminar(self):
        # Nos fijamos qué fila tocó el usuario
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, hacé clic en un vendedor de la lista para seleccionarlo primero.")
            return
        
        # Extraemos los datos de esa fila
        item = self.tree.item(seleccion[0])
        numero_vendedor = str(item['values'][0])
        nombre_vendedor = item['values'][1]
        
        # Cartel de seguridad para no borrar sin querer
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
    ventana_principal = tk.Tk()
    app = GestorWoodToolsUI(ventana_principal)
    ventana_principal.mainloop()