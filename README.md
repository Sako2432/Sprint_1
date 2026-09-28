# Sprint 1 - Calidad del aire en Las Pintas (PIN)

## Descripción

Este repositorio contiene el procesamiento y análisis de los datos de calidad del aire de la estación **Las Pintas (PIN)** durante **marzo de 2024**.

El objetivo del Sprint fue transformar los datos horarios en indicadores que permitan interpretar la calidad del aire desde dos perspectivas: la evolución hora por hora y el resumen diario.

## Datos utilizados

La base utilizada es `BD_2024.xlsx`, descargada de la base histórica del Sistema de Monitoreo Atmosférico de Jalisco.

Para el análisis se trabajó principalmente con:

- PM10
- O3
- PM2.5 como variable adicional
- Temperatura externa
- Velocidad del viento
- Dirección del viento

La humedad relativa también se revisó, pero para la estación PIN no se encontraron datos disponibles durante marzo de 2024, por lo que se reportó como una limitación y no se inventaron valores.

## Estructura del repositorio

```text
Sprint1-Las-Pintas/
├── README.md
├── data/
│   └── BD_2024.xlsx
├── src/
│   └── analisis_las_pintas.py
├── resultados/
│   ├── datos_marzo_PIN.csv
│   └── resultados_diarios.csv
├── graficas/
│   ├── fig1_pm10_11mar.png
│   ├── fig2_o3_11mar.png
│   ├── fig3_temp_11mar.png
│   ├── fig4_wind_11mar.png
│   ├── fig5_diario_particulas.png
│   ├── fig6_categoria_diaria.png
│   └── fig7_dias_categoria.png
└── reporte/
    └── Sprint1_Las_Pintas.pdf
```

## Procesamiento

El script realiza los siguientes pasos:

1. Lee la base histórica de 2024.
2. Selecciona únicamente la estación Las Pintas (`PIN`).
3. Filtra marzo de 2024 y conserva el 29 de febrero solamente como contexto para las primeras ventanas de NowCast.
4. Convierte las variables a formato numérico y conserva los valores faltantes como datos ausentes.
5. Calcula NowCast para PM10 y PM2.5.
6. Asigna las categorías del Índice AIRE Y SALUD correspondientes a 2024.
7. Calcula los indicadores diarios cuando existe información suficiente.
8. Determina la categoría global y el contaminante dominante de cada día.
9. Genera los archivos CSV y las gráficas utilizadas en el reporte.

## Cómo ejecutar

Instalar las dependencias:

```bash
pip install pandas matplotlib openpyxl
```

Después ejecutar:

```bash
python src/analisis_las_pintas.py
```

La base `BD_2024.xlsx` debe encontrarse dentro de la carpeta `data/`.

## Resultados generales

Se analizaron **744 registros horarios**, correspondientes a los 31 días de marzo de 2024.

En el resumen diario se obtuvieron:

- 26 días con categoría **Mala**.
- 5 días con categoría **Muy mala**.

El análisis horario permite observar cambios dentro de un mismo día que se pierden cuando toda la información se resume en una sola categoría diaria.

## Limitaciones

No todas las variables meteorológicas tienen la misma disponibilidad. En particular, la humedad relativa no presentó datos para PIN durante marzo de 2024. Por esta razón, las relaciones entre meteorología y contaminantes se presentan como asociaciones descriptivas y no como relaciones causales.

## Fuentes

- Sistema de Monitoreo Atmosférico de Jalisco (SIMAJ).
- Sistema Nacional de Información de la Calidad del Aire (SINAICA).
- NOM-172-SEMARNAT-2023.
