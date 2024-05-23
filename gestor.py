import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta
import calendar
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

# Crear la ventana principal
root = ttkb.Window(themename="flatly")
root.title("Gestión de Horarios de Natación")
root.geometry("1200x800")
root.resizable(True, True)

# Centrar la ventana en la pantalla
window_width = 1200
window_height = 800
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# Conectar a la base de datos (se creará una nueva si no existe)
conn = sqlite3.connect('horarios_natacion.db')
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alumnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tutor TEXT NOT NULL,
        edad INTEGER,
        contacto TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS clases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombres TEXT NOT NULL,
        lugar TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        duracion INTEGER NOT NULL,
        pendiente INTEGER,
        alumno_id INTEGER,
        FOREIGN KEY (alumno_id) REFERENCES alumnos (id)
    )
''')
conn.commit()

# Función para cambiar el contenido del panel principal
def mostrar_frame(frame):
    frame.tkraise()

# Paneles de contenido
registro_alumnos_frame = ttkb.Labelframe(root, text="Registro de Alumnos", padding=20)
registro_clases_frame = ttkb.Labelframe(root, text="Registro de Clases", padding=20)

for frame in (registro_alumnos_frame, registro_clases_frame):
    frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

# Menú de Navegación
menu_frame = ttkb.Frame(root, padding=20)
menu_frame.grid(row=0, column=0, sticky='ew')

ttkb.Button(menu_frame, text="Registro de Alumnos", command=lambda: mostrar_frame(registro_alumnos_frame)).pack(side="left", padx=10)
ttkb.Button(menu_frame, text="Registro de Clases", command=lambda: mostrar_frame(registro_clases_frame)).pack(side="left", padx=10)

# Generar lista de opciones de tiempo en intervalos de 15 minutos
def generar_horas():
    horas = []
    hora_inicial = datetime.strptime("08:00", "%H:%M")
    hora_final = datetime.strptime("20:00", "%H:%M")
    delta = timedelta(minutes=15)
    while hora_inicial <= hora_final:
        horas.append(hora_inicial.strftime("%H:%M"))
        hora_inicial += delta
    return horas

horas_disponibles = generar_horas()

# Función para limpiar los campos después de agregar una clase o alumno
def limpiar_campos():
    global entries_nombres
    for entry in entries_nombres:
        entry.delete(0, tk.END)
    entry_lugar.delete(0, tk.END)
    duracion_var.set(15)
    entry_hora.set('')
    for var in dias_vars:
        var.set(0)
    var_horarios_diferentes.set(0)
    for entry in entry_horas:
        entry.grid_remove()
        entry.set('')
    var_todo_mes.set(0)
    spin_alumnos.set(1)
    actualizar_alumnos()

def limpiar_campos_alumnos():
    entry_nombre_alumno.delete(0, tk.END)
    entry_tutor.delete(0, tk.END)
    entry_edad.delete(0, tk.END)
    entry_contacto.delete(0, tk.END)

# Función para añadir un alumno
def agregar_alumno():
    nombre = entry_nombre_alumno.get().strip()
    tutor = entry_tutor.get().strip()
    edad = entry_edad.get().strip()
    contacto = entry_contacto.get().strip()

    if nombre and tutor:
        cursor.execute('''
            INSERT INTO alumnos (nombre, tutor, edad, contacto)
            VALUES (?, ?, ?, ?)
        ''', (nombre, tutor, edad if edad else None, contacto if contacto else None))
        conn.commit()
        messagebox.showinfo("Éxito", "Alumno añadido exitosamente")
        limpiar_campos_alumnos()
    else:
        messagebox.showerror("Error", "Por favor, completa los campos obligatorios (Nombre y Tutor)")

# Función para actualizar los nombres de los alumnos en el combobox de la clase
def actualizar_nombres_alumnos():
    cursor.execute('SELECT nombre FROM alumnos')
    alumnos = cursor.fetchall()
    nombres_alumnos = [alumno[0] for alumno in alumnos]
    for combo in entry_alumnos:
        combo['values'] = nombres_alumnos

# Función para añadir una clase
def agregar_clase():
    global entries_nombres
    nombres = [combo.get().strip() for combo in entry_alumnos if combo.get().strip()]
    lugar = entry_lugar.get().strip()
    dias_seleccionados = [var.get() for var in dias_vars]
    hora = entry_hora.get().strip()
    duracion = duracion_var.get()
    agregar_todo_mes = var_todo_mes.get()
    usar_horarios_diferentes = var_horarios_diferentes.get()
    horarios = [entry_horas[i].get().strip() if dias_vars[i].get() else '' for i in range(len(dias))]

    if nombres and lugar and any(dias_seleccionados) and (hora or (usar_horarios_diferentes and all(horarios[i] for i, d in enumerate(dias_seleccionados) if d))) and duracion:
        for i, dia in enumerate(dias_seleccionados):
            if dia:
                hora_a_usar = horarios[i] if usar_horarios_diferentes else hora
                dia_nombre = dias[i]
                if agregar_todo_mes:
                    fechas = obtener_fechas_restantes_mes(dia_nombre)
                else:
                    fechas = [obtener_fecha(dia_nombre)]

                for fecha in fechas:
                    if not verificar_conflicto(fecha, hora_a_usar):
                        for nombre in nombres:
                            cursor.execute('SELECT id FROM alumnos WHERE nombre = ?', (nombre,))
                            alumno_id = cursor.fetchone()[0]
                            cursor.execute('''
                                INSERT INTO clases (nombres, lugar, fecha, hora, duracion, pendiente, alumno_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (nombre, lugar, fecha, hora_a_usar, duracion, 0, alumno_id))
                        conn.commit()
                    else:
                        messagebox.showerror("Error", f"Conflicto con otra clase el {dia_nombre} a las {hora_a_usar} en la fecha {fecha}")
                        return
        messagebox.showinfo("Éxito", "Clase añadida exitosamente")
        mostrar_calendario_mejorado()
        root.update_idletasks()  
        limpiar_campos()
    else:
        campos_faltantes = []
        if not nombres:
            campos_faltantes.append("Nombres")
        if not lugar:
            campos_faltantes.append("Lugar")
        if not any(dias_seleccionados):
            campos_faltantes.append("Días de la semana")
        if not hora and not (usar_horarios_diferentes and all(horarios[i] for i, d in enumerate(dias_seleccionados) if d)):
            campos_faltantes.append("Hora")
        if not duracion:
            campos_faltantes.append("Duración")
        messagebox.showerror("Error", f"Por favor, completa todos los campos: {', '.join(campos_faltantes)}")

# Función para verificar conflictos de horarios
def verificar_conflicto(fecha, hora):
    cursor.execute('''
        SELECT * FROM clases WHERE fecha = ? AND hora = ?
    ''', (fecha, hora))
    return cursor.fetchone() is not None

# Función para obtener la fecha de un día de la semana
def obtener_fecha(dia_nombre):
    today = datetime.now()
    days_ahead = dias.index(dia_nombre) - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

# Función para obtener todas las fechas restantes del mes para un día de la semana
def obtener_fechas_restantes_mes(dia_nombre):
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    last_day_of_month = calendar.monthrange(current_year, current_month)[1]
    fechas = []
    for day in range(today.day, last_day_of_month + 1):
        fecha = datetime(current_year, current_month, day)
        if fecha.weekday() == dias.index(dia_nombre):
            fechas.append(fecha.strftime('%Y-%m-%d'))
    return fechas

# Función para mostrar el calendario mejorado
def mostrar_calendario_mejorado():
    for widget in frame_calendario.winfo_children():
        widget.destroy()
    cal = calendar.monthcalendar(ano, mes)
    dias_semana = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]

    # Mostrar los botones de navegación del mes
    ttkb.Button(frame_calendario, text="<", command=lambda: cambiar_mes(-1)).grid(row=0, column=0, sticky="w")
    ttkb.Label(frame_calendario, text=f"{calendar.month_name[mes]} {ano}", bootstyle=INFO, anchor="center").grid(row=0, column=1, columnspan=5, sticky="ew")
    ttkb.Button(frame_calendario, text=">", command=lambda: cambiar_mes(1)).grid(row=0, column=6, sticky="e")

    # Mostrar los días de la semana
    for i, dia in enumerate(dias_semana):
        ttkb.Label(frame_calendario, text=dia, bootstyle=SECONDARY).grid(row=1, column=i, padx=5, pady=5)

    # Mostrar los días del mes
    for week in range(len(cal)):
        for day in range(len(cal[week])):
            if cal[week][day] != 0:
                fecha = datetime(ano, mes, cal[week][day]).strftime('%Y-%m-%d')
                dia_label = ttkb.Label(frame_calendario, text=str(cal[week][day]), bootstyle=INFO if verificar_dia_con_clase(fecha) else SECONDARY)
                dia_label.grid(row=week+2, column=day, padx=5, pady=5)
                dia_label.bind("<Button-1>", lambda e, d=cal[week][day]: mostrar_clases_del_dia(d, mes, ano))

def cambiar_mes(delta):
    global mes, ano
    mes += delta
    if mes > 12:
        mes = 1
        ano += 1
    elif mes < 1:
        mes = 12
        ano -= 1
    mostrar_calendario_mejorado()

def verificar_dia_con_clase(fecha):
    cursor.execute('SELECT * FROM clases WHERE fecha = ?', (fecha,))
    return cursor.fetchone() is not None

def mostrar_clases_del_dia(dia, mes, ano):
    for widget in frame_clases.winfo_children():
        widget.destroy()
    fecha = datetime(ano, mes, dia).strftime('%Y-%m-%d')
    cursor.execute('SELECT nombres, lugar, hora, duracion FROM clases WHERE fecha = ?', (fecha,))
    clases = cursor.fetchall()
    if clases:
        clases.sort(key=lambda x: datetime.strptime(x[2], '%H:%M'))
        tree = ttkb.Treeview(frame_clases, columns=("Hora", "Alumno(s)", "Lugar"), show="headings", bootstyle=INFO)
        tree.heading("Hora", text="Hora")
        tree.heading("Alumno(s)", text="Alumno(s)")
        tree.heading("Lugar", text="Lugar")
        tree.column("Hora", width=100, anchor="center")
        tree.column("Alumno(s)", width=200, anchor="center")
        tree.column("Lugar", width=200, anchor="center")
        for clase in clases:
            hora_fin = (datetime.strptime(clase[2], '%H:%M') + timedelta(minutes=clase[3])).strftime('%H:%M')
            tree.insert("", "end", values=(f"{clase[2]} - {hora_fin}", clase[0], clase[1]))
        tree.pack(expand=True, fill="both", padx=10, pady=10)
    else:
        ttkb.Label(frame_clases, text="No hay clases este día", bootstyle=WARNING).pack(pady=20)

# Función para actualizar los campos de nombres de alumnos
def actualizar_alumnos():
    global entry_alumnos
    for widget in frame_alumnos.winfo_children():
        widget.destroy()
    num_alumnos = spin_alumnos.get()
    if not num_alumnos:
        num_alumnos = 1
    num_alumnos = int(num_alumnos)
    entry_alumnos = []
    for i in range(num_alumnos):
        ttkb.Label(frame_alumnos, text=f" • Nombre del alumno {i+1}").grid(row=i, column=0, padx=5, pady=5, sticky="w")
        entry_alumno = ttkb.Combobox(frame_alumnos, values=[], width=20)
        entry_alumno.grid(row=i, column=1, padx=5, pady=4, sticky="w")
        entry_alumnos.append(entry_alumno)
    actualizar_nombres_alumnos()

def mostrar_ocultar_horarios():
    if var_horarios_diferentes.get():
        label_hora.grid_remove()  # Ocultar la etiqueta de hora global
        entry_hora.grid_remove()  # Ocultar el campo de hora global
        for i, dia in enumerate(dias):
            if dias_vars[i].get():
                entry_horas[i].grid(row=8+i, column=1, padx=5, pady=5, sticky="w")
            else:
                entry_horas[i].grid_remove()
    else:
        label_hora.grid()  # Mostrar la etiqueta de hora global
        entry_hora.grid()  # Mostrar el campo de hora global
        for entry in entry_horas:
            entry.grid_remove()

def actualizar_horarios():
    if var_horarios_diferentes.get():
        for i, dia in enumerate(dias):
            if dias_vars[i].get():
                entry_horas[i].grid(row=8+i, column=1, padx=5, pady=5, sticky="w")
            else:
                entry_horas[i].grid_remove()

# Registro de Alumnos
ttkb.Label(registro_alumnos_frame, text="Registro de Alumnos", font="-size 15 -weight bold").pack(pady=10)
ttkb.Label(registro_alumnos_frame, text="Nombre del Alumno:").pack(pady=5, anchor="w")
entry_nombre_alumno = ttkb.Entry(registro_alumnos_frame, width=30)
entry_nombre_alumno.pack(pady=5)

ttkb.Label(registro_alumnos_frame, text="Nombre del Tutor:").pack(pady=5, anchor="w")
entry_tutor = ttkb.Entry(registro_alumnos_frame, width=30)
entry_tutor.pack(pady=5)

ttkb.Label(registro_alumnos_frame, text="Edad (Opcional):").pack(pady=5, anchor="w")
entry_edad = ttkb.Entry(registro_alumnos_frame, width=30)
entry_edad.pack(pady=5)

ttkb.Label(registro_alumnos_frame, text="Contacto (Opcional):").pack(pady=5, anchor="w")
entry_contacto = ttkb.Entry(registro_alumnos_frame, width=30)
entry_contacto.pack(pady=5)

ttkb.Button(registro_alumnos_frame, text="Agregar Alumno", command=agregar_alumno).pack(pady=10)

# Registro de Clases
registro_frame = ttkb.Labelframe(registro_clases_frame, text="Registro de Clases", bootstyle="primary", padding=10)
registro_frame.pack(fill="both", expand=True, padx=10, pady=10)

ttkb.Label(registro_frame, text="Número de Alumnos:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
spin_alumnos = ttkb.Spinbox(registro_frame, from_=1, to=10, command=actualizar_alumnos, width=20)
spin_alumnos.grid(row=0, column=1, padx=5, pady=5, sticky="w")
spin_alumnos.set(1)

frame_alumnos = ttkb.Frame(registro_frame)
frame_alumnos.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
actualizar_alumnos()

ttkb.Label(registro_frame, text="Lugar").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_lugar = ttkb.Entry(registro_frame, width=23)
entry_lugar.grid(row=2, column=1, padx=5, pady=5, sticky="w")

ttkb.Label(registro_frame, text="Duración").grid(row=3, column=0, padx=5, pady=5, sticky="w")
duration_frame = ttkb.Frame(registro_frame)
duration_frame.grid(row=3, column=1, padx=0, pady=5, sticky="w")
duracion_var = tk.IntVar()
duracion_menu = ttkb.Combobox(duration_frame, textvariable=duracion_var, width=2)
duracion_menu['values'] = (15, 30, 45, 60)
duracion_menu.grid(row=0, column=0, padx=5, pady=5, sticky="w")
duracion_menu.current(0)
ttkb.Label(duration_frame, text="minutos").grid(row=0, column=1, padx=5, pady=5, sticky="w")

label_hora = ttkb.Label(registro_frame, text="Hora (HH:MM)")
label_hora.grid(row=4, column=0, padx=5, pady=5, sticky="w")
entry_hora = ttkb.Combobox(registro_frame, values=horas_disponibles, width=5)
entry_hora.grid(row=4, column=1, padx=5, pady=5, sticky="w")

var_horarios_diferentes = tk.IntVar()
ttkb.Checkbutton(registro_frame, text="Usar horarios diferentes para cada día", variable=var_horarios_diferentes, command=mostrar_ocultar_horarios).grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="w")

var_todo_mes = tk.IntVar()
ttkb.Checkbutton(registro_frame, text="Agregar en todo el mes", variable=var_todo_mes).grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="w")

ttkb.Label(registro_frame, text="Días de la semana").grid(row=7, column=0, padx=5, pady=10, sticky="w")
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dias_vars = [tk.IntVar() for _ in dias]

entry_horas = []
for i, dia in enumerate(dias):
    ttkb.Checkbutton(registro_frame, text=dia, variable=dias_vars[i], command=actualizar_horarios).grid(row=8+i, column=0, padx=5, pady=5, sticky="w")
    entry_hora_dia = ttkb.Combobox(registro_frame, values=horas_disponibles, width=5)
    entry_hora_dia.grid(row=8+i, column=1, padx=5, pady=5, sticky="w")
    entry_hora_dia.grid_remove()  # Ocultar inicialmente
    entry_horas.append(entry_hora_dia)

ttkb.Button(registro_frame, text="Añadir Clase", command=agregar_clase).grid(row=15, column=0, columnspan=2, padx=5, pady=15, sticky="w")

# Frame para el calendario
frame_calendario = ttkb.Frame(root, padding=20)
frame_calendario.grid(row=1, column=1, sticky='nsew')

# Frame para las clases
frame_clases = ttkb.Frame(root, padding=20)
frame_clases.grid(row=2, column=1, sticky='nsew')

# Obtener el mes y año actual
now = datetime.now()
mes = now.month
ano = now.year

# Mostrar el calendario inicial
mostrar_calendario_mejorado()

# Ejecutar el bucle principal de la interfaz
root.mainloop()

# Cerrar la conexión a la base de datos al finalizar
conn.close()