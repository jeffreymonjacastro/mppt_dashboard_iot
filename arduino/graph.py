import serial
import time
import csv
import matplotlib.pyplot as plt
import pandas as pd
import os

PUERTO_SERIAL = '/dev/cu.usbmodem31401'
BAUD_RATE = 115200
NOMBRE_ARCHIVO = 'datos_mppt_filtrados.csv'

datos = []

print("--- INICIANDO LECTURA ---")

# 1. CAPTURA O CARGA CSV
try:
    print(f"Conectando a {PUERTO_SERIAL}...")
    ser = serial.Serial(PUERTO_SERIAL, BAUD_RATE, timeout=1)
    time.sleep(2)
    
    with open(NOMBRE_ARCHIVO, mode='w', newline='') as f:
        writer = csv.writer(f)
        print("Recibiendo datos...")

        while True:
            if ser.in_waiting > 0:
                linea = ser.readline().decode('utf-8', errors='ignore').strip()
                if not linea:
                    continue

                if "FIN" in linea:
                    print("FIN del experimento.")
                    break

                if "Duty" in linea:
                    writer.writerow(["Duty", "Voltaje", "Corriente"])
                    continue
                
                partes = linea.split(',')
                if len(partes) == 3:
                    try:
                        vals = [float(x) for x in partes]
                        writer.writerow(vals)
                        datos.append(vals)
                        print(vals, end='\r')
                    except:
                        pass

    ser.close()

except Exception as e:
    print(f"Modo offline: {e}")
    if os.path.exists(NOMBRE_ARCHIVO):
        print(f"Cargando archivo {NOMBRE_ARCHIVO}...")
        df_tmp = pd.read_csv(NOMBRE_ARCHIVO)
        datos = df_tmp.values.tolist()
    else:
        print("NO HAY DATOS")
        exit()

# 2. PROCESAR
if not datos:
    print("No hay datos.")
    exit()

df = pd.DataFrame(datos, columns=['Duty', 'Voltaje', 'Corriente'])
df["Potencia"] = df["Voltaje"] * df["Corriente"]

# 3. GRÁFICAS
plt.figure(figsize=(12, 10))

# --- (1) Corriente vs Voltaje ---
plt.subplot(2, 2, 1)
plt.plot(df["Voltaje"], df["Corriente"], '.-')
plt.title("Corriente vs Voltaje")
plt.xlabel("Voltaje (V)")
plt.ylabel("Corriente (A)")
plt.grid(True)

# --- (2) Potencia vs Voltaje ---
plt.subplot(2, 2, 2)
plt.plot(df["Voltaje"], df["Potencia"], '.-')
plt.title("Potencia vs Voltaje")
plt.xlabel("Voltaje (V)")
plt.ylabel("Potencia (W)")
plt.grid(True)

# --- (3) Voltaje vs Duty ---
plt.subplot(2, 2, 3)
plt.plot(df["Duty"], df["Voltaje"], '.-')
plt.title("Voltaje vs Duty")
plt.xlabel("Duty Cycle")
plt.ylabel("Voltaje (V)")
plt.grid(True)

# --- (4) Corriente vs Duty ---
plt.subplot(2, 2, 4)
plt.plot(df["Duty"], df["Corriente"], '.-')
plt.title("Corriente vs Duty")
plt.xlabel("Duty Cycle")
plt.ylabel("Corriente (A)")
plt.grid(True)

plt.tight_layout()
plt.show()
