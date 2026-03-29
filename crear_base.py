import sqlite3
import csv

def iniciar_sistema():
    print("Conectando con la base de datos...")
    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()

    # --- 1. TABLA LIBROS ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Libros (
        nro_inventario INTEGER PRIMARY KEY,
        titulo TEXT NOT NULL,
        autor TEXT NOT NULL,
        editorial TEXT,
        anio INTEGER,
        signatura_topografica TEXT NOT NULL,
        observaciones TEXT
    )
    ''')
    print("Tabla 'Libros' lista.")

    try:
        with open("libros.csv", mode="r", encoding="utf-8-sig") as archivo_libros:
            lector_libros = csv.DictReader(archivo_libros, delimiter=";")
            for fila in lector_libros:
                cursor.execute('''
                INSERT OR IGNORE INTO Libros 
                (nro_inventario, titulo, autor, editorial, anio, signatura_topografica, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (fila['nro_inventario'], fila['titulo'], fila['autor'], fila['editorial'], fila['anio'], fila['signatura_topografica'], fila['observaciones']))
            print("¡Éxito! Libros procesados.")
    except FileNotFoundError:
        print("Error: No encuentro 'libros.csv'.")


    # --- 2. TABLA SOCIOS ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Socios (
        id_socio INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_completo TEXT NOT NULL,
        telefono TEXT NOT NULL
    )
    ''')
    print("Tabla 'Socios' lista.")

    try:
        with open("socios.csv", mode="r", encoding="utf-8-sig") as archivo_socios:
            lector_socios = csv.DictReader(archivo_socios, delimiter=";")
            for fila in lector_socios:
                # Revisamos si el socio ya existe para no duplicarlo
                cursor.execute('SELECT id_socio FROM Socios WHERE nombre_completo = ?', (fila['nombre_completo'],))
                if cursor.fetchone() is None:
                    cursor.execute('''
                    INSERT INTO Socios (nombre_completo, telefono)
                    VALUES (?, ?)
                    ''', (fila['nombre_completo'], fila['telefono']))
            print("¡Éxito! Socios semilla cargados correctamente.")
    except FileNotFoundError:
        print("Error: No encuentro 'socios.csv'.")

    # Guardamos todo y cerramos
    conexion.commit()
    conexion.close()
    print("¡Base de datos de Flores Solidario 100% lista para usar!")

iniciar_sistema()