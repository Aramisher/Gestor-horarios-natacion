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
position_top = int(screen_height/2 - window_height/2)
position_right = int(screen_width/2 - window_width/2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# Conectar a la base de datos (se creará una nueva si no existe)
conn = sqlite3.connect('horarios_natacion.db')
cursor = conn.cursor()

# Crear una tabla si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS clases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombres TEXT,
        lugar TEXT,
        fecha TEXT,
        hora TEXT,
        duracion INTEGER,
        pendiente INTEGER
    )
''')
conn.commit()

# Definir entries_nombres y entry_horas globalmente
entries_nombres = []
entry_horas = []

# Función para añadir una clase
def agregar_clase():
    global entries_nombres
    nombres = ', '.join([entry.get() for entry in entries_nombres if entry.get().strip()])
    lugar = entry_lugar.get().strip()
    dias_seleccionados = [var.get() for var in dias_vars]
    hora = entry_hora.get().strip()
    duracion = duracion_var.get()
    agregar_todo_mes = var_todo_mes.get()

    # Verificación de horarios diferentes
    usar_horarios_diferentes = var_horarios_diferentes.get()
    horarios = [entry_horas[i].get().strip() if dias_vars[i].get() else '' for i in range(len(dias))]

    # Mensajes de depuración
    print(f"Nombres: {nombres}")
    print(f"Lugar: {lugar}")
    print(f"Días seleccionados: {dias_seleccionados}")
    print(f"Hora global: {hora}")
    print(f"Horarios diferentes: {horarios}")
    print(f"Duración: {duracion}")
    print(f"Agregar en todo el mes: {agregar_todo_mes}")

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
                        cursor.execute('''
                            INSERT INTO clases (nombres, lugar, fecha, hora, duracion, pendiente)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (nombres, lugar, fecha, hora_a_usar, duracion, 0))
                        conn.commit()
                    else:
                        messagebox.showerror("Error", f"Conflicto con otra clase el {dia_nombre} a las {hora_a_usar} en la fecha {fecha}")
                        return
        messagebox.showinfo("Éxito", "Clase añadida exitosamente")
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
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

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
    global entries_nombres
    for widget in frame_alumnos.winfo_children():
        widget.destroy()
    num_alumnos = spin_alumnos.get()
    if not num_alumnos:
        num_alumnos = 1
    num_alumnos = int(num_alumnos)
    entries_nombres = []
    for i in range(num_alumnos):
        ttkb.Label(frame_alumnos, text=f"Nombre del alumno {i+1}").grid(row=i, column=0, padx=5, pady=5, sticky="w")
        entry_nombre = ttkb.Entry(frame_alumnos, width=23)
        entry_nombre.grid(row=i, column=1, padx=5, pady=5, sticky="w")
        entries_nombres.append(entry_nombre)

# Función para mostrar u ocultar el menú de horarios diferentes
def mostrar_ocultar_horarios():
    if var_horarios_diferentes.get():
        label_hora.grid_remove()  # Ocultar la etiqueta de hora global
        entry_hora.grid_remove()  # Ocultar el campo de hora global
        for i, dia in enumerate(dias):
            if dias_vars[i].get():
                entry_horas[i].grid(row=9+i, column=1, padx=5, pady=5, sticky="w")
            else:
                entry_horas[i].grid_remove()
    else:
        label_hora.grid()  # Mostrar la etiqueta de hora global
        entry_hora.grid()  # Mostrar el campo de hora global
        for entry in entry_horas:
            entry.grid_remove()

# Función para actualizar los horarios según los días seleccionados
def actualizar_horarios():
    if var_horarios_diferentes.get():
        for i, dia in enumerate(dias):
            if dias_vars[i].get():
                entry_horas[i].grid(row=9+i, column=1, padx=5, pady=5, sticky="w")
            else:
                entry_horas[i].grid_remove()

# Interfaz de entrada para los datos de las clases
menu_frame = ttkb.Frame(root, padding=20)
menu_frame.pack(side="left", fill="y", expand=False)

# Marco alrededor de la sección de registro de alumnos
registro_frame = ttkb.Labelframe(menu_frame, text="Registro de alumnos", bootstyle="primary", padding=10)
registro_frame.pack(fill="both", expand=True, padx=10, pady=10)

ttkb.Label(registro_frame, text="Número de alumnos").grid(row=0, column=0, padx=5, pady=5, sticky="w")
spin_alumnos = ttkb.Spinbox(registro_frame, from_=1, to=10, command=actualizar_alumnos, width=20)
spin_alumnos.grid(row=0, column=1, padx=5, pady=5, sticky="w")
spin_alumnos.set(1)

frame_alumnos = ttkb.Frame(registro_frame, padding=5)
frame_alumnos.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")
actualizar_alumnos()

ttkb.Label(registro_frame, text="Lugar").grid(row=2, column=0, padx=5, pady=5, sticky="w")
entry_lugar = ttkb.Entry(registro_frame, width=23)
entry_lugar.grid(row=2, column=1, padx=5, pady=5, sticky="w")

label_hora = ttkb.Label(registro_frame, text="Hora (HH:MM)")
label_hora.grid(row=3, column=0, padx=5, pady=5, sticky="w")
entry_hora = ttkb.Entry(registro_frame, width=23)
entry_hora.grid(row=3, column=1, padx=5, pady=5, sticky="w")

var_horarios_diferentes = tk.IntVar()
ttkb.Checkbutton(registro_frame, text="Usar horarios diferentes para cada día", variable=var_horarios_diferentes, command=mostrar_ocultar_horarios).grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

ttkb.Label(registro_frame, text="Duración").grid(row=5, column=0, padx=5, pady=5, sticky="w")
duracion_var = tk.IntVar()
duracion_menu = ttkb.Combobox(registro_frame, textvariable=duracion_var, width=20)
duracion_menu['values'] = (30, 45)
duracion_menu.grid(row=5, column=1, padx=5, pady=5, sticky="w")
duracion_menu.current(0)

var_todo_mes = tk.IntVar()
ttkb.Checkbutton(registro_frame, text="Agregar en todo el mes", variable=var_todo_mes).grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="w")

ttkb.Label(registro_frame, text="Días de la semana").grid(row=7, column=0, padx=5, pady=5, sticky="w")
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dias_vars = [tk.IntVar() for _ in dias]

for i, dia in enumerate(dias):
    ttkb.Checkbutton(registro_frame, text=dia, variable=dias_vars[i], command=actualizar_horarios).grid(row=8+i, column=0, padx=5, pady=5, sticky="w")
    entry_hora_dia = ttkb.Entry(registro_frame, width=23)
    entry_hora_dia.grid(row=8+i, column=1, padx=5, pady=5, sticky="w")
    entry_hora_dia.grid_remove()  # Ocultar inicialmente
    entry_horas.append(entry_hora_dia)

ttkb.Button(registro_frame, text="Añadir Clase", command=agregar_clase).grid(row=15, column=0, columnspan=2, padx=5, pady=5, sticky="w")

# Frame para el calendario
frame_calendario = ttkb.Frame(root, padding=20)
frame_calendario.pack(side="top", fill="both", expand=True)

# Frame para las clases
frame_clases = ttkb.Frame(root, padding=20)
frame_clases.pack(side="bottom", fill="both", expand=True)

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