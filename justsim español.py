import tkinter as tk
from tkinter import ttk
import numpy as np
import os

# --- 1. CONFIGURACIÓN DEL GEMELO DIGITAL ---
FILENAME = "cmd_joints.txt"

# Postura inicial predeterminada para el simulador (en grados)
INITIAL_POSE_DEG = [0, 29, -72, 0, 0, 0]

# Límites de movimiento de las articulaciones (en grados)
JOINT_RANGES = [
    (-90, 90),    # Articulación 1
    (-50, 30),    # Articulación 2
    (-50, 120),   # Articulación 3
    (-90, 90),    # Articulación 4
    (-80, 80),    # Articulación 5
    (-50, 50)     # Articulación 6
]

# --- 2. CREACIÓN DE LA INTERFAZ GRÁFICA DE USUARIO (Tkinter) ---
root = tk.Tk()
root.title("Panel de Control - Gemelo Digital Niryo (Simulación)")
root.geometry("480x520")
root.configure(bg='#222222')

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#222222", font=("Arial", 11))

title_lbl = ttk.Label(root, text="Control del Gemelo Digital (MuJoCo)", font=("Arial", 14, "bold"))
title_lbl.pack(pady=15)

sliders = []
label_values = []

# Variable global oculta para retener el estado de la pinza (0.020 = Cerrada por defecto en este mapeo independiente)
current_gripper_val = 0.020

def send_to_txt(*args):
    """Convierte los valores de los deslizadores a radianes y actualiza el archivo de texto de MuJoCo"""
    rad_vals = []
    
    # Procesar las 6 articulaciones del brazo
    for i in range(6):
        deg = sliders[i].get()
        label_values[i].config(text=f"{int(deg)}°")
        rad_vals.append(np.radians(deg))
    
    # Añadir el valor actual de la pinza determinado por los botones
    rad_vals.append(current_gripper_val)
    
    # Formatear una sola línea separada por comas para el analizador de MuJoCo
    line = ",".join([f"{x:.6f}" for x in rad_vals])
    try:
        with open(FILENAME, "w") as f:
            f.write(line)
    except Exception as e:
        print(f"Error al escribir en el archivo de simulación: {e}")

# Crear deslizadores para las 6 articulaciones
joint_names = ["Articulación 1", "Articulación 2", "Articulación 3", "Articulación 4", "Articulación 5", "Articulación 6"]
for i in range(6):
    frame = tk.Frame(root, bg='#222222', pady=5)
    frame.pack(fill='x', padx=20)
    
    lbl = ttk.Label(frame, text=joint_names[i], width=12)
    lbl.pack(side='left')
    
    slider = tk.Scale(frame, from_=JOINT_RANGES[i][0], to=JOINT_RANGES[i][1], orient='horizontal', 
                      bg='#333333', fg='white', highlightbackground='#222222',
                      troughcolor='#555555', command=send_to_txt)
    
    slider.set(INITIAL_POSE_DEG[i])  
    slider.pack(side='left', fill='x', expand=True, padx=10)
    sliders.append(slider)
    
    val_lbl = ttk.Label(frame, text=f"{INITIAL_POSE_DEG[i]}°", width=6)
    val_lbl.pack(side='right')
    label_values.append(val_lbl)

# --- 3. PANEL DE CONTROL DISCRETO DE LA PINZA ---
frame_g_ctrl = tk.Frame(root, bg='#222222', pady=15)
frame_g_ctrl.pack(fill='x', padx=20)

lbl_g_title = ttk.Label(frame_g_ctrl, text="Pinza:", width=10)
lbl_g_title.pack(side='left')

def close_gripper():
    """Modifica el estado de la pinza a cerrada (0.020) y actualiza el archivo txt"""
    global current_gripper_val
    current_gripper_val = 0.020
    val_lbl_g.config(text="0.020 (Cerrada)")
    send_to_txt()

def open_gripper():
    """Modifica el estado de la pinza a abierta (0.000) y actualiza el archivo txt"""
    global current_gripper_val
    current_gripper_val = 0.000
    val_lbl_g.config(text="0.000 (Abierta)")
    send_to_txt()

# Botones de acción para abrir y cerrar la pinza
btn_close_g = tk.Button(frame_g_ctrl, text="Cerrar Pinza", width=12, highlightbackground='#222222', command=close_gripper)
btn_close_g.pack(side='left', padx=5, expand=True, fill='x')

btn_open_g = tk.Button(frame_g_ctrl, text="Abrir Pinza", width=12, highlightbackground='#222222', command=open_gripper)
btn_open_g.pack(side='left', padx=5, expand=True, fill='x')

# Indicador del estado actual de la pinza (Inicializado para coincidir con el texto de respaldo de current_gripper_val)
val_lbl_g = ttk.Label(frame_g_ctrl, text="0.020 (Cerrada)", width=15, anchor="center")
val_lbl_g.pack(side='right', padx=5)

# --- 4. CIERRE SEGURO Y ARRANQUE ---
def on_close():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

# Escribir los valores de configuración iniciales en el archivo de texto al iniciar la interfaz
send_to_txt()

root.mainloop()