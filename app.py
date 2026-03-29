from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
# Esta "llave secreta" es obligatoria para que Flask pueda poner la pulserita VIP (session)
app.secret_key = "secreto_flores_2026" 

# --- NUEVO: CREACIÓN DE LAS DOS TABLAS ---
def inicializar_bd():
    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    
    # 1. Tabla de Obras (El texto, lleva el MFN)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Obras (
            mfn INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            editorial TEXT,
            anio TEXT
        )
    ''')
    
    # 2. Tabla de Ejemplares (El libro físico)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Ejemplares (
            nro_inventario INTEGER PRIMARY KEY,
            mfn_vinculado INTEGER,
            signatura_topografica TEXT NOT NULL,
            observaciones TEXT,
            FOREIGN KEY (mfn_vinculado) REFERENCES Obras (mfn)
        )
    ''')
    conexion.commit()
    conexion.close()

# Llamamos a la función para que cree las tablas ni bien arranca el programa
inicializar_bd()


@app.route('/')
def inicio():
    busqueda = request.args.get('q')
    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    
    # ACÁ ESTÁ EL CAMBIO: Agregamos o.mfn al final para que lo envíe al HTML
    consulta_base = '''
        SELECT e.nro_inventario, o.titulo, o.autor, o.editorial, o.anio, e.signatura_topografica, e.observaciones, o.mfn 
        FROM Ejemplares e
        JOIN Obras o ON e.mfn_vinculado = o.mfn
    '''
    
    if busqueda:
        termino = f"%{busqueda}%"
        consulta_base += " WHERE o.titulo LIKE ? OR o.autor LIKE ?"
        cursor.execute(consulta_base, (termino, termino))
    else:
        cursor.execute(consulta_base)
        
    lista_libros = cursor.fetchall() 
    conexion.close()
    
    return render_template('index.html', libros=lista_libros, busqueda=busqueda)
@app.route('/nuevo')
def nuevo_libro():
    return render_template('nuevo_libro.html')

@app.route('/guardar', methods=['POST'])
def guardar_libro():
    # ACÁ SACAMOS LA SEGURIDAD PARA QUE TODOS PUEDAN CARGAR
    nro_inventario = request.form['nro_inventario']
    titulo = request.form['titulo'].strip().title()
    autor = request.form['autor'].strip().title()
    editorial = request.form['editorial'].strip().title() if request.form['editorial'] else ""
    anio = request.form['anio']
    signatura = request.form['signatura'].strip().upper()
    observaciones = request.form['observaciones']

    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()

    try:
        # 1. Chequeamos que el Nro de inventario no exista para evitar el error feo
        cursor.execute("SELECT nro_inventario FROM Ejemplares WHERE nro_inventario = ?", (nro_inventario,))
        if cursor.fetchone():
            conexion.close()
            return render_template('nuevo_libro.html', error=f"Error: El Nro. de Inventario {nro_inventario} ya está en uso. Elegí otro.")

        # 2. LÓGICA MFN: Buscamos si la obra ya existe comparando Título y Autor
        cursor.execute("SELECT mfn FROM Obras WHERE LOWER(titulo) = LOWER(?) AND LOWER(autor) = LOWER(?)", (titulo, autor))
        obra_existente = cursor.fetchone()

        if obra_existente:
            mfn_asignado = obra_existente[0] # Ya la tenemos, usamos su MFN
        else:
            # Es un libro nuevo, creamos la ficha de la Obra
            cursor.execute('''
                INSERT INTO Obras (titulo, autor, editorial, anio)
                VALUES (?, ?, ?, ?)
            ''', (titulo, autor, editorial, anio))
            mfn_asignado = cursor.lastrowid # Atrapamos el MFN que recién se creó

        # 3. Guardamos el ejemplar físico apuntando a ese MFN
        cursor.execute('''
            INSERT INTO Ejemplares (nro_inventario, mfn_vinculado, signatura_topografica, observaciones)
            VALUES (?, ?, ?, ?)
        ''', (nro_inventario, mfn_asignado, signatura, observaciones))
        
        conexion.commit()
        conexion.close()
        return redirect('/')
        
    except Exception as e:
        conexion.close()
        return render_template('nuevo_libro.html', error=f"Ocurrió un error: {str(e)}")
# --- RUTAS DE SEGURIDAD ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        clave_ingresada = request.form['clave']
        if clave_ingresada == 'flores123': 
            session['admin'] = True 
            return redirect('/')
        else:
            return render_template('login.html', error="Clave incorrecta. Intentá de nuevo.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None) 
    return redirect('/')

@app.route('/borrar/<int:nro_inventario>')
def borrar_libro(nro_inventario):
    if not session.get('admin'):
        return redirect('/')

    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    
    # Buscamos a qué MFN pertenece antes de borrar el ejemplar
    cursor.execute("SELECT mfn_vinculado FROM Ejemplares WHERE nro_inventario = ?", (nro_inventario,))
    resultado = cursor.fetchone()
    
    if resultado:
        mfn = resultado[0]
        cursor.execute("DELETE FROM Ejemplares WHERE nro_inventario = ?", (nro_inventario,))
        
        # Limpieza: Si no quedan más ejemplares de esta obra, borramos la obra también
        cursor.execute("SELECT COUNT(*) FROM Ejemplares WHERE mfn_vinculado = ?", (mfn,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("DELETE FROM Obras WHERE mfn = ?", (mfn,))
            
        conexion.commit()
        
    conexion.close()
    return redirect('/')

@app.route('/editar/<int:nro_inventario>')
def editar_libro(nro_inventario):
    if not session.get('admin'):
        return redirect('/')

    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    # Traemos los datos unidos para llenar el formulario
    cursor.execute('''
        SELECT e.nro_inventario, o.titulo, o.autor, o.editorial, o.anio, e.signatura_topografica, e.observaciones 
        FROM Ejemplares e
        JOIN Obras o ON e.mfn_vinculado = o.mfn
        WHERE e.nro_inventario = ?
    ''', (nro_inventario,))
    libro_a_editar = cursor.fetchone() 
    conexion.close()

    return render_template('editar_libro.html', libro=libro_a_editar)


@app.route('/actualizar/<int:nro_inventario>', methods=['POST'])
def actualizar_libro(nro_inventario):
    if not session.get('admin'):
        return redirect('/')

    titulo = request.form['titulo'].strip().title()
    autor = request.form['autor'].strip().title()
    editorial = request.form['editorial'].strip().title() if request.form['editorial'] else ""
    anio = request.form['anio']
    signatura = request.form['signatura'].strip().upper()
    observaciones = request.form['observaciones']

    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    
    # Buscamos qué MFN le corresponde a este ejemplar
    cursor.execute("SELECT mfn_vinculado FROM Ejemplares WHERE nro_inventario = ?", (nro_inventario,))
    mfn = cursor.fetchone()[0]

    # Actualizamos los datos de la Obra (Esto corrige errores de tipeo para todos los ejemplares de este libro)
    cursor.execute('''
        UPDATE Obras 
        SET titulo = ?, autor = ?, editorial = ?, anio = ?
        WHERE mfn = ?
    ''', (titulo, autor, editorial, anio, mfn))
    
    # Actualizamos los datos propios de este ejemplar
    cursor.execute('''
        UPDATE Ejemplares 
        SET signatura_topografica = ?, observaciones = ?
        WHERE nro_inventario = ?
    ''', (signatura, observaciones, nro_inventario))
    
    conexion.commit()
    conexion.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)