import tkinter as tk
from tkinter import ttk
import numpy as np
import os

# --- 1. CONFIGURACIÓN DEL GEMELO DIGITAL ---
FILENAME = "cmd_joints.txt"

# Límites de movimiento de las articulaciones (en grados)
JOINT_RANGES = [
    (-90, 90), (-50, 30), (-50, 120), (-90, 90), (-80, 80), (-50, 50)
]

# --- 2. SECUENCIA OPTIMIZADA DE RECOGER Y DEJAR (Valores Discretos de la Pinza) ---
# Formato: [J1, J2, J3, J4, J5, J6, Pinza]
# Pinza Abierta = 0.000  |  Pinza Cerrada = 0.020 
SEQUENCE = [
    {"desc": "1. Inicio / Posición Inicial", "pose": [0, 29, -72, 0, 0, 0, 0.000]},
    
    # --- FASE DE APROXIMACIÓN AL OBJETO A -90° ---
    {"desc": "2. Rotar a la Zona de Recogida (-90°)", "pose": [-90, 29, -72, 0, 0, 0, 0.000]},
    {"desc": "3. Descender hacia el Objeto", "pose": [-90, -19, -43, 0, 25, 0, 0.000]},
    {"desc": "3.1 Descender hacia el Objeto - Cerrar", "pose": [-90, -19, -43, 0, 34, 0, 0.020]},
    {"desc": "4. ¡Cerrar Pinza! (Recoger)", "pose": [-90, 25, -43, 0, 0, 0, 0.020]},
    
    # --- FASE DE LEVANTAMIENTO DE SEGURIDAD ---
    {"desc": "5. Levantar Brazo con Objeto", "pose": [-90, 30, -26, 0, 0, 0, 0.020]},
    
    # --- TRÁNSITO AÉREO SUAVE HACIA 90° ---
    {"desc": "6. Desplazamiento Aéreo Alto (-90° a 90°)", "pose": [90, 30, -26, 0, 0, 0, 0.020]},
    
    # --- FASE DE DESCARGA A 90° ---
    {"desc": "7. Descender sobre Zona de Descarga", "pose": [90, -30, -24, 0, 0, 0, 0.020]},
    {"desc": "8. ¡Abrir Pinza! (Dejar)", "pose": [90, -30, -24, 0, 30, 0, 0.000]},
    
    # --- RETRACCIÓN Y REGRESO ---
    {"desc": "9. Levantar y Despejar Zona", "pose": [90, 30, -26, 0, 0, 0, 0.000]},
    {"desc": "10. Regresar a Inicio", "pose": [0, 29, -72, 0, 0, 0, 0.000]}
]

# --- 3. CREACIÓN DE LA INTERFAZ GRÁFICA DE USUARIO (Tkinter) ---
root = tk.Tk()
root.title("Panel de Control - Niryo Ned2 SUAVE")
root.geometry("480x580")
root.configure(bg='#222222')

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#222222", font=("Arial", 11))

title_lbl = ttk.Label(root, text="Niryo Ned2 - Trayectoria Suave", font=("Arial", 14, "bold"))
title_lbl.pack(pady=15)

status_lbl = ttk.Label(root, text="Estado: Esperando comando...", font=("Arial", 11, "italic"), foreground="#00FF00")
status_lbl.pack(pady=5)

sliders = []
label_values = []

# Variable de estado interno para la pinza (Inicia abierta)
current_gripper_val = 0.000

def send_to_txt(*args):
    """Convierte las posiciones actuales de los deslizadores a radianes y escribe en el archivo MuJoCo"""
    rad_vals = []
    for i in range(6):
        deg = sliders[i].get()
        label_values[i].config(text=f"{int(deg)}°")
        rad_vals.append(np.radians(deg))
    
    # Inyectar valor actual de la pinza
    rad_vals.append(current_gripper_val)
    
    line = ",".join([f"{x:.6f}" for x in rad_vals])
    try:
        with open(FILENAME, "w") as f:
            f.write(line)
    except Exception:
        pass

# --- 4. MOTOR DE INTERPOLACIÓN DE MOVIMIENTO SUAVE ---
paso_secuencia_actual = 0
sub_paso_actual = 0
total_sub_pasos = 60  # Pasos intermedios (60 pasos @ 50FPS = 1.2 segundos de tránsito suave)
pose_inicial_tramo = []

def interpolar_movimiento():
    global sub_paso_actual, paso_secuencia_actual, pose_inicial_tramo, current_gripper_val
    
    if paso_secuencia_actual >= len(SEQUENCE):
        status_lbl.config(text="Estado: ¡Rutina de Recoger y Dejar Completada con Éxito!", foreground="#00FF00")
        btn_start.config(state="normal")
        btn_close_g.config(state="normal")
        btn_open_g.config(state="normal")
        return

    pose_objetivo = SEQUENCE[paso_secuencia_actual]["pose"]
    
    # Capturar estado inicial al comenzar un nuevo segmento de la secuencia
    if sub_paso_actual == 0:
        pose_inicial_tramo = [sliders[i].get() for i in range(6)] + [current_gripper_val]
        status_lbl.config(text=f"Ejecutando: {SEQUENCE[paso_secuencia_actual]['desc']}", foreground="#FFCC00")

    # Porcentaje de progreso actual (0.0 a 1.0)
    t = sub_paso_actual / total_sub_pasos
    
    # Interpolar los 6 ejes suavemente
    for i in range(6):
        val_interpolado = pose_inicial_tramo[i] + (pose_objetivo[i] - pose_inicial_tramo[i]) * t
        sliders[i].set(val_interpolado)
        
    # Interpolar el valor de la pinza
    current_gripper_val = pose_inicial_tramo[6] + (pose_objetivo[6] - pose_inicial_tramo[6]) * t
    
    # Actualizar indicador visual basado en la configuración del hardware
    if current_gripper_val >= 0.015:
        val_lbl_g.config(text="Cerrada")
    else:
        val_lbl_g.config(text="Abierta")
        
    send_to_txt()
    
    sub_paso_actual += 1
    
    if sub_paso_actual <= total_sub_pasos:
        root.after(20, interpolar_movimiento)
    else:
        sub_paso_actual = 0
        paso_secuencia_actual += 1
        # Pausa estática de 400ms en el destino para asegurar un agarre/liberación estable
        root.after(400, interpolar_movimiento)

def comenzar_rutina():
    global paso_secuencia_actual, sub_paso_actual
    btn_start.config(state="disabled")
    btn_close_g.config(state="disabled")
    btn_open_g.config(state="disabled")
    
    paso_secuencia_actual = 0
    sub_paso_actual = 0
    interpolar_movimiento()

# --- 5. VINCULAR DESLIZADORES EN LA INTERFAZ ---
joint_names = ["Articulación 1", "Articulación 2", "Articulación 3", "Articulación 4", "Articulación 5", "Articulación 6"]
for i in range(6):
    frame = tk.Frame(root, bg='#222222', pady=5)
    frame.pack(fill='x', padx=20)
    
    lbl = ttk.Label(frame, text=joint_names[i], width=12)
    lbl.pack(side='left')
    
    slider = tk.Scale(frame, from_=JOINT_RANGES[i][0], to=JOINT_RANGES[i][1], orient='horizontal', 
                      bg='#333333', fg='white', highlightbackground='#222222',
                      troughcolor='#555555', command=send_to_txt, resolution=0.1) # Decimales para mayor suavidad
    slider.set(SEQUENCE[0]["pose"][i])  
    slider.pack(side='left', fill='x', expand=True, padx=10)
    sliders.append(slider)
    
    val_lbl = ttk.Label(frame, text=f"{SEQUENCE[0]['pose'][i]}°", width=6)
    val_lbl.pack(side='right')
    label_values.append(val_lbl)

# --- 6. PANEL DE CONTROL DIRECTO DE LA PINZA (BOTONES MANUALES) ---
frame_g_ctrl = tk.Frame(root, bg='#222222', pady=15)
frame_g_ctrl.pack(fill='x', padx=20)

lbl_g_title = ttk.Label(frame_g_ctrl, text="Pinza:", width=10)
lbl_g_title.pack(side='left')

def manual_close_gripper():
    """Cambia manualmente el estado de la pinza a cerrada enviando 0.020 a MuJoCo"""
    global current_gripper_val
    current_gripper_val = 0.020
    val_lbl_g.config(text="Cerrada")
    send_to_txt()

def manual_open_gripper():
    """Cambia manualmente el estado de la pinza a abierta enviando 0.000 a MuJoCo"""
    global current_gripper_val
    current_gripper_val = 0.000
    val_lbl_g.config(text="Abierta")
    send_to_txt()

# Botones manuales de acción rápida para abrir y cerrar
btn_close_g = tk.Button(frame_g_ctrl, text="Cerrar Pinza", width=12, highlightbackground='#222222', command=manual_close_gripper)
btn_close_g.pack(side='left', padx=5, expand=True, fill='x')

btn_open_g = tk.Button(frame_g_ctrl, text="Abrir Pinza", width=12, highlightbackground='#222222', command=manual_open_gripper)
btn_open_g.pack(side='left', padx=5, expand=True, fill='x')

# Indicador de estado actual de la pinza en texto plano (Evita confusión numérica)
val_lbl_g = ttk.Label(frame_g_ctrl, text="Abierta", width=15, anchor="center")
val_lbl_g.pack(side='right', padx=5)

# --- 7. BOTÓN DE RUTINA AUTOMÁTICA ---
btn_start = tk.Button(root, text="▶ INICIAR RUTINA SUAVE", font=("Arial", 12, "bold"),
                      bg="#00AA55", fg="white", activebackground="#008844", activeforeground="white",
                      bd=0, padx=10, pady=10, command=comenzar_rutina)
btn_start.pack(pady=20)

def on_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Escribir los valores iniciales de arranque antes del bucle principal
send_to_txt()

root.mainloop()