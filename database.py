import sqlite3
import json
import os
from contextlib import contextmanager
import streamlit as st

DATABASE_PATH = "inventario.db"

@contextmanager
def get_db_connection():
    """Context manager para conexiones a base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error en base de datos: {e}")
        raise
    finally:
        conn.close()

def inicializar_bd():
    """Inicializa la base de datos con las tablas necesarias"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Tabla de Estados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS estados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tabla de Ciudades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ciudades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                estado_id INTEGER NOT NULL,
                FOREIGN KEY (estado_id) REFERENCES estados(id),
                UNIQUE(nombre, estado_id)
            )
        ''')
        
        # Tabla de Planteles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planteles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ciudad_id INTEGER NOT NULL,
                FOREIGN KEY (ciudad_id) REFERENCES ciudades(id),
                UNIQUE(nombre, ciudad_id)
            )
        ''')
        
        # Tabla de Edificios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS edificios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                plantel_id INTEGER NOT NULL,
                FOREIGN KEY (plantel_id) REFERENCES planteles(id),
                UNIQUE(nombre, plantel_id)
            )
        ''')
        
        # Tabla de Cubículos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cubiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                edificio_id INTEGER NOT NULL,
                FOREIGN KEY (edificio_id) REFERENCES edificios(id),
                UNIQUE(nombre, edificio_id)
            )
        ''')
        
        # Tabla de Encargados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS encargados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                correo TEXT,
                telefono TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de Empleados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                correo TEXT,
                telefono TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de Tipos de Activos (categorías generales)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tipos_activos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                descripcion TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de Modelos de Activos (variantes técnicas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS modelos_activos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo_activo_id INTEGER NOT NULL REFERENCES tipos_activos(id),
                nombre TEXT NOT NULL,
                descripcion TEXT,
                especificaciones TEXT
            )
        ''')
        
        # Tabla de Activos (instancias físicas en inventario)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activos (
                numero_inventario TEXT PRIMARY KEY,
                clave TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                clave_activo TEXT,
                descripcion_activo TEXT,
                tipo_activo_id INTEGER REFERENCES tipos_activos(id),
                modelo_activo_id INTEGER REFERENCES modelos_activos(id),
                empleado_id INTEGER REFERENCES empleados(id),
                encargado_id INTEGER REFERENCES encargados(id),
                cubiculo_id INTEGER REFERENCES cubiculos(id),
                presente BOOLEAN DEFAULT 0,
                cantidad INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Añadir columna cantidad si no existe (para compatibilidad)
        try:
            cursor.execute("ALTER TABLE activos ADD COLUMN cantidad INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # La columna ya existe

        conn.commit()

def agregar_o_obtener_estado(nombre):
    """Agrega un estado si no existe, retorna su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM estados WHERE nombre = ?", (nombre,))
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado['id']
        
        cursor.execute("INSERT INTO estados (nombre) VALUES (?)", (nombre,))
        return cursor.lastrowid

def agregar_o_obtener_ciudad(nombre, estado_id):
    """Agrega una ciudad si no existe, retorna su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (nombre, estado_id))
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado['id']
        
        cursor.execute("INSERT INTO ciudades (nombre, estado_id) VALUES (?, ?)", (nombre, estado_id))
        return cursor.lastrowid

def agregar_o_obtener_plantel(nombre, ciudad_id):
    """Agrega un plantel si no existe, retorna su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (nombre, ciudad_id))
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado['id']
        
        cursor.execute("INSERT INTO planteles (nombre, ciudad_id) VALUES (?, ?)", (nombre, ciudad_id))
        return cursor.lastrowid

def agregar_o_obtener_edificio(nombre, plantel_id):
    """Agrega un edificio si no existe, retorna su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM edificios WHERE nombre = ? AND plantel_id = ?", (nombre, plantel_id))
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado['id']
        
        cursor.execute("INSERT INTO edificios (nombre, plantel_id) VALUES (?, ?)", (nombre, plantel_id))
        return cursor.lastrowid

def agregar_o_obtener_cubiculo(nombre, edificio_id):
    """Agrega un cubículo si no existe, retorna su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cubiculos WHERE nombre = ? AND edificio_id = ?", (nombre, edificio_id))
        resultado = cursor.fetchone()
        
        if resultado:
            return resultado['id']
        
        cursor.execute("INSERT INTO cubiculos (nombre, edificio_id) VALUES (?, ?)", (nombre, edificio_id))
        return cursor.lastrowid

def obtener_nombre_cubiculo(cubiculo_id):
    """Obtiene el nombre de un cubículo por su ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM cubiculos WHERE id = ?", (cubiculo_id,))
        resultado = cursor.fetchone()
        return resultado['nombre'] if resultado else None

def obtener_ruta_id(ruta_componentes):
    """Obtiene el ID del cubículo según la ruta de componentes"""
    if not ruta_componentes:
        return None
    
    estado_id = agregar_o_obtener_estado(ruta_componentes[0])
    
    if len(ruta_componentes) > 1:
        ciudad_id = agregar_o_obtener_ciudad(ruta_componentes[1], estado_id)
    else:
        return None
    
    if len(ruta_componentes) > 2:
        plantel_id = agregar_o_obtener_plantel(ruta_componentes[2], ciudad_id)
    else:
        return None
    
    if len(ruta_componentes) > 3:
        edificio_id = agregar_o_obtener_edificio(ruta_componentes[3], plantel_id)
    else:
        return None
    
    if len(ruta_componentes) > 4:
        cubiculo_id = agregar_o_obtener_cubiculo(ruta_componentes[4], edificio_id)
        return cubiculo_id
    
    return None

def guardar_activo(clave_activo, descripcion_activo, empleado_id, encargado_id, cubiculo_id, presente=0, tipo_activo_id=None, cantidad=1):
    """Asigna un activo insertando una nueva instancia en la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Generar numero_inventario único
        cursor.execute("SELECT MAX(CAST(numero_inventario AS INTEGER)) AS max_inv FROM activos WHERE numero_inventario GLOB '[0-9]*'")
        row = cursor.fetchone()
        siguiente_numero = (row["max_inv"] or 0) + 1
        numero_inventario = f"{siguiente_numero:011d}"
        
        cursor.execute('''
            INSERT INTO activos (numero_inventario, clave, clave_activo, descripcion, descripcion_activo, tipo_activo_id, empleado_id, encargado_id, cubiculo_id, presente, cantidad)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (numero_inventario, clave_activo, clave_activo, descripcion_activo, descripcion_activo, tipo_activo_id, empleado_id, encargado_id, cubiculo_id, presente, cantidad))
        
        return numero_inventario

def actualizar_activo_asignado(numero_inventario, empleado_id=None, encargado_id=None, presente=None, cantidad=None, descripcion=None):
    """Actualiza un activo asignado en la base de datos"""
    fields = []
    params = []

    if empleado_id is not None:
        fields.append("empleado_id = ?")
        params.append(empleado_id)
    if encargado_id is not None:
        fields.append("encargado_id = ?")
        params.append(encargado_id)
    if presente is not None:
        fields.append("presente = ?")
        params.append(presente)
    if cantidad is not None:
        fields.append("cantidad = ?")
        params.append(cantidad)
    if descripcion is not None:
        fields.append("descripcion = ?")
        params.append(descripcion)
        fields.append("descripcion_activo = ?")
        params.append(descripcion)

    if not fields:
        return

    fields.append("fecha_modificacion = CURRENT_TIMESTAMP")
    query = f"UPDATE activos SET {', '.join(fields)} WHERE numero_inventario = ?"
    params.append(numero_inventario)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))

@st.cache_data
def cargar_activos_cubiculo(cubiculo_id):
    """Carga todos los activos de un cubículo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.clave AS clave_activo,
                   COALESCE(base.descripcion, d.descripcion_activo) AS descripcion_activo,
                   d.numero_inventario,
                   e.nombre AS empleado_nombre,
                   enc.nombre AS encargado_nombre,
                   d.presente, d.cantidad
            FROM activos d
            LEFT JOIN activos base ON d.clave_activo = base.clave AND base.cubiculo_id IS NULL
            LEFT JOIN empleados e ON d.empleado_id = e.id
            LEFT JOIN encargados enc ON d.encargado_id = enc.id
            WHERE d.cubiculo_id = ?
        ''', (cubiculo_id,))
        
        activos = []
        for row in cursor.fetchall():
            activo = dict(row)
            activos.append(activo)
        
        return activos

def eliminar_activo_asignado(numero_inventario):
    """Elimina un activo asignado de la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activos WHERE numero_inventario = ?", (numero_inventario,))

def buscar_activos(ruta_parcial=[]):
    """Busca activos según una ruta parcial (incluyendo cubículos)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT d.*, 
                   c.nombre as cubiculo_nombre,
                   e.nombre as edificio_nombre,
                   p.nombre as plantel_nombre,
                   ci.nombre as ciudad_nombre,
                   es.nombre as estado_nombre
            FROM activos d
            JOIN cubiculos c ON d.cubiculo_id = c.id
            JOIN edificios e ON c.edificio_id = e.id
            JOIN planteles p ON e.plantel_id = p.id
            JOIN ciudades ci ON p.ciudad_id = ci.id
            JOIN estados es ON ci.estado_id = es.id
        '''
        
        params = []
        conditions = []
        
        if len(ruta_parcial) > 0:
            conditions.append("es.nombre = ?")
            params.append(ruta_parcial[0])
        
        if len(ruta_parcial) > 1:
            conditions.append("ci.nombre = ?")
            params.append(ruta_parcial[1])
        
        if len(ruta_parcial) > 2:
            conditions.append("p.nombre = ?")
            params.append(ruta_parcial[2])
        
        if len(ruta_parcial) > 3:
            conditions.append("e.nombre = ?")
            params.append(ruta_parcial[3])
        
        if len(ruta_parcial) > 4:
            conditions.append("c.nombre = ?")
            params.append(ruta_parcial[4])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor.execute(query, params)
        
        activos = []
        for row in cursor.fetchall():
            activo = dict(row)
            activo['ubicacion'] = " > ".join([
                activo['estado_nombre'],
                activo['ciudad_nombre'],
                activo['plantel_nombre'],
                activo['edificio_nombre'],
                activo['cubiculo_nombre']
            ])
            activos.append(activo)
        
        return activos

def buscar_activos_por_criterios(texto_busqueda="", encargado=None, empleado=None, ruta_parcial=[], tipo_activo_id=None):
    """Busca activos por texto, encargado, empleado, tipo y/o ruta jerárquica"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT d.*, 
                   COALESCE(base.descripcion, d.descripcion_activo) AS descripcion_activo,
                   COALESCE(base.tipo_activo_id, d.tipo_activo_id) AS tipo_activo_id,
                   c.nombre as cubiculo_nombre,
                   e.nombre as edificio_nombre,
                   p.nombre as plantel_nombre,
                   ci.nombre as ciudad_nombre,
                   es.nombre as estado_nombre,
                   emp.nombre as empleado_nombre,
                   enc.nombre as encargado_nombre,
                   t.nombre as tipo_nombre
            FROM activos d
            LEFT JOIN activos base ON d.clave_activo = base.clave AND base.cubiculo_id IS NULL
            JOIN cubiculos c ON d.cubiculo_id = c.id
            JOIN edificios e ON c.edificio_id = e.id
            JOIN planteles p ON e.plantel_id = p.id
            JOIN ciudades ci ON p.ciudad_id = ci.id
            JOIN estados es ON ci.estado_id = es.id
            LEFT JOIN empleados emp ON d.empleado_id = emp.id
            LEFT JOIN encargados enc ON d.encargado_id = enc.id
            LEFT JOIN tipos_activos t ON COALESCE(base.tipo_activo_id, d.tipo_activo_id) = t.id
            WHERE 1=1
        '''
        
        params = []
        
        if texto_busqueda.strip():
            query += '''
                AND (
                    d.clave LIKE ? OR
                    COALESCE(base.descripcion, d.descripcion_activo) LIKE ? OR
                    d.numero_inventario LIKE ? OR
                    t.nombre LIKE ?
                )
            '''
            patron = f"%{texto_busqueda}%"
            params.extend([patron, patron, patron, patron])
        
        if encargado:
            query += " AND enc.nombre = ?"
            params.append(encargado)

        if empleado:
            query += " AND emp.nombre = ?"
            params.append(empleado)

        if tipo_activo_id is not None:
            query += " AND d.tipo_activo_id = ?"
            params.append(tipo_activo_id)

        if len(ruta_parcial) > 0:
            query += " AND es.nombre = ?"
            params.append(ruta_parcial[0])
        if len(ruta_parcial) > 1:
            query += " AND ci.nombre = ?"
            params.append(ruta_parcial[1])
        if len(ruta_parcial) > 2:
            query += " AND p.nombre = ?"
            params.append(ruta_parcial[2])
        if len(ruta_parcial) > 3:
            query += " AND e.nombre = ?"
            params.append(ruta_parcial[3])
        if len(ruta_parcial) > 4:
            query += " AND c.nombre = ?"
            params.append(ruta_parcial[4])

        cursor.execute(query, params)
        
        activos = []
        for row in cursor.fetchall():
            activo = dict(row)
            activo['ubicacion'] = " > ".join([
                activo['estado_nombre'],
                activo['ciudad_nombre'],
                activo['plantel_nombre'],
                activo['edificio_nombre'],
                activo['cubiculo_nombre']
            ])
            activos.append(activo)
        
        return activos

def obtener_opciones_nivel(nivel_indice, ruta_previa=[]):
    """Obtiene opciones disponibles para un nivel jerárquico"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if nivel_indice == 0:  # Estados
            cursor.execute("SELECT DISTINCT nombre FROM estados ORDER BY nombre")
        
        elif nivel_indice == 1:  # Ciudades
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                cursor.execute("SELECT DISTINCT nombre FROM ciudades WHERE estado_id = ? ORDER BY nombre", (estado_id,))
        
        elif nivel_indice == 2:  # Planteles
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    cursor.execute("SELECT DISTINCT nombre FROM planteles WHERE ciudad_id = ? ORDER BY nombre", (ciudad_id,))
        
        elif nivel_indice == 3:  # Edificios
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    plantel_id = None
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (ruta_previa[2], ciudad_id))
                    row = cursor.fetchone()
                    if row:
                        plantel_id = row['id']
                        cursor.execute("SELECT DISTINCT nombre FROM edificios WHERE plantel_id = ? ORDER BY nombre", (plantel_id,))
        
        elif nivel_indice == 4:  # Cubículos
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    plantel_id = None
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (ruta_previa[2], ciudad_id))
                    row = cursor.fetchone()
                    if row:
                        plantel_id = row['id']
                        edificio_id = None
                        cursor.execute("SELECT id FROM edificios WHERE nombre = ? AND plantel_id = ?", (ruta_previa[3], plantel_id))
                        row = cursor.fetchone()
                        if row:
                            edificio_id = row['id']
                            cursor.execute("SELECT DISTINCT nombre FROM cubiculos WHERE edificio_id = ? ORDER BY nombre", (edificio_id,))
        
        opciones = [row['nombre'] for row in cursor.fetchall()]
        return opciones

def eliminar_elemento_jerarquico(nombre, nivel, ruta_previa=[]):
    """Elimina un elemento de la jerarquía y todos sus descendientes"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if nivel == 0:  # Estado
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (nombre,))
        elif nivel == 1:  # Ciudad
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (nombre, estado_id))
        elif nivel == 2:  # Plantel
            # Obtener IDs necesarios...
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (nombre, ciudad_id))
        elif nivel == 3:  # Edificio
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    plantel_id = None
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (ruta_previa[2], ciudad_id))
                    row = cursor.fetchone()
                    if row:
                        plantel_id = row['id']
                        cursor.execute("SELECT id FROM edificios WHERE nombre = ? AND plantel_id = ?", (nombre, plantel_id))
        elif nivel == 4:  # Cubículo
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    plantel_id = None
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (ruta_previa[2], ciudad_id))
                    row = cursor.fetchone()
                    if row:
                        plantel_id = row['id']
                        edificio_id = None
                        cursor.execute("SELECT id FROM edificios WHERE nombre = ? AND plantel_id = ?", (ruta_previa[3], plantel_id))
                        row = cursor.fetchone()
                        if row:
                            edificio_id = row['id']
                            cursor.execute("SELECT id FROM cubiculos WHERE nombre = ? AND edificio_id = ?", (nombre, edificio_id))
        
        row = cursor.fetchone()
        if row:
            elemento_id = row['id']
            
            # Eliminar en cascada según el nivel
            if nivel == 0:
                cursor.execute("DELETE FROM ciudades WHERE estado_id = ?", (elemento_id,))
                cursor.execute("DELETE FROM planteles WHERE ciudad_id IN (SELECT id FROM ciudades WHERE estado_id = ?)", (elemento_id,))
                cursor.execute("DELETE FROM edificios WHERE plantel_id IN (SELECT id FROM planteles WHERE ciudad_id IN (SELECT id FROM ciudades WHERE estado_id = ?))", (elemento_id,))
                cursor.execute("DELETE FROM cubiculos WHERE edificio_id IN (SELECT id FROM edificios WHERE plantel_id IN (SELECT id FROM planteles WHERE ciudad_id IN (SELECT id FROM ciudades WHERE estado_id = ?)))", (elemento_id,))
                cursor.execute("DELETE FROM activos WHERE cubiculo_id IN (SELECT id FROM cubiculos WHERE edificio_id IN (SELECT id FROM edificios WHERE plantel_id IN (SELECT id FROM planteles WHERE ciudad_id IN (SELECT id FROM ciudades WHERE estado_id = ?))))", (elemento_id,))
                cursor.execute("DELETE FROM estados WHERE id = ?", (elemento_id,))
            elif nivel == 1:
                cursor.execute("DELETE FROM planteles WHERE ciudad_id = ?", (elemento_id,))
                cursor.execute("DELETE FROM edificios WHERE plantel_id IN (SELECT id FROM planteles WHERE ciudad_id = ?)", (elemento_id,))
                cursor.execute("DELETE FROM cubiculos WHERE edificio_id IN (SELECT id FROM edificios WHERE plantel_id IN (SELECT id FROM planteles WHERE ciudad_id = ?))", (elemento_id,))
                cursor.execute("DELETE FROM activos WHERE cubiculo_id IN (SELECT id FROM cubiculos WHERE edificio_id IN (SELECT id FROM edificios WHERE plantel_id IN (SELECT id FROM planteles WHERE ciudad_id = ?)))", (elemento_id,))
                cursor.execute("DELETE FROM ciudades WHERE id = ?", (elemento_id,))
            elif nivel == 2:
                cursor.execute("DELETE FROM edificios WHERE plantel_id = ?", (elemento_id,))
                cursor.execute("DELETE FROM cubiculos WHERE edificio_id IN (SELECT id FROM edificios WHERE plantel_id = ?)", (elemento_id,))
                cursor.execute("DELETE FROM activos WHERE cubiculo_id IN (SELECT id FROM cubiculos WHERE edificio_id IN (SELECT id FROM edificios WHERE plantel_id = ?))", (elemento_id,))
                cursor.execute("DELETE FROM planteles WHERE id = ?", (elemento_id,))
            elif nivel == 3:
                cursor.execute("DELETE FROM cubiculos WHERE edificio_id = ?", (elemento_id,))
                cursor.execute("DELETE FROM activos WHERE cubiculo_id IN (SELECT id FROM cubiculos WHERE edificio_id = ?)", (elemento_id,))
                cursor.execute("DELETE FROM edificios WHERE id = ?", (elemento_id,))
            elif nivel == 4:
                cursor.execute("DELETE FROM activos WHERE cubiculo_id = ?", (elemento_id,))
                cursor.execute("DELETE FROM cubiculos WHERE id = ?", (elemento_id,))
            
            conn.commit()

def renombrar_elemento_jerarquico(nombre_viejo, nombre_nuevo, nivel, ruta_previa=[]):
    """Renombra un elemento de la jerarquía"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if nivel == 0:  # Estado
            cursor.execute("UPDATE estados SET nombre = ? WHERE nombre = ?", (nombre_nuevo, nombre_viejo))
        elif nivel == 1:  # Ciudad
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                cursor.execute("UPDATE ciudades SET nombre = ? WHERE nombre = ? AND estado_id = ?", (nombre_nuevo, nombre_viejo, estado_id))
        elif nivel == 2:  # Plantel
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    cursor.execute("UPDATE planteles SET nombre = ? WHERE nombre = ? AND ciudad_id = ?", (nombre_nuevo, nombre_viejo, ciudad_id))
        elif nivel == 3:  # Edificio
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    plantel_id = None
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (ruta_previa[2], ciudad_id))
                    row = cursor.fetchone()
                    if row:
                        plantel_id = row['id']
                        cursor.execute("UPDATE edificios SET nombre = ? WHERE nombre = ? AND plantel_id = ?", (nombre_nuevo, nombre_viejo, plantel_id))
        elif nivel == 4:  # Cubículo
            estado_id = None
            cursor.execute("SELECT id FROM estados WHERE nombre = ?", (ruta_previa[0],))
            row = cursor.fetchone()
            if row:
                estado_id = row['id']
                ciudad_id = None
                cursor.execute("SELECT id FROM ciudades WHERE nombre = ? AND estado_id = ?", (ruta_previa[1], estado_id))
                row = cursor.fetchone()
                if row:
                    ciudad_id = row['id']
                    plantel_id = None
                    cursor.execute("SELECT id FROM planteles WHERE nombre = ? AND ciudad_id = ?", (ruta_previa[2], ciudad_id))
                    row = cursor.fetchone()
                    if row:
                        plantel_id = row['id']
                        edificio_id = None
                        cursor.execute("SELECT id FROM edificios WHERE nombre = ? AND plantel_id = ?", (ruta_previa[3], plantel_id))
                        row = cursor.fetchone()
                        if row:
                            edificio_id = row['id']
                            cursor.execute("UPDATE cubiculos SET nombre = ? WHERE nombre = ? AND edificio_id = ?", (nombre_nuevo, nombre_viejo, edificio_id))
        
        conn.commit()


# ============ FUNCIONES DE ENCARGADOS ============

def obtener_todos_encargados():
    """Obtiene todos los encargados disponibles"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, telefono FROM encargados ORDER BY nombre")
        encargados = [dict(row) for row in cursor.fetchall()]
        return encargados

def agregar_encargado(nombre, correo="", telefono=""):
    """Agrega un nuevo encargado a la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO encargados (nombre, correo, telefono) VALUES (?, ?, ?)",
                (nombre, correo, telefono)
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # El nombre ya existe
            return None

def actualizar_encargado(encargado_id, nombre, correo, telefono):
    """Actualiza los datos de un encargado"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE encargados SET nombre = ?, correo = ?, telefono = ? WHERE id = ?",
                (nombre, correo, telefono, encargado_id)
            )
        except sqlite3.IntegrityError:
            # El nombre ya existe
            return False
        return True

def eliminar_encargado(encargado_id):
    """Elimina un encargado de la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM encargados WHERE id = ?", (encargado_id,))

def obtener_encargado_por_id(encargado_id):
    """Obtiene un encargado específico por ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, telefono FROM encargados WHERE id = ?", (encargado_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def obtener_encargado_por_nombre(nombre):
    """Obtiene un encargado específico por nombre"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, telefono FROM encargados WHERE nombre = ?", (nombre,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ============ FUNCIONES PARA EMPLEADOS ============

def obtener_todos_empleados():
    """Obtiene todos los empleados disponibles"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, telefono FROM empleados ORDER BY nombre")
        empleados = [dict(row) for row in cursor.fetchall()]
        return empleados

def agregar_empleado(nombre, correo="", telefono=""):
    """Agrega un nuevo empleado a la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO empleados (nombre, correo, telefono) VALUES (?, ?, ?)",
                (nombre, correo, telefono)
            )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # El nombre ya existe
            return None

def actualizar_empleado(empleado_id, nombre, correo, telefono):
    """Actualiza los datos de un empleado"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE empleados SET nombre = ?, correo = ?, telefono = ? WHERE id = ?",
                (nombre, correo, telefono, empleado_id)
            )
        except sqlite3.IntegrityError:
            # El nombre ya existe
            return False
        return True

def eliminar_empleado(empleado_id):
    """Elimina un empleado de la base de datos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM empleados WHERE id = ?", (empleado_id,))

def obtener_empleado_por_id(empleado_id):
    """Obtiene un empleado específico por ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, telefono FROM empleados WHERE id = ?", (empleado_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def obtener_empleado_por_nombre(nombre):
    """Obtiene un empleado específico por nombre"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, telefono FROM empleados WHERE nombre = ?", (nombre,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ============ FUNCIONES PARA ACTIVOS HUÉRFANOS ============

def obtener_activos_huerfanos():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT a.*, e.nombre AS empleado_nombre, enc.nombre AS encargado_nombre
            FROM activos a
            LEFT JOIN empleados e ON a.empleado_id = e.id
            LEFT JOIN encargados enc ON a.encargado_id = enc.id
            WHERE a.cubiculo_id NOT IN (SELECT id FROM cubiculos)
        ''')
        return [dict(row) for row in cursor.fetchall()]

def eliminar_activos_huerfanos():
    """Elimina todos los activos huérfanos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM activos
            WHERE cubiculo_id NOT IN (SELECT id FROM cubiculos)
        ''')
        return cursor.rowcount  # Retorna el número de filas eliminadas

# ============ FUNCIONES PARA TIPOS DE ACTIVOS ============

def obtener_todos_tipos_activos():
    """Obtiene todos los tipos de activos"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion FROM tipos_activos ORDER BY nombre")
        tipos = []
        for row in cursor.fetchall():
            tipos.append(dict(row))
        return tipos

def agregar_tipo_activo(nombre, descripcion=""):
    """Agrega un nuevo tipo de activo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tipos_activos (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        return cursor.lastrowid

def actualizar_tipo_activo(tipo_id, nombre, descripcion):
    """Actualiza un tipo de activo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tipos_activos SET nombre = ?, descripcion = ? WHERE id = ?", (nombre, descripcion, tipo_id))

def eliminar_tipo_activo(tipo_id):
    """Elimina un tipo de activo"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tipos_activos WHERE id = ?", (tipo_id,))

def obtener_tipo_activo_por_id(tipo_id):
    """Obtiene un tipo de activo específico por ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, descripcion FROM tipos_activos WHERE id = ?", (tipo_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ============ FUNCIONES PARA ACTIVOS ============

def obtener_todos_activos():
    """Obtiene todos los activos base (no asignados)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT a.numero_inventario, a.clave, a.descripcion, t.nombre AS tipo_nombre, a.tipo_activo_id
            FROM activos a
            LEFT JOIN tipos_activos t ON a.tipo_activo_id = t.id
            WHERE a.cubiculo_id IS NULL
            ORDER BY a.clave
        """)
        return [dict(row) for row in cursor.fetchall()]

def agregar_activo(descripcion, tipo_activo_id=None):
    """Agrega un nuevo activo base y retorna la clave generada"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(CAST(clave AS INTEGER)) AS max_clave FROM activos WHERE clave GLOB '[0-9]*'"
        )
        row = cursor.fetchone()
        siguiente_numero = (row["max_clave"] or 0) + 1
        clave = f"{siguiente_numero:07d}"

        cursor.execute(
            "SELECT MAX(CAST(numero_inventario AS INTEGER)) AS max_inv FROM activos WHERE numero_inventario GLOB '[0-9]*'"
        )
        row_inv = cursor.fetchone()
        siguiente_inv = (row_inv["max_inv"] or 0) + 1
        numero_inventario = f"{siguiente_inv:011d}"

        cursor.execute(
            "INSERT INTO activos (numero_inventario, clave, clave_activo, descripcion, descripcion_activo, tipo_activo_id) VALUES (?, ?, ?, ?, ?, ?)",
            (numero_inventario, clave, clave, descripcion, descripcion, tipo_activo_id)
        )
        return clave

def actualizar_activo(numero_inventario, descripcion, tipo_activo_id=None):
    """Actualiza un activo base"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT clave FROM activos WHERE numero_inventario = ? AND cubiculo_id IS NULL",
            (numero_inventario,)
        )
        row = cursor.fetchone()
        cursor.execute(
            "UPDATE activos SET descripcion = ?, descripcion_activo = ?, tipo_activo_id = ? WHERE numero_inventario = ?",
            (descripcion, descripcion, tipo_activo_id, numero_inventario)
        )
        if row:
            clave_base = row['clave']
            cursor.execute(
                "UPDATE activos SET descripcion_activo = ?, tipo_activo_id = ? WHERE clave_activo = ? AND cubiculo_id IS NOT NULL",
                (descripcion, tipo_activo_id, clave_base)
            )

def eliminar_activo(numero_inventario):
    """Elimina un activo base"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activos WHERE numero_inventario = ?", (numero_inventario,))

def obtener_activo_por_id(numero_inventario):
    """Obtiene un activo específico por numero_inventario"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT numero_inventario, clave, descripcion FROM activos WHERE numero_inventario = ?", (numero_inventario,))
        row = cursor.fetchone()
        return dict(row) if row else None

def obtener_activo_por_clave(clave):
    """Obtiene un activo específico por clave"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, clave, descripcion FROM activos WHERE clave = ?", (clave,))
        row = cursor.fetchone()
        return dict(row) if row else None
