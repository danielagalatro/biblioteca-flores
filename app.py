from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
# Esta "llave secreta" es obligatoria para que Flask pueda poner la pulserita VIP (session)
app.secret_key = "secreto_flores_2026" 

@app.route('/')
def inicio():
    # 1. Nos fijamos si el usuario escribió algo en el buscador (la variable 'q')
    busqueda = request.args.get('q')
    
    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    
    # 2. Si hay una búsqueda, filtramos. Si no, traemos todo.
    if busqueda:
        # En SQLite, los signos % significan "cualquier cosa antes o después"
        # Así, si buscan "bor", encuentra "Borges" o "Laboratorio"
        termino = f"%{busqueda}%"
        
        # Le pedimos que busque coincidencias tanto en el título como en el autor
        cursor.execute("SELECT * FROM Libros WHERE titulo LIKE ? OR autor LIKE ?", (termino, termino))
    else:
        cursor.execute("SELECT * FROM Libros")
        
    lista_libros = cursor.fetchall() 
    conexion.close()
    
    # 3. Le mandamos los libros (filtrados o todos) y la palabra que buscó para que quede en la barrita
    return render_template('index.html', libros=lista_libros, busqueda=busqueda)

@app.route('/nuevo')
def nuevo_libro():
    return render_template('nuevo_libro.html')

@app.route('/guardar', methods=['POST'])
def guardar_libro():
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
        cursor.execute('''
        INSERT INTO Libros (nro_inventario, titulo, autor, editorial, anio, signatura_topografica, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nro_inventario, titulo, autor, editorial, anio, signatura, observaciones))
        conexion.commit()
        conexion.close()
        return redirect('/')
    except sqlite3.IntegrityError:
        conexion.close()
        mensaje = f"Error: El Nro. de Inventario {nro_inventario} ya está en uso. Elegí otro para continuar."
        return render_template('nuevo_libro.html', error=mensaje)

# --- NUEVAS RUTAS DE SEGURIDAD ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        clave_ingresada = request.form['clave']
        if clave_ingresada == 'flores123': # Acá definimos la contraseña compartida
            session['admin'] = True # Le ponemos la pulserita VIP
            return redirect('/')
        else:
            return render_template('login.html', error="Clave incorrecta. Intentá de nuevo.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None) # Le sacamos la pulserita VIP
    return redirect('/')

@app.route('/borrar/<int:nro_inventario>')
def borrar_libro(nro_inventario):
    # Dimos de alta un guardia de seguridad: si NO tiene la pulserita, lo rebota al inicio
    if not session.get('admin'):
        return redirect('/')

    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM Libros WHERE nro_inventario = ?", (nro_inventario,))
    conexion.commit()
    conexion.close()
    return redirect('/')
@app.route('/editar/<int:nro_inventario>')
def editar_libro(nro_inventario):
    # Seguridad: si no tiene pulserita, lo pateamos al inicio
    if not session.get('admin'):
        return redirect('/')

    # Buscamos los datos actuales de ese libro específico
    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM Libros WHERE nro_inventario = ?", (nro_inventario,))
    libro_a_editar = cursor.fetchone() # fetchone trae uno solo
    conexion.close()

    # Le mandamos los datos al HTML para que llene los cuadraditos
    return render_template('editar_libro.html', libro=libro_a_editar)


@app.route('/actualizar/<int:nro_inventario>', methods=['POST'])
def actualizar_libro(nro_inventario):
    # Seguridad de nuevo por las dudas
    if not session.get('admin'):
        return redirect('/')

    # Atrapamos los datos corregidos y los limpiamos igual que en la carga nueva
    titulo = request.form['titulo'].strip().title()
    autor = request.form['autor'].strip().title()
    editorial = request.form['editorial'].strip().title() if request.form['editorial'] else ""
    anio = request.form['anio']
    signatura = request.form['signatura'].strip().upper()
    observaciones = request.form['observaciones']

    # Guardamos los cambios en la base de datos usando UPDATE en vez de INSERT
    conexion = sqlite3.connect("biblioteca.db")
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE Libros 
        SET titulo = ?, autor = ?, editorial = ?, anio = ?, signatura_topografica = ?, observaciones = ?
        WHERE nro_inventario = ?
    ''', (titulo, autor, editorial, anio, signatura, observaciones, nro_inventario))
    
    conexion.commit()
    conexion.close()

    return redirect('/')
if __name__ == '__main__':
    app.run(debug=True)