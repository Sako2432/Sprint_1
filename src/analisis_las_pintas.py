"""
Sprint 1 - Calidad del aire, estación Las Pintas (PIN), marzo de 2024.

Entrada esperada:
    data/BD_2024.xlsx

Salidas:
    resultados/datos_marzo_PIN.csv
    resultados/resultados_diarios.csv
    graficas/*.png

Dependencias:
    pip install pandas matplotlib openpyxl
"""

from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
ARCHIVO = BASE / "data" / "BD_2024.xlsx"
OUT = BASE / "resultados"
GRAF = BASE / "graficas"
OUT.mkdir(exist_ok=True)
GRAF.mkdir(exist_ok=True)

RANK = {
    "Buena": 1,
    "Aceptable": 2,
    "Mala": 3,
    "Muy mala": 4,
    "Extremadamente mala": 5,
}


def nowcast(valores, pm):
    """
    NowCast con la lógica del código de referencia proporcionado en clase.

    valores: hasta 12 concentraciones, de la más antigua a la más reciente.
    pm: 0 = PM10, 1 = PM2.5.
    """
    ultimas_3 = valores[-3:] if len(valores) >= 3 else valores
    if sum(x is not None and not pd.isna(x) for x in ultimas_3) < 2:
        return None

    datos = []
    for edad, valor in enumerate(reversed(valores)):
        if valor is not None and not pd.isna(valor):
            datos.append((float(valor), edad))

    if len(datos) < 2:
        return None

    solo = [v for v, _ in datos]
    maximo = max(solo)
    minimo = min(solo)
    w_raw = round(1 - ((maximo - minimo) / maximo), 2) if maximo > 0 else 0.5
    w = max(w_raw, 0.5)

    numerador = sum(v * (w ** edad) for v, edad in datos)
    denominador = sum(w ** edad for _, edad in datos)
    if denominador == 0:
        return None

    promedio = round(numerador / denominador, 0)

    # Factores usados por el código de referencia de la actividad.
    factor = 0.714 if pm == 0 else 0.694
    return int(round(promedio * factor, 0))


def categoria_pm10_2024(valor):
    """Bandas aplicables a PM10 durante 2024."""
    if pd.isna(valor):
        return None
    if valor <= 45:
        return "Buena"
    if valor <= 60:
        return "Aceptable"
    if valor <= 132:
        return "Mala"
    if valor <= 213:
        return "Muy mala"
    return "Extremadamente mala"


def categoria_pm25_2024(valor):
    """Bandas aplicables a PM2.5 durante 2024."""
    if pd.isna(valor):
        return None
    if valor <= 15:
        return "Buena"
    if valor <= 33:
        return "Aceptable"
    if valor <= 79:
        return "Mala"
    if valor <= 130:
        return "Muy mala"
    return "Extremadamente mala"


def categoria_o3(valor):
    if pd.isna(valor):
        return None
    valor = round(float(valor), 3)
    if valor <= 0.058:
        return "Buena"
    if valor <= 0.090:
        return "Aceptable"
    if valor <= 0.135:
        return "Mala"
    if valor <= 0.175:
        return "Muy mala"
    return "Extremadamente mala"


def categoria_global(pares):
    pares = [(p, c) for p, c in pares if c is not None]
    if not pares:
        return None, None
    peor = max(RANK[c] for _, c in pares)
    categoria = next(c for _, c in pares if RANK[c] == peor)
    dominantes = "/".join(p for p, c in pares if RANK[c] == peor)
    return categoria, dominantes


# --------------------------
# 1. Carga y preparación
# --------------------------
df = pd.read_excel(ARCHIVO, sheet_name="Data")
df.columns = [str(c).strip() for c in df.columns]

# Convertir las variables a número; valores inválidos se vuelven NaN.
variables = [
    "O3", "NO", "NO2", "NOX", "SO2", "CO", "PM10", "PM2.5",
    "IT", "ET", "RH", "WS", "WD", "PP", "ATM", "RS", "UVI"
]
for col in variables:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["HOUR"] = pd.to_numeric(df["HOUR"], errors="coerce")
df["DIA"] = pd.to_numeric(df["DIA"], errors="coerce")
df["MES"] = pd.to_numeric(df["MES"], errors="coerce")

# Se conserva el 29 de febrero como contexto para el NowCast de las primeras horas de marzo.
pin_contexto = df[
    (df["STATION"].astype(str).str.strip() == "PIN")
    & (
        (df["MES"] == 3)
        | ((df["MES"] == 2) & (df["DIA"] == 29))
    )
].copy()

pin_contexto["fecha_hora"] = pd.to_datetime(
    {
        "year": 2024,
        "month": pin_contexto["MES"].astype(int),
        "day": pin_contexto["DIA"].astype(int),
        "hour": pin_contexto["HOUR"].astype(int),
    }
)
pin_contexto = pin_contexto.sort_values("fecha_hora").reset_index(drop=True)

# --------------------------
# 2. Indicadores horarios
# --------------------------
pm10_nowcast = []
pm25_nowcast = []

for i in range(len(pin_contexto)):
    ventana = pin_contexto.iloc[max(0, i - 11): i + 1]
    pm10_nowcast.append(nowcast(ventana["PM10"].tolist(), 0))
    pm25_nowcast.append(nowcast(ventana["PM2.5"].tolist(), 1))

pin_contexto["PM10_NowCast"] = pm10_nowcast
pin_contexto["PM2_5_NowCast"] = pm25_nowcast

pin_contexto["categoria_PM10_horaria"] = pin_contexto["PM10_NowCast"].apply(categoria_pm10_2024)
pin_contexto["categoria_PM2_5_horaria"] = pin_contexto["PM2_5_NowCast"].apply(categoria_pm25_2024)
pin_contexto["categoria_O3_horaria"] = pin_contexto["O3"].apply(categoria_o3)

globales = pin_contexto.apply(
    lambda r: categoria_global([
        ("PM10", r["categoria_PM10_horaria"]),
        ("PM2.5", r["categoria_PM2_5_horaria"]),
        ("O3", r["categoria_O3_horaria"]),
    ]),
    axis=1,
)
pin_contexto["categoria_global_horaria"] = [x[0] for x in globales]
pin_contexto["contaminante_dominante_horario"] = [x[1] for x in globales]

marzo = pin_contexto[pin_contexto["MES"] == 3].copy()
marzo["fecha"] = marzo["fecha_hora"].dt.date

# Guardar datos horarios procesados.
columnas_horarias = [
    "fecha_hora", "fecha", "HOUR", "STATION",
    "O3", "PM10", "PM2.5", "ET", "IT", "RH", "WS", "WD", "PP", "ATM", "RS",
    "PM10_NowCast", "PM2_5_NowCast",
    "categoria_PM10_horaria", "categoria_PM2_5_horaria", "categoria_O3_horaria",
    "categoria_global_horaria", "contaminante_dominante_horario",
]
marzo[columnas_horarias].to_csv(
    OUT / "datos_marzo_PIN.csv", index=False, encoding="utf-8-sig"
)

# --------------------------
# 3. Resultados diarios
# --------------------------
filas_diarias = []

for fecha, grupo in marzo.groupby("fecha"):
    o3 = grupo["O3"].dropna()
    pm10 = grupo["PM10"].dropna()
    pm25 = grupo["PM2.5"].dropna()

    # Se requiere al menos 75 % de las 24 horas (18 datos válidos).
    o3_max = o3.max() if len(o3) >= 18 else np.nan
    pm10_24 = round(pm10.mean(), 0) if len(pm10) >= 18 else np.nan
    pm25_24 = round(pm25.mean(), 0) if len(pm25) >= 18 else np.nan

    c_o3 = categoria_o3(o3_max)
    c_pm10 = categoria_pm10_2024(pm10_24)
    c_pm25 = categoria_pm25_2024(pm25_24)

    c_global, dominante = categoria_global([
        ("PM10", c_pm10),
        ("PM2.5", c_pm25),
        ("O3", c_o3),
    ])

    filas_diarias.append({
        "fecha": fecha,
        "horas_validas_O3": len(o3),
        "O3_max_1h_ppm": o3_max,
        "categoria_O3": c_o3,
        "horas_validas_PM10": len(pm10),
        "PM10_promedio_24h_ug_m3": pm10_24,
        "categoria_PM10": c_pm10,
        "horas_validas_PM2_5": len(pm25),
        "PM2_5_promedio_24h_ug_m3": pm25_24,
        "categoria_PM2_5": c_pm25,
        "categoria_global": c_global,
        "contaminante_dominante": dominante,
        "temperatura_externa_media_C": grupo["ET"].mean(),
        "velocidad_viento_media": grupo["WS"].mean(),
        "direccion_viento_media_grados": grupo["WD"].mean(),
    })

diario = pd.DataFrame(filas_diarias)
diario.to_csv(OUT / "resultados_diarios.csv", index=False, encoding="utf-8-sig")

# --------------------------
# 4. Gráficas
# --------------------------
rep = marzo[marzo["fecha_hora"].dt.date == pd.Timestamp("2024-03-11").date()]
horas = rep["HOUR"]

plt.figure(figsize=(9, 4.2))
plt.plot(horas, rep["PM10"], marker="o", label="PM10 horario")
plt.plot(horas, rep["PM10_NowCast"], marker="o", label="NowCast PM10")
plt.xlabel("Hora")
plt.ylabel("µg/m³")
plt.title("Las Pintas - PM10 horario y NowCast, 11 de marzo de 2024")
plt.xticks(range(0, 24, 2))
plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()
plt.savefig(GRAF / "fig1_pm10_11mar.png", dpi=180)
plt.close()

plt.figure(figsize=(9, 4.2))
plt.plot(horas, rep["O3"], marker="o")
plt.xlabel("Hora")
plt.ylabel("ppm")
plt.title("Las Pintas - O3 horario, 11 de marzo de 2024")
plt.xticks(range(0, 24, 2))
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(GRAF / "fig2_o3_11mar.png", dpi=180)
plt.close()

plt.figure(figsize=(9, 4.2))
plt.plot(horas, rep["ET"], marker="o")
plt.xlabel("Hora")
plt.ylabel("°C")
plt.title("Las Pintas - Temperatura externa disponible, 11 de marzo de 2024")
plt.xticks(range(0, 24, 2))
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(GRAF / "fig3_temp_11mar.png", dpi=180)
plt.close()

plt.figure(figsize=(9, 4.2))
plt.plot(horas, rep["WS"], marker="o")
plt.xlabel("Hora")
plt.ylabel("Velocidad del viento")
plt.title("Las Pintas - Velocidad del viento disponible, 11 de marzo de 2024")
plt.xticks(range(0, 24, 2))
plt.grid(alpha=0.25)
plt.tight_layout()
plt.savefig(GRAF / "fig4_wind_11mar.png", dpi=180)
plt.close()

dias = pd.to_datetime(diario["fecha"]).dt.day

plt.figure(figsize=(9, 4.5))
plt.plot(dias, diario["PM10_promedio_24h_ug_m3"], marker="o", label="PM10 promedio 24 h")
plt.plot(dias, diario["PM2_5_promedio_24h_ug_m3"], marker="o", label="PM2.5 promedio 24 h")
plt.xlabel("Día de marzo")
plt.ylabel("µg/m³")
plt.title("Las Pintas - Promedios diarios de partículas, marzo 2024")
plt.xticks(range(1, 32, 2))
plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()
plt.savefig(GRAF / "fig5_diario_particulas.png", dpi=180)
plt.close()

orden = ["Buena", "Aceptable", "Mala", "Muy mala", "Extremadamente mala"]

plt.figure(figsize=(10, 4.5))
y = diario["categoria_global"].map(RANK)
plt.plot(dias, y, marker="o")
plt.xlabel("Día de marzo")
plt.ylabel("Categoría global")
plt.yticks(range(1, 6), orden)
plt.xticks(range(1, 32))
plt.ylim(0.5, 5.5)
plt.title("Las Pintas - Categoría diaria, marzo 2024")
plt.grid(axis="y", alpha=0.25)
plt.tight_layout()
plt.savefig(GRAF / "fig6_categoria_diaria.png", dpi=180)
plt.close()

conteo = Counter(diario["categoria_global"].dropna())
plt.figure(figsize=(7, 4.2))
plt.bar(orden, [conteo.get(x, 0) for x in orden])
plt.ylabel("Número de días")
plt.title("Días por categoría global - Las Pintas, marzo 2024")
plt.xticks(rotation=25, ha="right")
plt.tight_layout()
plt.savefig(GRAF / "fig7_dias_categoria.png", dpi=180)
plt.close()

print("Proceso terminado.")
print(f"Registros horarios de marzo: {len(marzo)}")
print(f"Días analizados: {len(diario)}")
print(diario["categoria_global"].value_counts())
