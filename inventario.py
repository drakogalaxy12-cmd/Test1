import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from database import (
    inicializar_bd, obtener_opciones_nivel, guardar_activo,
    actualizar_activo, eliminar_activo, actualizar_activo_asignado, eliminar_activo_asignado, cargar_activos_cubiculo,
    buscar_activos_por_criterios, obtener_todos_encargados, agregar_encargado,
    actualizar_encargado, eliminar_encargado, eliminar_elemento_jerarquico,
    renombrar_elemento_jerarquico, obtener_activos_huerfanos, eliminar_activos_huerfanos,
    obtener_todos_empleados, agregar_empleado, actualizar_empleado, eliminar_empleado,
    obtener_todos_tipos_activos, agregar_tipo_activo, actualizar_tipo_activo, eliminar_tipo_activo,
    obtener_todos_activos, agregar_activo, actualizar_activo, eliminar_activo, obtener_nombre_cubiculo
)

# streamlit run inventario.py

# Configurar página
st.set_page_config(
    page_title="Inventario",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar base de datos
inicializar_bd()

# Estilos CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(to right, #2e7d32 0%, #66bb6a 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .section-header {
        background-color: #e8f5e9;
        color: #0b3d0f;
        padding: 10px 15px;
        border-left: 4px solid #2e7d32;
        margin: 15px 0 10px 0;
        border-radius: 5px;
    }
    .stApp {
        background-color: #f7fff5 !important;
        color: #0b3d0f !important;
    }
    .stApp, .stApp * {
        color: #0b3d0f !important;
    }
    .stApp input, .stApp textarea, .stApp select, .stApp button {
        color: #0b3d0f !important;
        background-color: #ffffff !important;
    }
    .stApp input:disabled, .stApp textarea:disabled {
        background-color: #f0f0f0 !important;
    }
    section[data-testid="stSidebar"] {
        position: sticky !important;
        top: 0 !important;
        height: 100vh !important;
        overflow: auto !important;
        transform: none !important;
    }
    button[title="Toggle sidebar"] {
        display: none !important;
    }
    .device-table-wrapper {
        overflow-x: auto;
        width: 100%;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .device-table {
        width: 100%;
        border-collapse: collapse;
        background: #ffffff;
        margin-bottom: 16px;
    }
    .device-table th,
    .device-table td {
        border: 1px solid #cfd8dc;
        padding: 10px 12px;
        text-align: left;
    }
    .device-table th {
        background: #e8f5e9;
        color: #0b3d0f;
        font-weight: 700;
    }
    .device-table tr:nth-child(even) {
        background: #f7f7f7;
    }
    .device-table tr:hover {
        background: #e8f5e9;
    }
    .device-table-content {
        min-width: 1000px;
    }
    .device-table-header {
        display: flex;
        gap: 10px;
        font-weight: 700;
        background: #dcedc8;
        padding: 10px 12px;
        border-radius: 8px;
        margin-bottom: 8px;
        color: #1b5e20;
    }
    .device-cell {
        flex: 1 0 160px;
        min-width: 160px;
        overflow-wrap: anywhere;
        padding: 10px 0;
        border-bottom: 0px solid #cfd8dc;
    }
    .device-action {
        flex: 0 0 140px;
    }
    /* Ajusta la altura de los checkboxes */
    div.stCheckbox > label > div {
        min-height: 0px;
        padding-top: 0px;
    }
    .checkbox-section div.stCheckbox + div.stCheckbox {
        margin-top: 1px;
    }
    .checkbox-section div.stCheckbox:first-of-type {
        margin-top: 40px !important;
    }
    /* Ajusta el tamaño del cuadro de selección */
    div.stCheckbox input[type="checkbox"] {
        transform: scale(0.5);
    }
    .stDataFrame {
        font-size: 15px !important;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar sesión
if 'nivel' not in st.session_state:
    st.session_state.nivel = 0
    st.session_state.ruta = []
    st.session_state.cubiculo_id = None
    st.session_state.pagina = "🏠 Inicio"
    st.session_state.activo_a_eliminar = None
    st.session_state.nombre_activo_eliminar = None
    st.session_state.encargado_a_eliminar = None
    st.session_state.nombre_encargado_eliminar = None
    st.session_state.editar_activo_id = None
    st.session_state.editar_encargado = ""
    st.session_state.editar_empleado = ""
    st.session_state.editar_cantidad = None
    st.session_state.texto_busqueda = ""
    st.session_state.filtro_estado = "-- Todos --"
    st.session_state.filtro_ciudad = "-- Todos --"
    st.session_state.filtro_plantel = "-- Todos --"
    st.session_state.filtro_edificio = "-- Todos --"
    st.session_state.filtro_cubiculo = "-- Todos --"
    st.session_state.filtro_encargado = "-- Todos --"
    st.session_state.filtro_empleado = "-- Todos --"
    st.session_state.filtro_tipo_activo = "-- Todos --"
    st.session_state.filtro_presencia = "-- Todos --"
    st.session_state.resultados_busqueda = None
    st.session_state.change_to_inicio = False

if  st.session_state.get('change_to_inicio', False):
    st.session_state.pagina = "🏠 Inicio"
    st.session_state.change_to_inicio = False

HIERARCHY_LEVELS = ["Estados", "Ciudades", "Planteles", "Edificios", "Cubículos"]
HIERARCHY_SINGULAR = ["Estado", "Ciudad", "Plantel", "Edificio", "Cubículo"]

# Mapeo de nombre de nivel a nombre correcto de tabla en base de datos
TABLA_NAMES = {
    "estados": "estados",
    "ciudades": "ciudades",
    "planteles": "planteles",
    "edificios": "edificios",
    "cubículos": "cubiculos"
}

def reiniciar_filtros_busqueda():
    """Restablece los filtros de búsqueda y el resultado guardado."""
    st.session_state.update({
        "texto_busqueda": "",
        "filtro_estado": "-- Todos --",
        "filtro_ciudad": "-- Todos --",
        "filtro_plantel": "-- Todos --",
        "filtro_edificio": "-- Todos --",
        "filtro_cubiculo": "-- Todos --",
        "filtro_encargado": "-- Todos --",
        "filtro_empleado": "-- Todos --",
        "filtro_tipo_activo": "-- Todos --",
        "filtro_presencia": "-- Todos --",
        "resultados_busqueda": None,
    })

# ============ FUNCIONES AUXILIARES ============

def obtener_id_cubiculo(nombre, ruta=None):
    """Obtiene el ID del cubículo por nombre y ruta completa"""
    with sqlite3.connect("inventario.db") as conn:
        cursor = conn.cursor()
        if ruta and len(ruta) >= 4:
            cursor.execute('''
                SELECT c.id
                FROM cubiculos c
                JOIN edificios e ON c.edificio_id = e.id
                JOIN planteles p ON e.plantel_id = p.id
                JOIN ciudades ci ON p.ciudad_id = ci.id
                JOIN estados es ON ci.estado_id = es.id
                WHERE c.nombre = ?
                  AND e.nombre = ?
                  AND p.nombre = ?
                  AND ci.nombre = ?
                  AND es.nombre = ?
            ''', (nombre, ruta[3], ruta[2], ruta[1], ruta[0]))
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]

        cursor.execute("SELECT id FROM cubiculos WHERE nombre = ? LIMIT 1", (nombre,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else None


def agregar_elemento_bd(nivel, ruta, nombre):
    """Agrega un elemento a la base de datos"""
    # Mapeo de tabla a columna de clave foránea
    mapeo_columnas = {
        "ciudades": "estado_id",
        "planteles": "ciudad_id",
        "edificios": "plantel_id",
        "cubiculos": "edificio_id"
    }
    
    with sqlite3.connect("inventario.db") as conn:
        cursor = conn.cursor()
        # Usar el mapeo TABLA_NAMES para obtener el nombre correcto de la tabla
        nombre_tabla_display = HIERARCHY_LEVELS[nivel].lower()
        nombre_tabla = TABLA_NAMES.get(nombre_tabla_display, nombre_tabla_display)
        
        if nivel == 0:  # Estados
            cursor.execute(f"INSERT INTO {nombre_tabla} (nombre) VALUES (?)", (nombre,))
        else:
            # Obtener ID del padre
            nombre_padre_display = HIERARCHY_LEVELS[nivel - 1].lower()
            padre_tabla = TABLA_NAMES.get(nombre_padre_display, nombre_padre_display)
            padre_id_col = mapeo_columnas.get(nombre_tabla, f"{padre_tabla.rstrip('s')}_id")
            
            cursor.execute(f"SELECT id FROM {padre_tabla} WHERE nombre = ?", (ruta[-1],))
            padre_id = cursor.fetchone()[0]
            
            cursor.execute(
                f"INSERT INTO {nombre_tabla} (nombre, {padre_id_col}) VALUES (?, ?)",
                (nombre, padre_id)
            )
        conn.commit()

def manejar_activos():
    """Maneja la interfaz de activos en un cubículo"""
    st.markdown("<div class='section-header'><b>Activos del Cubículo</b></div>", unsafe_allow_html=True)

    activos = cargar_activos_cubiculo(st.session_state.cubiculo_id)

    # Filtrado
    activos_filtrados = activos
    busqueda_cubiculo = st.text_input("Buscar en este cubículo", key="busqueda_cubiculo")
    if busqueda_cubiculo.strip():
        texto = busqueda_cubiculo.strip().lower()
        activos_filtrados = [
            d for d in activos
            if texto in str(d.get('clave_activo', '')).lower()
            or texto in str(d.get('descripcion_activo', '')).lower()
            or texto in str(d.get('numero_inventario', '')).lower()
            or texto in str(d.get('encargado_nombre', '')).lower()
            or texto in str(d.get('empleado_nombre', '')).lower()
        ]

    if activos_filtrados:
        rows = []
        for d in activos_filtrados:
            presente_estado = bool(d.get('presente', False))
            rows.append({
                "Clave": d.get('clave_activo', '-'),
                "Descripción": d.get('descripcion_activo', '-'),
                "Número de inventario": d.get('numero_inventario', '-'),
                "Encargado": d.get('encargado_nombre', '-'),
                "Empleado": d.get('empleado_nombre', '-'),
                "Cantidad": d.get('cantidad', 1),
                "Presente interno": presente_estado  # checkbox dentro de la tabla
            })

        df_activos = pd.DataFrame(rows)

        if not df_activos.empty:
            df_editado = st.data_editor(
                df_activos,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Presente interno": st.column_config.CheckboxColumn(
                        "Presente", disabled=False
                    )
                },
                key="tabla_activos"
            )

            # Persistir cambios de presencia en la base de datos
            for idx, row in df_editado.iterrows():
                original_presente = df_activos.loc[idx, "Presente interno"]
                nuevo_presente = row["Presente interno"]
                if original_presente != nuevo_presente:
                    actualizar_activo_asignado(
                        row['Número de inventario'],
                        presente=int(bool(nuevo_presente))
                    )
            st.cache_data.clear()
        else:
            st.info("No hay activos en este cubículo")

        # Selección compacta de activo
        opciones_activos = [f"Inv {r['Número de inventario']} - {r['Clave']}" for r in rows]
        
        col1, col2, col3 = st.columns([2.5, 0.75, 0.75])
        
        with col1:
            seleccion = st.selectbox("Selecciona:", opciones_activos, key="activo_seleccionado", label_visibility="collapsed")
            activo_seleccionado = rows[opciones_activos.index(seleccion)]
        
        with col2:
            if st.button("✏️ Editar", key="btn_editar_seleccionado", use_container_width=True):
                selected_device = next((d for d in activos if d.get('numero_inventario') == activo_seleccionado['Número de inventario']), None)
                if selected_device:
                    st.session_state.editar_activo_id = activo_seleccionado['Número de inventario']
                    st.session_state.editar_encargado = selected_device.get('encargado_nombre', '')
                    st.session_state.editar_empleado = selected_device.get('empleado_nombre', '')
                    st.session_state.editar_presente = selected_device.get('presente', False)
                    st.session_state.editar_cantidad = selected_device.get('cantidad', 1)
                    st.rerun()
        
        with col3:
            if st.button("🗑️ Eliminar", key="btn_eliminar_seleccionado", use_container_width=True):
                st.session_state.activo_a_eliminar = activo_seleccionado['Número de inventario']
                st.session_state.nombre_activo_eliminar = f"{activo_seleccionado['Clave']} - {activo_seleccionado['Descripción']}"

        # Confirmación de eliminación
        if st.session_state.activo_a_eliminar is not None:
            st.divider()
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.warning(f"⚠️ ¿Eliminar el activo '{st.session_state.nombre_activo_eliminar}'?")
            with col2:
                if st.button("✅ Confirmar", key="confirmar_eliminar_activo", use_container_width=True):
                    eliminar_activo_asignado(st.session_state.activo_a_eliminar)
                    st.session_state.activo_a_eliminar = None
                    st.session_state.nombre_activo_eliminar = None
                    st.cache_data.clear()
                    st.success("✅ Activo eliminado")
                    st.rerun()
            with col3:
                if st.button("❌ Cancelar", key="cancelar_eliminar_activo", use_container_width=True):
                    st.session_state.activo_a_eliminar = None
                    st.session_state.nombre_activo_eliminar = None
                    st.rerun()
    else:
        st.info("No hay activos en este cubículo")

    # Formulario de edición
    if st.session_state.editar_activo_id is not None:
        activo_edit = next((item for item in activos if item.get('numero_inventario') == st.session_state.editar_activo_id), None)
        if activo_edit:
            st.divider()
            col_title, col_cancel = st.columns([4, 1])
            with col_title:
                st.markdown("<div class='section-header'><b>✏️ Editar activo</b></div>", unsafe_allow_html=True)
            with col_cancel:
                if st.button("❌ Cancelar", key="cancelar_edicion", use_container_width=True):
                    st.session_state.editar_activo_id = None
                    st.session_state.editar_encargado = ""
                    st.session_state.editar_empleado = ""
                    st.session_state.editar_presente = False
                    st.session_state.editar_cantidad = None
                    st.rerun()
            
            with st.form("form_editar_activo"):
                activos_disponibles = obtener_todos_activos()
                opciones_activos = ["-- Selecciona --"] + [f"{a['clave']} - {a['descripcion'][:50]}..." for a in activos_disponibles]
                # Encontrar el índice del activo actual
                activo_actual_opcion = f"{activo_edit.get('clave_activo', '')} - {activo_edit.get('descripcion_activo', '')[:50]}..."
                activo_index = opciones_activos.index(activo_actual_opcion) if activo_actual_opcion in opciones_activos else 0
                activo_edit_seleccionado = st.selectbox("Activo", opciones_activos, index=activo_index, key="editar_activo_input")
                col1, col2, col3 = st.columns(3)
                with col1:
                    encargados = obtener_todos_encargados()
                    nombres_encargados = ["-- Selecciona --"] + [e['nombre'] for e in encargados]
                    encargado_index = nombres_encargados.index(st.session_state.editar_encargado) if st.session_state.editar_encargado in nombres_encargados else 0
                    encargado_edit = st.selectbox("Encargado", nombres_encargados, index=encargado_index, key="editar_encargado_input")
                with col2:
                    empleados = obtener_todos_empleados()
                    nombres_empleados = ["-- Selecciona --"] + [e['nombre'] for e in empleados]
                    empleado_index = nombres_empleados.index(st.session_state.editar_empleado) if st.session_state.editar_empleado in nombres_empleados else 0
                    empleado_edit = st.selectbox("Empleado", nombres_empleados, index=empleado_index, key="editar_empleado_input")
                with col3:
                    cantidad_edit = st.number_input("Cantidad", min_value=1, value=st.session_state.editar_cantidad, step=1, key="editar_cantidad_input")
                    presente_edit = st.checkbox("Presente", value=st.session_state.editar_presente, key="editar_presente_input")

                submitted = st.form_submit_button("💾 Guardar cambios")

            if submitted:
                if activo_edit_seleccionado == "-- Selecciona --":
                    st.error("Selecciona un activo")
                elif encargado_edit == "-- Selecciona --":
                    st.error("Selecciona un encargado")
                else:
                    # Encontrar IDs
                    encargado_id = None
                    for enc in encargados:
                        if enc['nombre'] == encargado_edit:
                            encargado_id = enc['id']
                            break
                    empleado_id = None
                    for emp in empleados:
                        if emp['nombre'] == empleado_edit:
                            empleado_id = emp['id']
                            break
                    
                    # Verificar si el activo cambió
                    activo_actual_opcion = f"{activo_edit.get('clave_activo', '')} - {activo_edit.get('descripcion_activo', '')[:50]}..."
                    if activo_edit_seleccionado != activo_actual_opcion:
                        # Activo cambió, eliminar el actual y agregar el nuevo
                        eliminar_activo_asignado(st.session_state.editar_activo_id)
                        # Encontrar el nuevo activo
                        nuevo_activo = None
                        for a in activos_disponibles:
                            if f"{a['clave']} - {a['descripcion'][:50]}..." == activo_edit_seleccionado:
                                nuevo_activo = a
                                break
                        if nuevo_activo:
                            guardar_activo(nuevo_activo['clave'], nuevo_activo['descripcion'], empleado_id, encargado_id, st.session_state.cubiculo_id, int(presente_edit), nuevo_activo.get('tipo_activo_id'), cantidad_edit)
                        else:
                            st.error("Activo no encontrado")
                            return
                    else:
                        # Solo actualizar propiedades
                        actualizar_activo_asignado(
                            st.session_state.editar_activo_id,
                            empleado_id=empleado_id,
                            encargado_id=encargado_id,
                            presente=presente_edit,
                            cantidad=cantidad_edit
                        )
                    
                    st.session_state.editar_activo_id = None
                    st.session_state.editar_encargado = ""
                    st.session_state.editar_empleado = ""
                    st.session_state.editar_presente = False
                    st.session_state.editar_cantidad = None
                    st.cache_data.clear()
                    st.success("✅ Activo actualizado")
                    st.rerun()
    
    # Agregar activo
    with st.expander("➕ Agregar Activo"):
        activos = obtener_todos_activos()
        opciones_activos = [f"{a['clave']} - {a['descripcion'][:50]}..." for a in activos]
        activo_seleccionado = st.selectbox("Selecciona un activo", ["-- Selecciona --"] + opciones_activos, key="agregar_activo")
        
        col1, col2 = st.columns(2)
        with col1:
            encargados = obtener_todos_encargados()
            nombres_encargados = [e['nombre'] for e in encargados]
            encargado = st.selectbox("Encargado", ["-- Selecciona --"] + nombres_encargados, key="agregar_encargado")
        
        with col2:
            empleados = obtener_todos_empleados()
            nombres_empleados = [e['nombre'] for e in empleados]
            empleado = st.selectbox("Empleado", ["-- Selecciona --"] + nombres_empleados, key="agregar_empleado")
        
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, key="agregar_cantidad")
        
        if st.button("✅ Guardar Activo"):
            if activo_seleccionado != "-- Selecciona --" and encargado != "-- Selecciona --":
                # Encontrar el activo seleccionado
                activo = None
                for a in activos:
                    if f"{a['clave']} - {a['descripcion'][:50]}..." == activo_seleccionado:
                        activo = a
                        break
                if activo:
                    # Encontrar IDs
                    encargado_id = None
                    for enc in encargados:
                        if enc['nombre'] == encargado:
                            encargado_id = enc['id']
                            break
                    empleado_id = None
                    if empleado != "-- Selecciona --":
                        for emp in empleados:
                            if emp['nombre'] == empleado:
                                empleado_id = emp['id']
                                break
                    guardar_activo(activo['clave'], activo['descripcion'], empleado_id, encargado_id, st.session_state.cubiculo_id, 0, activo.get('tipo_activo_id'), cantidad)
                    st.cache_data.clear()
                    st.success("✅ Activo agregado al cubículo")
                    st.rerun()
                else:
                    st.error("Activo no encontrado")
            else:
                st.error("Selecciona activo, encargado y empleado")

    # Subir Excel
    if 'excel_procesado' not in st.session_state:
        st.session_state.excel_procesado = None
    if 'excel_cargado' not in st.session_state:
        st.session_state.excel_cargado = None
    if 'excel_df' not in st.session_state:
        st.session_state.excel_df = None
    
    with st.expander("📤 Subir Excel"):
        uploaded_file = st.file_uploader("Sube archivo Excel con columnas: Clave, Encargado, Empleado (opcional), Cantidad", type=['xlsx'])
        
        if uploaded_file is not None:
            archivo_id = f"{uploaded_file.name}_{uploaded_file.size}"
            
            # Cargar el archivo si es nuevo
            if archivo_id != st.session_state.excel_cargado:
                try:
                    df = pd.read_excel(uploaded_file, header=None)
                    if df.shape[1] < 4:
                        st.error("El archivo debe tener al menos 4 columnas: Clave (primera), Encargado (segunda), Empleado (tercera), Cantidad (cuarta)")
                    else:
                        st.session_state.excel_df = df
                        st.session_state.excel_cargado = archivo_id
                        st.info(f"✅ Archivo cargado: {len(df)} filas detectadas. Haz clic en 'Procesar Excel' para agregar los activos.")
                except Exception as e:
                    st.error(f"Error al cargar el archivo: {e}")
        
        # Mostrar preview del archivo cargado
        if st.session_state.excel_df is not None:
            st.markdown("**Vista previa del archivo:**")
            st.dataframe(st.session_state.excel_df, use_container_width=True)
            
            # Botón para procesar
            if st.button("🔄 Procesar Excel", key="procesar_excel"):
                df = st.session_state.excel_df
                activos = obtener_todos_activos()
                encargados = obtener_todos_encargados()
                empleados = obtener_todos_empleados()
                agregados = 0
                ignorados = 0
                detalles_error = []
                
                for index, row in df.iterrows():
                    try:
                        clave = str(row.iloc[0]).strip().lstrip('0') if pd.notna(row.iloc[0]) else ""
                        enc_nombre = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                        emp_nombre = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                        cantidad = row.iloc[3] if pd.notna(row.iloc[3]) else 1
                        
                        try:
                            cantidad = int(cantidad)
                            if cantidad <= 0:
                                cantidad = 1
                        except:
                            cantidad = 1
                        
                        if not clave or not enc_nombre:
                            ignorados += 1
                            detalles_error.append(f"Fila {index + 1}: Campos requeridos vacíos (Clave y Encargado son obligatorios)")
                            continue
                        
                        activo = next((a for a in activos if str(a['clave']).strip().lstrip('0') == clave), None)
                        if not activo:
                            ignorados += 1
                            detalles_error.append(f"Fila {index + 1}: Clave '{clave}' no encontrada")
                            continue
                        
                        encargado = next((e for e in encargados if str(e['nombre']).strip() == enc_nombre), None)
                        if not encargado:
                            ignorados += 1
                            detalles_error.append(f"Fila {index + 1}: Encargado '{enc_nombre}' no encontrado")
                            continue
                        
                        empleado_id = None
                        if emp_nombre:
                            empleado = next((e for e in empleados if str(e['nombre']).strip() == emp_nombre), None)
                            if not empleado:
                                ignorados += 1
                                detalles_error.append(f"Fila {index + 1}: Empleado '{emp_nombre}' no encontrado")
                                continue
                            empleado_id = empleado['id']
                        
                        # Añadir activo
                        guardar_activo(activo['clave'], activo['descripcion'], empleado_id, encargado['id'], st.session_state.cubiculo_id, 0, activo.get('tipo_activo_id'), cantidad)
                        agregados += 1
                    except Exception as e:
                        ignorados += 1
                        detalles_error.append(f"Fila {index + 1}: Error - {str(e)}")
                
                # Limpiar todo
                st.session_state.excel_procesado = None
                st.session_state.excel_df = None
                st.session_state.excel_cargado = None
                
                st.success(f"✅ {agregados} activos agregados. {ignorados} filas ignoradas.")
                
                if detalles_error:
                    with st.expander("📋 Detalles de errores"):
                        for detalle in detalles_error:
                            st.write(f"❌ {detalle}")
                
                if agregados > 0:
                    st.cache_data.clear()
                    st.rerun()

# Sidebar - Navegación principal
st.sidebar.markdown("# 📦 Inventario")

pagina = st.sidebar.radio(
    "Selecciona una sección:",
    ["🏠 Inicio", "🔍 Buscar", "👥 Encargados", "🧑 Empleados", "📦 Tipos de Activos", "📋 Activos", "🔧 Mantenimiento"],
    key="pagina"
)

# ============ PÁGINA INICIO ============
if pagina == "🏠 Inicio":
    if st.session_state.cubiculo_id:
        # Mostrar activos del cubículo
        col1, col2 = st.columns([4, 1])
        with col1:
            nombre_cubiculo = obtener_nombre_cubiculo(st.session_state.cubiculo_id)
            st.markdown(f"<div class='main-header'><h1>📍 {nombre_cubiculo}</h1></div>", 
                        unsafe_allow_html=True)
        with col2:
            if st.button("← Volver al navegador", use_container_width=True, key="volver_navegador"):
                st.session_state.cubiculo_id = None
                st.session_state.nivel = len(HIERARCHY_LEVELS) - 1
                st.rerun()

        st.markdown(f"**Ubicación:** {' > '.join(st.session_state.ruta)}")
        st.divider()
        manejar_activos()
    else:
        # Navegación jerárquica
        st.markdown("<div class='main-header'><h1>Sistema de Inventario</h1><p>Gestión jerárquica de activos</p></div>", 
                    unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([3.2, 0.4, 0.7, 0.7])
        with col1:
            st.markdown(f"**Ubicación:** {' > '.join(st.session_state.ruta) if st.session_state.ruta else HIERARCHY_LEVELS[st.session_state.nivel]}")

        with col2:
            st.write("")

        with col3:
            if st.session_state.nivel > 0:
                if st.button("← Atrás", key="btn_atras_top"):
                    st.session_state.ruta.pop()
                    st.session_state.nivel -= 1
                    st.rerun()

        with col4:
            if st.button("↺ Reiniciar", key="btn_reiniciar"):
                st.session_state.nivel = 0
                st.session_state.ruta = []
                st.session_state.cubiculo_id = None
                st.rerun()

        # Cargar elementos del nivel actual
        elementos = obtener_opciones_nivel(st.session_state.nivel, st.session_state.ruta)
        
        st.markdown(f"<div class='section-header'><b>{HIERARCHY_LEVELS[st.session_state.nivel]}</b></div>", 
                    unsafe_allow_html=True)

        # Grid de elementos
        if st.session_state.nivel < len(HIERARCHY_LEVELS) - 1:
            cols = st.columns(3)
            for i, elemento in enumerate(elementos):
                with cols[i % 3]:
                    if st.button(f"📁 {elemento}", key=f"btn_{elemento}", use_container_width=True):
                        st.session_state.ruta.append(elemento)
                        st.session_state.nivel += 1
                        st.rerun()
        
        else:  # Estamos en Cubículos
            cols = st.columns(3)
            for i, elemento in enumerate(elementos):
                with cols[i % 3]:
                    if st.button(f"📍 {elemento}", key=f"cubiculo_{elemento}", use_container_width=True):
                        st.session_state.cubiculo_id = obtener_id_cubiculo(elemento, st.session_state.ruta)
                        st.rerun()

        st.divider()

        # Formulario para agregar elemento
        with st.expander("➕ Agregar nuevo", expanded=False):
            nombre_nuevo = st.text_input(f"Nombre del nuevo {HIERARCHY_SINGULAR[st.session_state.nivel].lower()}")
            
            if st.button("Crear", key="crear_elemento"):
                if nombre_nuevo and nombre_nuevo not in elementos:
                    agregar_elemento_bd(st.session_state.nivel, st.session_state.ruta, nombre_nuevo)
                    st.success(f"✅ {nombre_nuevo} creado exitosamente")
                    st.rerun()
                elif nombre_nuevo in elementos:
                    st.error("⚠️ Este elemento ya existe")
                else:
                    st.error("⚠️ Por favor ingresa un nombre")

        # Selector de eliminación
        if elementos:
            st.markdown("---")
            st.subheader(f"🗑️ Eliminar {HIERARCHY_LEVELS[st.session_state.nivel].lower()}")
            elemento_a_eliminar = st.selectbox(
                f"Selecciona {HIERARCHY_SINGULAR[st.session_state.nivel].lower()} para eliminar",
                ["-- Selecciona --"] + elementos,
                key=f"select_eliminar_{st.session_state.nivel}"
            )
            if elemento_a_eliminar != "-- Selecciona --" and st.button("Eliminar seleccionado", key=f"btn_eliminar_{st.session_state.nivel}"):
                st.session_state.pending_eliminar = {
                    "nombre": elemento_a_eliminar,
                    "nivel": st.session_state.nivel,
                    "ruta": list(st.session_state.ruta)
                }

            if st.session_state.get("pending_eliminar") and st.session_state.pending_eliminar["nivel"] == st.session_state.nivel:
                objetivo = st.session_state.pending_eliminar["nombre"]
                st.warning(
                    f"⚠️ ¿Estás seguro de que quieres eliminar '{objetivo}' y todos sus elementos descendientes? Esta acción no se puede deshacer."
                )
                col_confirmar, col_cancelar = st.columns([1, 1])
                with col_confirmar:
                    if st.button("✅ Sí, eliminar", key=f"confirmar_eliminacion_{st.session_state.nivel}"):
                        try:
                            eliminar_elemento_jerarquico(objetivo, st.session_state.nivel, st.session_state.pending_eliminar["ruta"])
                            st.success(f"✅ '{objetivo}' y todos sus elementos descendientes han sido eliminados.")
                            del st.session_state.pending_eliminar
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al eliminar: {str(e)}")
                with col_cancelar:
                    if st.button("❌ Cancelar", key=f"cancelar_eliminacion_{st.session_state.nivel}"):
                        del st.session_state.pending_eliminar
                        st.rerun()

        # Renombrar elemento en el nivel actual
        if elementos:
            st.markdown("---")
            st.subheader(f"✏️ Renombrar {HIERARCHY_SINGULAR[st.session_state.nivel].lower()}")
            elemento_a_renombrar = st.selectbox(
                f"Selecciona {HIERARCHY_SINGULAR[st.session_state.nivel].lower()} para renombrar",
                ["-- Selecciona --"] + elementos,
                key="select_renombrar_elemento"
            )
            nuevo_nombre = st.text_input("Nuevo nombre", key="nuevo_nombre_elemento")
            if elemento_a_renombrar != "-- Selecciona --" and st.button("Guardar nombre", key="btn_renombrar_elemento"):
                if not nuevo_nombre:
                    st.error(f"⚠️ Ingresa un nuevo nombre para el {HIERARCHY_SINGULAR[st.session_state.nivel].lower()}")
                elif nuevo_nombre in elementos:
                    st.error(f"⚠️ Ya existe un {HIERARCHY_SINGULAR[st.session_state.nivel].lower()} con ese nombre")
                else:
                    try:
                        renombrar_elemento_jerarquico(elemento_a_renombrar, nuevo_nombre, st.session_state.nivel, st.session_state.ruta)
                        st.success(f"✅ {HIERARCHY_SINGULAR[st.session_state.nivel]} '{elemento_a_renombrar}' renombrado a '{nuevo_nombre}'")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al renombrar: {str(e)}")

# ============ PÁGINA BÚSQUEDA ============
elif pagina == "🔍 Buscar":
    st.markdown("<div class='main-header'><h1>🔍 Buscar activos</h1></div>", 
                unsafe_allow_html=True)

    if st.session_state.get('reset_filters', False):
        reiniciar_filtros_busqueda()
        st.session_state.reset_filters = False

    texto_busqueda = st.text_input("Buscar por nombre, código, etc.", value=st.session_state.texto_busqueda, key="texto_busqueda")

    # Filtros jerárquicos
    estados = obtener_opciones_nivel(0, [])

    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 1.2])
    with col1:
        estado_seleccionado = st.selectbox(
            "Estado",
            ["-- Todos --"] + estados,
            index=(estados.index(st.session_state.filtro_estado) + 1) if st.session_state.filtro_estado in estados else 0,
            key="filtro_estado"
        )

    if estado_seleccionado == "-- Todos --":
        st.session_state.filtro_ciudad = "-- Todos --"
        st.session_state.filtro_plantel = "-- Todos --"
        st.session_state.filtro_edificio = "-- Todos --"
        st.session_state.filtro_cubiculo = "-- Todos --"

    ciudades = obtener_opciones_nivel(1, [estado_seleccionado]) if estado_seleccionado != "-- Todos --" else []
    with col2:
        ciudad_seleccionada = st.selectbox(
            "Ciudad",
            ["-- Todos --"] + ciudades,
            index=(ciudades.index(st.session_state.filtro_ciudad) + 1) if st.session_state.filtro_ciudad in ciudades else 0,
            key="filtro_ciudad",
            disabled=(estado_seleccionado == "-- Todos --")
        )

    if ciudad_seleccionada == "-- Todos --":
        st.session_state.filtro_plantel = "-- Todos --"
        st.session_state.filtro_edificio = "-- Todos --"
        st.session_state.filtro_cubiculo = "-- Todos --"

    planteles = obtener_opciones_nivel(2, [estado_seleccionado, ciudad_seleccionada]) if ciudad_seleccionada != "-- Todos --" else []
    with col3:
        plantel_seleccionado = st.selectbox(
            "Plantel",
            ["-- Todos --"] + planteles,
            index=(planteles.index(st.session_state.filtro_plantel) + 1) if st.session_state.filtro_plantel in planteles else 0,
            key="filtro_plantel",
            disabled=(ciudad_seleccionada == "-- Todos --")
        )

    if plantel_seleccionado == "-- Todos --":
        st.session_state.filtro_edificio = "-- Todos --"
        st.session_state.filtro_cubiculo = "-- Todos --"

    edificios = obtener_opciones_nivel(3, [estado_seleccionado, ciudad_seleccionada, plantel_seleccionado]) if plantel_seleccionado != "-- Todos --" else []
    with col4:
        edificio_seleccionado = st.selectbox(
            "Edificio",
            ["-- Todos --"] + edificios,
            index=(edificios.index(st.session_state.filtro_edificio) + 1) if st.session_state.filtro_edificio in edificios else 0,
            key="filtro_edificio",
            disabled=(plantel_seleccionado == "-- Todos --")
        )

    if edificio_seleccionado == "-- Todos --":
        st.session_state.filtro_cubiculo = "-- Todos --"

    col5, col6, col7, col8 = st.columns([1.1, 1.1, 1.1, 1.1])
    with col5:
        cubiculos = obtener_opciones_nivel(4, [estado_seleccionado, ciudad_seleccionada, plantel_seleccionado, edificio_seleccionado]) if edificio_seleccionado != "-- Todos --" else []
        cubiculo_seleccionado = st.selectbox(
            "Cubículo",
            ["-- Todos --"] + cubiculos,
            index=(cubiculos.index(st.session_state.filtro_cubiculo) + 1) if st.session_state.filtro_cubiculo in cubiculos else 0,
            key="filtro_cubiculo",
            disabled=(edificio_seleccionado == "-- Todos --")
        )

    with col6:
        encargados = obtener_todos_encargados()
        opciones_encargados = ["-- Todos --"] + [e['nombre'] for e in encargados]
        encargado_seleccionado = st.selectbox(
            "Encargado",
            opciones_encargados,
            index=(opciones_encargados.index(st.session_state.filtro_encargado) if st.session_state.filtro_encargado in opciones_encargados else 0),
            key="filtro_encargado"
        )

    with col7:
        empleados = obtener_todos_empleados()
        opciones_empleados = ["-- Todos --"] + [e['nombre'] for e in empleados]
        empleado_seleccionado = st.selectbox(
            "Empleado",
            opciones_empleados,
            index=(opciones_empleados.index(st.session_state.filtro_empleado) if st.session_state.filtro_empleado in opciones_empleados else 0),
            key="filtro_empleado"
        )

    with col8:
        tipos_activos = obtener_todos_tipos_activos()
        opciones_tipos = ["-- Todos --"] + [t['nombre'] for t in tipos_activos]
        tipo_activo_seleccionado = st.selectbox(
            "Tipo de activo",
            opciones_tipos,
            index=(opciones_tipos.index(st.session_state.filtro_tipo_activo) if st.session_state.filtro_tipo_activo in opciones_tipos else 0),
            key="filtro_tipo_activo"
        )

    col9, col10 = st.columns([1.2, 1.2])
    with col9:
        presencia_opciones = ["-- Todos --", "Presentes", "No presentes"]
        filtro_presencia = st.selectbox(
            "Estado",
            presencia_opciones,
            index=presencia_opciones.index(st.session_state.filtro_presencia) if st.session_state.filtro_presencia in presencia_opciones else 0,
            key="filtro_presencia"
        )

    col_buttons1, col_buttons2 = st.columns(2)
    with col_buttons1:
        if st.button("🧹 Limpiar filtros", use_container_width=True, key="limpiar_filtros"):
            st.session_state.reset_filters = True
            st.rerun()

    with col_buttons2:
        if st.button("🔍 Buscar", use_container_width=True, key="buscar_filtros"):
            ruta_filtro = []
            if estado_seleccionado != "-- Todos --":
                ruta_filtro.append(estado_seleccionado)
            if ciudad_seleccionada != "-- Todos --":
                ruta_filtro.append(ciudad_seleccionada)
            if plantel_seleccionado != "-- Todos --":
                ruta_filtro.append(plantel_seleccionado)
            if edificio_seleccionado != "-- Todos --":
                ruta_filtro.append(edificio_seleccionado)
            if cubiculo_seleccionado != "-- Todos --":
                ruta_filtro.append(cubiculo_seleccionado)

            tipo_activo_id = next((t['id'] for t in tipos_activos if t['nombre'] == tipo_activo_seleccionado), None)
            st.session_state.resultados_busqueda = buscar_activos_por_criterios(
                texto_busqueda,
                encargado_seleccionado if encargado_seleccionado != "-- Todos --" else None,
                empleado_seleccionado if empleado_seleccionado != "-- Todos --" else None,
                ruta_filtro,
                tipo_activo_id
            )

    st.divider()
    if st.session_state.resultados_busqueda is not None:
        resultados_filtrados = st.session_state.resultados_busqueda
        if st.session_state.filtro_presencia == "Presentes":
            resultados_filtrados = [
                disp for disp in resultados_filtrados
                if disp.get('presente')
            ]
        elif st.session_state.filtro_presencia == "No presentes":
            resultados_filtrados = [
                disp for disp in resultados_filtrados
                if not disp.get('presente')
            ]

        if resultados_filtrados:
            st.markdown("### Resultados encontrados:")
            for disp in resultados_filtrados:
                with st.expander(f" {disp.get('clave_activo', 'N/A')} - {disp.get('descripcion_activo', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Clave:** {disp.get('clave_activo', 'N/A')}")
                        st.write(f"**Descripción:** {disp.get('descripcion_activo', 'N/A')}")
                        st.write(f"**Tipo:** {disp.get('tipo_nombre', 'Sin tipo')}")
                        st.write(f"**Número de inventario:** {disp.get('numero_inventario', 'N/A')}")
                    with col2:
                        st.write(f"**Encargado:** {disp.get('encargado_nombre', 'N/A')}")
                        st.write(f"**Empleado:** {disp.get('empleado_nombre', 'N/A')}")
                        st.write(f"**Presente:** {'Sí' if disp.get('presente') else 'No'}")
                    st.write(f"**Ubicación:** {disp.get('ubicacion', 'N/A')}")
                    ubicacion = disp.get('ubicacion', '')
                    if ' > ' in ubicacion:
                        if st.button("📍 Ir al Cubículo", key=f"go_to_cubiculo_{disp.get('numero_inventario')}"):
                            ruta = ubicacion.split(' > ')
                            if len(ruta) >= 5:
                                cubiculo_nombre = ruta[-1]
                                ruta_sin_cubiculo = ruta[:-1]
                                cubiculo_id = obtener_id_cubiculo(cubiculo_nombre, ruta_sin_cubiculo)
                                if cubiculo_id:
                                    st.session_state.ruta = ruta_sin_cubiculo
                                    st.session_state.cubiculo_id = cubiculo_id
                                    st.session_state.nivel = len(HIERARCHY_LEVELS) - 1
                                    st.session_state.change_to_inicio = True
                                    st.rerun()
                                else:
                                    st.error("No se pudo encontrar el cubículo")
                            else:
                                st.error("Ubicación incompleta")
                    else:
                        st.write("Ubicación no disponible para navegación")
        else:
            st.info("No se encontraron activos")

# ============ PÁGINA MANTENIMIENTO ============
elif pagina == "🔧 Mantenimiento":
    st.markdown("<div class='main-header'><h1>🔧 Mantenimiento de Base de Datos</h1></div>", 
                unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🧹 Limpiar Datos", "📊 Estadísticas"])

    with tab1:
        st.markdown("<div class='section-header'><b>🧹 Limpieza de Datos</b></div>", 
                    unsafe_allow_html=True)
        
        st.markdown("### Activos Huérfanos")
        st.write("Los activos huérfanos son aquellos que están asociados a cubículos que ya no existen en la base de datos.")
        
        if st.button("🔍 Buscar Activos Huérfanos", use_container_width=True):
            huerfanos = obtener_activos_huerfanos()
            if huerfanos:
                st.warning(f"⚠️ Se encontraron {len(huerfanos)} activos huérfanos:")
                
                for disp in huerfanos:
                    with st.expander(f"📦 {disp.get('clave_activo', 'N/A')} - {disp.get('descripcion_activo', 'N/A')} (Inv: {disp.get('numero_inventario')})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Clave:** {disp.get('clave_activo', 'N/A')}")
                            st.write(f"**Número de inventario:** {disp.get('numero_inventario')}")
                        with col2:
                            st.write(f"**ID del Cubículo (inválido):** {disp.get('cubiculo_id')}")
                            st.write(f"**Encargado:** {disp.get('encargado_nombre', 'N/A')}")
                
                if st.button("🗑️ Eliminar Todos los Activos Huérfanos", use_container_width=True, type="primary"):
                    eliminados = eliminar_activos_huerfanos()
                    if eliminados > 0:
                        st.success(f"✅ Se eliminaron {eliminados} activos huérfanos exitosamente")
                        st.rerun()
                    else:
                        st.info("No se encontraron activos huérfanos para eliminar")
            else:
                st.success("✅ No se encontraron activos huérfanos")

    with tab2:
        st.markdown("<div class='section-header'><b>📊 Estadísticas del Sistema</b></div>", 
                    unsafe_allow_html=True)
        
        # Obtener estadísticas básicas
        with sqlite3.connect("inventario.db") as conn:
            cursor = conn.cursor()
            
            # Contar elementos por tabla
            cursor.execute("SELECT COUNT(*) FROM estados")
            estados_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ciudades")
            ciudades_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM planteles")
            planteles_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM edificios")
            edificios_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cubiculos")
            cubiculos_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM activos")
            activos_asignados_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM encargados")
            encargados_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM empleados")
            empleados_count = cursor.fetchone()[0]
            
            # activos huérfanos
            huerfanos_count = len(obtener_activos_huerfanos())
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Estados", estados_count)
            st.metric("Ciudades", ciudades_count)
            st.metric("Planteles", planteles_count)
            st.metric("Edificios", edificios_count)
        
        with col2:
            st.metric("Cubículos", cubiculos_count)
            st.metric("Activos asignados", activos_asignados_count)
            st.metric("Encargados", encargados_count)
            st.metric("Empleados", empleados_count)
            st.metric("Activos huérfanos", huerfanos_count, delta=-huerfanos_count if huerfanos_count > 0 else None)

# ============ PÁGINA ENCARGADOS ============
elif pagina == "👥 Encargados":
    st.markdown("<div class='main-header'><h1>👥 Gestión de Encargados</h1></div>", 
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Agregar", "Editar/Eliminar"])

    with tab1:
        st.markdown("<div class='section-header'><b>Encargados Registrados</b></div>", 
                    unsafe_allow_html=True)
        encargados = obtener_todos_encargados()
        
        if encargados:
            for enc in encargados:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{enc['nombre']}**")
                with col2:
                    if enc.get('correo'):
                        st.write(f"📧 {enc['correo']}")
                    if enc.get('telefono'):
                        st.write(f"📱 {enc['telefono']}")
                with col3:
                    st.write(f"ID: {enc['id']}")
                st.divider()
        else:
            st.info("No hay encargados registrados")

    with tab2:
        st.markdown("<div class='section-header'><b>Agregar Nuevo Encargado</b></div>", 
                    unsafe_allow_html=True)
        
        nombre = st.text_input("Nombre completo")
        correo = st.text_input("Correo electrónico")
        telefono = st.text_input("Teléfono")

        if st.button("🆕 Agregar Encargado", key="agregar_enc"):
            if nombre:
                agregar_encargado(nombre, correo, telefono)
                st.success(f"✅ Encargado '{nombre}' agregado exitosamente")
                st.rerun()
            else:
                st.error("⚠️ El nombre es obligatorio")

    with tab3:
        st.markdown("<div class='section-header'><b>Editar o Eliminar</b></div>", 
                    unsafe_allow_html=True)
        
        encargados = obtener_todos_encargados()
        opciones = {e['nombre']: e for e in encargados}
        
        if opciones:
            enc_seleccionado = st.selectbox("Selecciona un encargado", list(opciones.keys()), key="select_enc_edit")
            enc = opciones[enc_seleccionado]
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.expander("✏️ Editar"):
                    nombre_new = st.text_input("Nombre", enc['nombre'], key="edit_nombre")
                    correo_new = st.text_input("Correo", enc.get('correo', ''), key="edit_correo")
                    telefono_new = st.text_input("Teléfono", enc.get('telefono', ''), key="edit_telefono")
                    
                    if st.button("💾 Guardar cambios"):
                        actualizar_encargado(enc['id'], nombre_new, correo_new, telefono_new)
                        st.success("✅ Encargado actualizado")
                        st.rerun()
            
            with col2:
                with st.expander("🗑️ Eliminar", expanded=False):
                    st.warning(f"¿Eliminar a '{enc_seleccionado}'?")
                    if st.button("🗑️ Confirmar eliminación", key="confirmar_eliminar"):
                        eliminar_encargado(enc['id'])
                        st.success("✅ Encargado eliminado")
                        st.rerun()
        else:
            st.info("No hay encargados para editar")

# ============ PÁGINA EMPLEADOS ============
elif pagina == "🧑 Empleados":
    st.markdown("<div class='main-header'><h1>🧑 Gestión de Empleados</h1></div>", 
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Agregar", "Editar/Eliminar"])

    with tab1:
        st.markdown("<div class='section-header'><b>Empleados Registrados</b></div>", 
                    unsafe_allow_html=True)
        empleados = obtener_todos_empleados()
        
        if empleados:
            for emp in empleados:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{emp['nombre']}**")
                with col2:
                    if emp.get('correo'):
                        st.write(f"📧 {emp['correo']}")
                    if emp.get('telefono'):
                        st.write(f"📱 {emp['telefono']}")
                with col3:
                    st.write(f"ID: {emp['id']}")
                st.divider()
        else:
            st.info("No hay empleados registrados")

    with tab2:
        st.markdown("<div class='section-header'><b>Agregar Nuevo Empleado</b></div>", 
                    unsafe_allow_html=True)
        
        nombre = st.text_input("Nombre completo")
        correo = st.text_input("Correo electrónico")
        telefono = st.text_input("Teléfono")

        if st.button("🆕 Agregar Empleado", key="agregar_emp"):
            if nombre:
                agregar_empleado(nombre, correo, telefono)
                st.success(f"✅ Empleado '{nombre}' agregado exitosamente")
                st.rerun()
            else:
                st.error("⚠️ El nombre es obligatorio")

    with tab3:
        st.markdown("<div class='section-header'><b>Editar o Eliminar</b></div>", 
                    unsafe_allow_html=True)
        
        empleados = obtener_todos_empleados()
        opciones = {e['nombre']: e for e in empleados}
        
        if opciones:
            emp_seleccionado = st.selectbox("Selecciona un empleado", list(opciones.keys()), key="select_emp_edit")
            emp = opciones[emp_seleccionado]
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.expander("✏️ Editar"):
                    nombre_new = st.text_input("Nombre", emp['nombre'], key="edit_emp_nombre")
                    correo_new = st.text_input("Correo", emp.get('correo', ''), key="edit_emp_correo")
                    telefono_new = st.text_input("Teléfono", emp.get('telefono', ''), key="edit_emp_telefono")
                    
                    if st.button("💾 Guardar cambios", key="btn_guardar_emp"):
                        actualizar_empleado(emp['id'], nombre_new, correo_new, telefono_new)
                        st.success("✅ Empleado actualizado")
                        st.rerun()
            
            with col2:
                with st.expander("🗑️ Eliminar", expanded=False):
                    st.warning(f"¿Eliminar a '{emp_seleccionado}'?")
                    if st.button("🗑️ Confirmar eliminación", key="confirmar_eliminar_emp"):
                        eliminar_empleado(emp['id'])
                        st.success("✅ Empleado eliminado")
                        st.rerun()
        else:
            st.info("No hay empleados para editar")

# ============ PÁGINA TIPOS DE ACTIVOS ============
elif pagina == "📦 Tipos de Activos":
    st.markdown("<div class='main-header'><h1>📦 Gestión de Tipos de Activos</h1></div>", 
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Agregar", "Editar/Eliminar"])

    with tab1:
        st.markdown("<div class='section-header'><b>Tipos de Activos Registrados</b></div>", 
                    unsafe_allow_html=True)
        tipos = obtener_todos_tipos_activos()
        
        if tipos:
            for t in tipos:
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.write(f"**{t['nombre']}**")
                with col2:
                    st.write(f"{t.get('descripcion', 'Sin descripción')}")
                st.divider()
        else:
            st.warning("No se encontraron tipos de activos registrados.")

    with tab2:
        st.markdown("<div class='section-header'><b>Agregar Nuevo Tipo de Activo</b></div>", 
                    unsafe_allow_html=True)
        
        nombre_tipo = st.text_input("Nombre del tipo")
        descripcion_tipo = st.text_area("Descripción")

        if st.button("🆕 Agregar Tipo de Activo", key="agregar_tipo"):
            if nombre_tipo.strip():
                agregar_tipo_activo(nombre_tipo.strip(), descripcion_tipo.strip())
                st.success(f"✅ Tipo de activo agregado exitosamente")
                st.rerun()
            else:
                st.error("El nombre es obligatorio")

    with tab3:
        st.markdown("<div class='section-header'><b>Editar o Eliminar Tipo de Activo</b></div>", 
                    unsafe_allow_html=True)
        
        tipos = obtener_todos_tipos_activos()
        opciones = {t['nombre']: t for t in tipos}
        
        if opciones:
            tipo_seleccionado = st.selectbox("Selecciona un tipo de activo", list(opciones.keys()), key="select_tipo_edit")
            t = opciones[tipo_seleccionado]
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.expander("Editar"):
                    nombre_new = st.text_input("Nombre", t.get('nombre', ''), key="edit_tipo_nombre")
                    descripcion_new = st.text_area("Descripción", t.get('descripcion', ''), key="edit_tipo_desc")
                    
                    if st.button("Guardar cambios", key="btn_guardar_tipo"):
                        actualizar_tipo_activo(t['id'], nombre_new, descripcion_new)
                        st.success("Tipo de activo actualizado")
                        st.rerun()
            
            with col2:
                with st.expander("Eliminar", expanded=False):
                    st.warning(f"¿Eliminar tipo de activo '{t['nombre']}'?")
                    if st.button("Confirmar eliminación", key="confirmar_eliminar_tipo"):
                        eliminar_tipo_activo(t['id'])
                        st.success("Tipo de activo eliminado")
                        st.rerun()
        else:
            st.info("No hay tipos de activos para editar")

# ============ PÁGINA ACTIVOS BASE ============
elif pagina == "📋 Activos":
    st.markdown("<div class='main-header'><h1> Gestión de Activos</h1></div>", 
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Agregar", "Editar/Eliminar"])

    # --- Listar Activos ---
    with tab1:
        st.markdown("<div class='section-header'><b>Activos Registrados</b></div>", 
                    unsafe_allow_html=True)
        activos = obtener_todos_activos()
        
        if activos:
            for a in activos:
                col1, col2 = st.columns([2, 3])
                with col1:
                    st.write(f"**{a['clave']}**")
                with col2:
                    st.write(f"Tipo: {a.get('tipo_nombre', 'Sin tipo')} - {a.get('descripcion', 'Sin descripción')}")
                st.divider()
        else:
            st.warning("No se encontraron activos registrados.")

    # --- Agregar Activo ---
    with tab2:
        st.markdown("<div class='section-header'><b>Agregar Nuevo Activo</b></div>", 
                    unsafe_allow_html=True)

        tipos_activos = obtener_todos_tipos_activos()
        opciones_tipos = [t['nombre'] for t in tipos_activos]
        tipo_seleccionado = st.selectbox("Tipo de activo", opciones_tipos, key="tipo_activo")

        descripcion = st.text_area("Descripción del activo")

        if st.button("🆕 Agregar Activo", key="agregar_activo"):
            if descripcion.strip():
                tipo_id = next((t['id'] for t in tipos_activos if t['nombre'] == tipo_seleccionado), None)
                clave = agregar_activo(descripcion.strip(), tipo_id)
                st.success(f"✅ Activo agregado exitosamente con clave {clave}")
                st.rerun()
            else:
                st.error("La descripción es obligatoria")

    # --- Editar / Eliminar Activo ---
    with tab3:
        st.markdown("<div class='section-header'><b>Editar o Eliminar Activo</b></div>", 
                    unsafe_allow_html=True)

        activos = obtener_todos_activos()
        opciones = {f"{a['clave']} - {a['descripcion'][:50]}...": a for a in activos}

        if opciones:
            activo_seleccionado = st.selectbox("Selecciona un activo", list(opciones.keys()), key="select_activo_edit")
            a = opciones[activo_seleccionado]

            col1, col2 = st.columns(2)

            with col1:
                with st.expander("Editar"):
                    descripcion_new = st.text_area("Descripción", a.get('descripcion', ''), key="edit_activo_desc")
                    
                    tipos_activos = obtener_todos_tipos_activos()
                    opciones_tipos = [t['nombre'] for t in tipos_activos]
                    tipo_actual = next((t['nombre'] for t in tipos_activos if t['id'] == a.get('tipo_activo_id')), None)
                    tipo_seleccionado = st.selectbox("Tipo de activo", opciones_tipos, index=opciones_tipos.index(tipo_actual) if tipo_actual else 0, key="edit_activo_tipo")

                    if st.button("Guardar cambios", key="btn_guardar_activo"):
                        tipo_id = next((t['id'] for t in tipos_activos if t['nombre'] == tipo_seleccionado), None)
                        actualizar_activo(a['numero_inventario'], descripcion_new, tipo_id)
                        st.success("Activo actualizado")
                        st.rerun()

            with col2:
                with st.expander("Eliminar", expanded=False):
                    st.warning(f"¿Eliminar activo '{a['clave']}'?")
                    if st.button("Confirmar eliminación", key="confirmar_eliminar_activo"):
                        eliminar_activo(a['numero_inventario'])
                        st.success("Activo eliminado")
                        st.rerun()
        else:
            st.info("No hay activos para editar")
