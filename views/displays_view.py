from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QScrollArea, QFrame, 
                               QGridLayout, QRadioButton, QButtonGroup, QMessageBox,
                               QComboBox, QSpinBox, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator, QIntValidator, QColor, QFont
import qtawesome as qta
from database.connection import get_connection
from datetime import datetime
# Agrégalo en la parte superior, junto a tus otras importaciones
from views.generador_ticket import GeneradorTicket

# ================= MODAL DE HISTORIAL DE VENTAS =================
class HistorialVentasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Ventas de Displays")
        self.setFixedSize(850, 450) # Lo hice un poco más ancho
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        layout = QVBoxLayout(self)
        # ... (filtro de mes igual) ...
        lay_filtro = QHBoxLayout()
        lay_filtro.addWidget(QLabel("Filtrar por Mes:"))
        self.cb_mes = QComboBox()
        self.cb_mes.setStyleSheet("background-color: #222; color: white; border: 1px solid #555; padding: 5px;")
        self.cargar_meses_disponibles()
        self.cb_mes.currentIndexChanged.connect(self.cargar_ventas)
        lay_filtro.addWidget(self.cb_mes)
        lay_filtro.addStretch()
        layout.addLayout(lay_filtro)

        # TABLA ACTUALIZADA
        self.table_historial = QTableWidget()
        self.table_historial.setColumnCount(7) # Ahora son 7 columnas
        self.table_historial.setHorizontalHeaderLabels(["ID Venta", "Fecha", "Cliente", "Display", "Cant.", "Total", "Acciones"])
        self.table_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_historial.verticalHeader().setVisible(False)
        self.table_historial.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_historial.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #444; border: 1px solid #555;")
        layout.addWidget(self.table_historial)

        self.lbl_total_mes = QLabel("Total del Mes: $0.00")
        self.lbl_total_mes.setStyleSheet("font-size: 16px; font-weight: bold; color: #00e6e6;")
        self.lbl_total_mes.setAlignment(Qt.AlignRight)
        layout.addWidget(self.lbl_total_mes)
        self.cargar_ventas()

    def cargar_ventas(self):
        mes_seleccionado = self.cb_mes.currentData()
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Agregamos v.id y v.cliente_nombre a la consulta
            query = """
                SELECT v.id, v.fecha_hora, v.cliente_nombre, d.marca || ' ' || d.modelo, v.cantidad, v.total 
                FROM ventas_displays v
                JOIN inventario_displays d ON v.display_id = d.id
            """
            params = []
            if mes_seleccionado and mes_seleccionado != "TODOS":
                query += " WHERE strftime('%Y-%m', v.fecha_hora) = ?"
                params.append(mes_seleccionado)
                
            query += " ORDER BY v.fecha_hora DESC"
            cursor.execute(query, params)
            ventas = cursor.fetchall()
            conn.close()

            self.table_historial.setRowCount(0)
            suma_total = 0.0

            for idx, v in enumerate(ventas):
                self.table_historial.insertRow(idx)
                suma_total += v[5]
                
                f_str = v[1] # Simplificado por espacio
                cliente = v[2] if v[2] else "Público en General"

                items = [
                    QTableWidgetItem(str(v[0])),
                    QTableWidgetItem(f_str),
                    QTableWidgetItem(cliente),
                    QTableWidgetItem(v[3]),
                    QTableWidgetItem(str(v[4])),
                    QTableWidgetItem(f"${v[5]:.2f}")
                ]
                for col, item in enumerate(items):
                    self.table_historial.setItem(idx, col, item)

                # Agregar botón de Ticket
                btn_ticket = QPushButton()
                btn_ticket.setIcon(qta.icon('fa5s.receipt', color='#2077D4'))
                btn_ticket.setCursor(Qt.PointingHandCursor)
                btn_ticket.setStyleSheet("background: transparent; border: none;")
                btn_ticket.clicked.connect(lambda *args, vid=v[0]: GeneradorTicket.generar_ticket(self.parent(), vid, "DISPLAY"))
                
                self.table_historial.setCellWidget(idx, 6, btn_ticket)

            self.lbl_total_mes.setText(f"Total: ${suma_total:.2f}")
        except Exception as e:
            print("Error cargando historial:", e)

    def cargar_meses_disponibles(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT strftime('%Y-%m', fecha_hora) FROM ventas_displays ORDER BY fecha_hora DESC")
            meses = cursor.fetchall()
            conn.close()

            self.cb_mes.addItem("Todos los meses", "TODOS")
            for m in meses:
                mes_str = m[0]
                try:
                    f_obj = datetime.strptime(mes_str, '%Y-%m')
                    nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    nombre_amigable = f"{nombres[f_obj.month - 1]} {f_obj.year}"
                    self.cb_mes.addItem(nombre_amigable, mes_str)
                except:
                    self.cb_mes.addItem(mes_str, mes_str)
        except Exception as e:
            print("Error cargando meses:", e)

    



# ================= VISTA PRINCIPAL DE DISPLAYS =================
class DisplaysView(QWidget):
    def __init__(self, usuario_id=1):
        super().__init__()
        self.usuario_id = usuario_id
        self.display_seleccionado_id = None
        self.editando_display_id = None # NUEVO: Control para la edición
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(20, 20, 20, 20)
        self.layout_container.setSpacing(15)

        # --- TÍTULO Y BOTÓN DE HISTORIAL ---
        lay_titulo = QHBoxLayout()
        title = QLabel("GESTIÓN DE INVENTARIO DE DISPLAYS")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        lay_titulo.addWidget(title)
        
        btn_historial = QPushButton("  VER HISTORIAL DE VENTAS")
        btn_historial.setIcon(qta.icon('fa5s.history', color='black'))
        btn_historial.setStyleSheet("background-color: #f0ad4e; color: black; font-weight: bold; padding: 8px 15px; border-radius: 4px;")
        btn_historial.setCursor(Qt.PointingHandCursor)
        btn_historial.clicked.connect(self.abrir_historial_ventas)
        lay_titulo.addStretch()
        lay_titulo.addWidget(btn_historial)
        
        self.layout_container.addLayout(lay_titulo)

        # ================= 1. AÑADIR/EDITAR DISPLAY =================
        self.lbl_nuevo = QLabel("AÑADIR NUEVO DISPLAY A INVENTARIO")
        self.lbl_nuevo.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        self.layout_container.addWidget(self.lbl_nuevo)

        frame_add = QFrame()
        frame_add.setStyleSheet("border: 1px solid #2077D4; border-radius: 5px; background-color: rgba(15,15,20,200);")
        lay_add = QGridLayout(frame_add)
        lay_add.setContentsMargins(15, 15, 15, 15)

        estilo_input = "background-color: rgba(10,10,15,150); border: 1px solid #555; padding: 8px; color: white;"
        
        self.txt_marca = QLineEdit()
        self.txt_marca.setStyleSheet(estilo_input)
        self.txt_modelo = QLineEdit()
        self.txt_modelo.setStyleSheet(estilo_input)
        
        self.txt_cantidad = QLineEdit()
        self.txt_cantidad.setValidator(QIntValidator(0, 9999))
        self.txt_cantidad.setStyleSheet(estilo_input)
        
        self.txt_precio1 = QLineEdit()
        self.txt_precio1.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        self.txt_precio1.setStyleSheet(estilo_input)
        
        self.txt_precio2 = QLineEdit()
        self.txt_precio2.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        self.txt_precio2.setStyleSheet(estilo_input)

        lay_add.addWidget(QLabel("Marca", styleSheet="border:none;"), 0, 0)
        lay_add.addWidget(self.txt_marca, 1, 0)
        lay_add.addWidget(QLabel("Modelo", styleSheet="border:none;"), 0, 1)
        lay_add.addWidget(self.txt_modelo, 1, 1)
        lay_add.addWidget(QLabel("NO. PIEZAS", styleSheet="border:none;"), 0, 2)
        lay_add.addWidget(self.txt_cantidad, 1, 2)
        lay_add.addWidget(QLabel("Precio 1 (Mayorista)", styleSheet="border:none;"), 0, 3)
        lay_add.addWidget(self.txt_precio1, 1, 3)
        lay_add.addWidget(QLabel("Precio 2 (Cliente)", styleSheet="border:none;"), 0, 4)
        lay_add.addWidget(self.txt_precio2, 1, 4)

        # Botones de Guardar / Cancelar Edición
        lay_botones_form = QHBoxLayout()
        self.btn_cancelar_edicion = QPushButton("CANCELAR EDICIÓN")
        self.btn_cancelar_edicion.setStyleSheet("background-color: #555; color: white; font-weight: bold; padding: 10px; border-radius: 3px;")
        self.btn_cancelar_edicion.clicked.connect(self.cancelar_edicion)
        self.btn_cancelar_edicion.hide()

        self.btn_guardar_inv = QPushButton("GUARDAR EN INVENTARIO")
        self.btn_guardar_inv.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 10px; border-radius: 3px;")
        self.btn_guardar_inv.setCursor(Qt.PointingHandCursor)
        self.btn_guardar_inv.clicked.connect(self.guardar_display)
        
        lay_botones_form.addWidget(self.btn_cancelar_edicion)
        lay_botones_form.addWidget(self.btn_guardar_inv)
        
        lay_add.addLayout(lay_botones_form, 2, 0, 1, 5)

        self.layout_container.addWidget(frame_add)

        # ================= 1.5 FILTROS Y BÚSQUEDA =================
        lay_filtros = QHBoxLayout()
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por marca o modelo...")
        self.txt_buscar.setStyleSheet(estilo_input)
        self.txt_buscar.textChanged.connect(self.cargar_datos)

        self.cb_filtro = QComboBox()
        self.cb_filtro.addItems(["Todos los Displays", "Con Stock (> 0)", "Sin Stock (0)"])
        self.cb_filtro.setStyleSheet("background-color: #222; color: white; border: 1px solid #555; padding: 8px;")
        self.cb_filtro.currentIndexChanged.connect(self.cargar_datos)

        lay_filtros.addWidget(self.txt_buscar, stretch=3)
        lay_filtros.addWidget(self.cb_filtro, stretch=1)
        self.layout_container.addLayout(lay_filtros)

        # ================= 2. LISTA DE DISPLAYS =================
        lbl_lista = QLabel("LISTA DE DISPLAYS DISPONIBLES")
        lbl_lista.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        self.layout_container.addWidget(lbl_lista)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Marca", "Modelo", "NO. PIEZAS", "Precio 1 (Mayorista)", "Precio 2 (Cliente)", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #444; border: 1px solid #555; color: white;")
        self.table.setMinimumHeight(250)
        self.layout_container.addWidget(self.table)

        # ================= 3. CREAR VENTA =================
# ... (dentro de __init__ de DisplaysView) ...
        # ================= 3. CREAR VENTA =================
        lbl_venta = QLabel("CREAR VENTA DE DISPLAY Y REDUCIR STOCK")
        lbl_venta.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px; margin-top: 10px;")
        self.layout_container.addWidget(lbl_venta)

        frame_venta = QFrame()
        frame_venta.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: rgba(15,15,20,200);")
        lay_venta = QGridLayout(frame_venta)
        lay_venta.setContentsMargins(15, 15, 15, 15)

        estilo_bloqueado = "background-color: rgba(10,10,15,100); border: 1px solid #444; padding: 8px; color: #888;"
        estilo_input = "background-color: rgba(10,10,15,150); border: 1px solid #555; padding: 8px; color: white;"
        
        self.txt_venta_marca = QLineEdit()
        self.txt_venta_marca.setReadOnly(True)
        self.txt_venta_marca.setStyleSheet(estilo_bloqueado)
        
        self.txt_venta_modelo = QLineEdit()
        self.txt_venta_modelo.setReadOnly(True)
        self.txt_venta_modelo.setStyleSheet(estilo_bloqueado)

        # NUEVOS CAMPOS CLIENTE
        self.txt_venta_cliente = QLineEdit()
        self.txt_venta_cliente.setPlaceholderText("Opcional")
        self.txt_venta_cliente.setStyleSheet(estilo_input)
        
        self.txt_venta_tel = QLineEdit()
        self.txt_venta_tel.setPlaceholderText("Opcional")
        self.txt_venta_tel.setStyleSheet(estilo_input)

        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(1)
        self.spin_cantidad.setStyleSheet(estilo_input)

        self.radio_may = QRadioButton("Mayorista")
        self.radio_cli = QRadioButton("Cliente")
        self.radio_may.setStyleSheet("border: none; color: white;")
        self.radio_cli.setStyleSheet("border: none; color: white;")
        self.radio_may.setChecked(True)
        lay_radios = QHBoxLayout()
        lay_radios.addWidget(self.radio_may)
        lay_radios.addWidget(self.radio_cli)

        lay_venta.addWidget(QLabel("Marca", styleSheet="border:none;"), 0, 0)
        lay_venta.addWidget(self.txt_venta_marca, 1, 0)
        lay_venta.addWidget(QLabel("Modelo", styleSheet="border:none;"), 0, 1)
        lay_venta.addWidget(self.txt_venta_modelo, 1, 1)
        lay_venta.addWidget(QLabel("Cantidad", styleSheet="border:none;"), 0, 2)
        lay_venta.addWidget(self.spin_cantidad, 1, 2)
        lay_venta.addWidget(QLabel("Precio", styleSheet="border:none;"), 0, 3)
        lay_venta.addLayout(lay_radios, 1, 3)
        
        # Agregamos la fila del cliente abajo
        lay_venta.addWidget(QLabel("Cliente:", styleSheet="border:none;"), 2, 0)
        lay_venta.addWidget(self.txt_venta_cliente, 2, 1)
        lay_venta.addWidget(QLabel("Teléfono:", styleSheet="border:none;"), 2, 2)
        lay_venta.addWidget(self.txt_venta_tel, 2, 3)

        self.btn_confirmar_venta = QPushButton("CONFIRMAR VENTA, REDUCIR STOCK Y GENERAR TICKET")
        self.btn_confirmar_venta.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 10px; border: none; border-radius: 3px;")
        self.btn_confirmar_venta.setCursor(Qt.PointingHandCursor)
        self.btn_confirmar_venta.clicked.connect(self.procesar_venta)
        self.btn_confirmar_venta.setEnabled(False)
        lay_venta.addWidget(self.btn_confirmar_venta, 3, 0, 1, 4)
        # ...
##########################################
        self.layout_container.addWidget(frame_venta)
        self.layout_container.addStretch()
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        self.cargar_datos()

    def abrir_historial_ventas(self):
        dialog = HistorialVentasDialog(self)
        dialog.exec()

    def guardar_display(self):
        marca = self.txt_marca.text().strip().upper()
        modelo = self.txt_modelo.text().strip()
        cant_str = self.txt_cantidad.text().strip()
        p1_str = self.txt_precio1.text().strip()
        p2_str = self.txt_precio2.text().strip()

        if not all([marca, modelo, cant_str, p1_str, p2_str]):
            QMessageBox.warning(self, "Campos Vacíos", "Llena todos los campos para agregar al inventario.")
            return

        try:
            cant = int(cant_str)
            p1 = float(p1_str)
            p2 = float(p2_str)

            conn = get_connection()
            cursor = conn.cursor()

            if self.editando_display_id:
                # UPDATE
                cursor.execute("""
                    UPDATE inventario_displays 
                    SET marca=?, modelo=?, cantidad=?, precio_mayorista=?, precio_publico=? 
                    WHERE id=?
                """, (marca, modelo, cant, p1, p2, self.editando_display_id))
                
                log_msg = f"Actualizó display ID {self.editando_display_id} ({marca} {modelo})"
                msj_exito = "Display actualizado correctamente."
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO inventario_displays (marca, modelo, cantidad, precio_mayorista, precio_publico, activo)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (marca, modelo, cant, p1, p2))
                disp_id = cursor.lastrowid
                log_msg = f"Agregó {cant} piezas del display {marca} {modelo} al inventario."
                msj_exito = "Display agregado al inventario."
                self.editando_display_id = disp_id

            # Registrar movimiento
            cursor.execute("""
                INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
                VALUES (?, ?, ?, 'DISPLAY')
            """, (self.usuario_id, log_msg, self.editando_display_id))

            conn.commit()
            conn.close()

            self.cancelar_edicion() # Limpia y restaura la vista
            self.cargar_datos()
            QMessageBox.information(self, "Éxito", msj_exito)

        except Exception as e:
            QMessageBox.critical(self, "Error BD", f"Error guardando display:\n{e}")

    def cargar_datos(self):
        busqueda = self.txt_buscar.text().strip().lower()
        filtro_stock = self.cb_filtro.currentText()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # NUEVO: Solo seleccionamos los activos (activo = 1)
            query = "SELECT id, marca, modelo, cantidad, precio_mayorista, precio_publico FROM inventario_displays WHERE activo = 1"
            params = []

            if busqueda:
                query += " AND (LOWER(marca) LIKE ? OR LOWER(modelo) LIKE ?)"
                params.extend([f"%{busqueda}%", f"%{busqueda}%"])

            if filtro_stock == "Con Stock (> 0)":
                query += " AND cantidad > 0"
            elif filtro_stock == "Sin Stock (0)":
                query += " AND cantidad = 0"

            query += " ORDER BY marca ASC, modelo ASC"
            
            cursor.execute(query, params)
            displays = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            
            colores_marca = {
                'HONOR': QColor(212, 160, 23),
                'OPPO': QColor(40, 82, 163),
                'MOTOROLA': QColor(163, 21, 21)
            }
            
            marca_actual = None

            for disp in displays:
                marca = disp[1]
                
                if marca != marca_actual:
                    marca_actual = marca
                    idx = self.table.rowCount()
                    self.table.insertRow(idx)
                    
                    item_header = QTableWidgetItem(marca_actual)
                    item_header.setTextAlignment(Qt.AlignCenter)
                    font = QFont()
                    font.setBold(True)
                    item_header.setFont(font)
                    
                    color_bg = colores_marca.get(marca_actual.upper(), QColor(85, 85, 85))
                    item_header.setBackground(color_bg)
                    
                    self.table.setItem(idx, 0, item_header)
                    self.table.setSpan(idx, 0, 1, 6)

                idx = self.table.rowCount()
                self.table.insertRow(idx)
                
                items = [
                    QTableWidgetItem(disp[1]),
                    QTableWidgetItem(disp[2]),
                    QTableWidgetItem(str(disp[3])),
                    QTableWidgetItem(f"${disp[4]:.2f}"),
                    QTableWidgetItem(f"${disp[5]:.2f}")
                ]
                
                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(idx, col, item)

                # ================= BOTONES DE ACCIÓN (VENTA, EDITAR, ELIMINAR) =================
                widget_acciones = QWidget()
                lay_acciones = QHBoxLayout(widget_acciones)
                lay_acciones.setContentsMargins(0,0,0,0)
                lay_acciones.setSpacing(5)

                # Botón Crear Venta
                btn_venta = QPushButton("CREAR VENTA")
                btn_venta.setStyleSheet("background: transparent; color: #2077D4; font-weight: bold; border: 1px solid #2077D4; border-radius: 3px; padding: 2px;")
                btn_venta.setCursor(Qt.PointingHandCursor)
                if disp[3] <= 0:
                    btn_venta.setEnabled(False)
                    btn_venta.setStyleSheet("background: transparent; color: #555; border: 1px solid #555;")
                else:
                    btn_venta.clicked.connect(lambda *args, d=disp: self.preparar_venta(d))

                # Botón Editar
                btn_edit = QPushButton()
                btn_edit.setIcon(qta.icon('fa5s.edit', color='#f0ad4e'))
                btn_edit.setCursor(Qt.PointingHandCursor)
                btn_edit.setStyleSheet("background: transparent; border: none;")
                btn_edit.clicked.connect(lambda *args, d=disp: self.cargar_para_edicion(d))

                # Botón Eliminar
                btn_delete = QPushButton()
                btn_delete.setIcon(qta.icon('fa5s.trash-alt', color='#ff4d4d'))
                btn_delete.setCursor(Qt.PointingHandCursor)
                btn_delete.setStyleSheet("background: transparent; border: none;")
                btn_delete.clicked.connect(lambda *args, did=disp[0]: self.eliminar_display(did))

                lay_acciones.addWidget(btn_venta)
                lay_acciones.addWidget(btn_edit)
                lay_acciones.addWidget(btn_delete)
                self.table.setCellWidget(idx, 5, widget_acciones)

        except Exception as e:
            print(f"Error cargando displays: {e}")

    # --- NUEVOS MÉTODOS PARA EDICIÓN Y ELIMINACIÓN LÓGICA ---
    def cargar_para_edicion(self, disp_data):
        self.editando_display_id = disp_data[0]
        self.lbl_nuevo.setText("EDITANDO DISPLAY (INVENTARIO)")
        self.txt_marca.setText(disp_data[1])
        self.txt_modelo.setText(disp_data[2])
        self.txt_cantidad.setText(str(disp_data[3]))
        self.txt_precio1.setText(str(disp_data[4]))
        self.txt_precio2.setText(str(disp_data[5]))

        self.btn_guardar_inv.setText("ACTUALIZAR INVENTARIO")
        self.btn_guardar_inv.setStyleSheet("background-color: #f0ad4e; color: black; font-weight: bold; padding: 10px; border-radius: 3px;")
        self.btn_cancelar_edicion.show()

    def cancelar_edicion(self):
        self.editando_display_id = None
        self.lbl_nuevo.setText("AÑADIR NUEVO DISPLAY A INVENTARIO")
        self.txt_marca.clear()
        self.txt_modelo.clear()
        self.txt_cantidad.clear()
        self.txt_precio1.clear()
        self.txt_precio2.clear()

        self.btn_guardar_inv.setText("GUARDAR EN INVENTARIO")
        self.btn_guardar_inv.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 10px; border-radius: 3px;")
        self.btn_cancelar_edicion.hide()

    def eliminar_display(self, disp_id):
        respuesta = QMessageBox.question(self, "Confirmar", 
                                         "¿Eliminar este display del inventario? (No afectará al historial de ventas).", 
                                         QMessageBox.Yes | QMessageBox.No)
        if respuesta == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                # Borrado lógico: cambiamos activo a 0
                cursor.execute("UPDATE inventario_displays SET activo = 0 WHERE id = ?", (disp_id,))
                
                # Log de movimiento
                cursor.execute("""
                    INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
                    VALUES (?, ?, ?, 'DISPLAY')
                """, (self.usuario_id, f"Eliminó display ID {disp_id} del inventario.", disp_id))

                conn.commit()
                conn.close()
                self.cargar_datos()
                QMessageBox.information(self, "Eliminado", "El display ha sido removido del inventario.")
            except Exception as e:
                QMessageBox.critical(self, "Error BD", f"Error eliminando display:\n{e}")

    # --- MÉTODOS DE VENTA ---
    def preparar_venta(self, disp_data):
        self.display_seleccionado_id = disp_data[0]
        self.txt_venta_marca.setText(disp_data[1])
        self.txt_venta_modelo.setText(disp_data[2])
        self.stock_disponible = disp_data[3]
        self.precio_may = disp_data[4]
        self.precio_pub = disp_data[5]
        
        self.spin_cantidad.setMaximum(self.stock_disponible)
        self.spin_cantidad.setValue(1)
        
        self.btn_confirmar_venta.setEnabled(True)

    def procesar_venta(self):
        if not self.display_seleccionado_id: return

        self.spin_cantidad.clearFocus()
        cantidad_vender = self.spin_cantidad.value()

        if cantidad_vender > self.stock_disponible:
            QMessageBox.warning(self, "Stock Insuficiente", f"Solo hay {self.stock_disponible} disponibles.")
            self.spin_cantidad.setValue(self.stock_disponible)
            return

        cliente = self.txt_venta_cliente.text().strip()
        telefono = self.txt_venta_tel.text().strip()
        tipo_precio = "Mayorista" if self.radio_may.isChecked() else "Cliente"
        precio_unitario = self.precio_may if tipo_precio == "Mayorista" else self.precio_pub
        total_venta = precio_unitario * cantidad_vender
        
        marca = self.txt_venta_marca.text()
        modelo = self.txt_venta_modelo.text()

        respuesta = QMessageBox.question(self, "Confirmar Venta", 
                                         f"¿Vender {cantidad_vender} Display(s) {marca} {modelo}?\n"
                                         f"TOTAL: ${total_venta:.2f}", 
                                         QMessageBox.Yes | QMessageBox.No)
        
        if respuesta == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                cursor.execute("UPDATE inventario_displays SET cantidad = cantidad - ? WHERE id = ?", (cantidad_vender, self.display_seleccionado_id))
                
                cursor.execute("""
                    INSERT INTO ventas_displays (usuario_id, display_id, cantidad, precio_unitario, total, tipo_precio, cliente_nombre, cliente_telefono)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.usuario_id, self.display_seleccionado_id, cantidad_vender, precio_unitario, total_venta, tipo_precio, cliente, telefono))
                
                venta_id = cursor.lastrowid # Extraemos el ID de la venta generada

                log_msg = f"Vendió {cantidad_vender} display(s) {marca} {modelo} (Total: ${total_venta:.2f})"
                cursor.execute("""
                    INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
                    VALUES (?, ?, ?, 'VENTA_DISPLAY')
                """, (self.usuario_id, log_msg, self.display_seleccionado_id))

                conn.commit()
                conn.close()

                # Limpiar UI
                self.display_seleccionado_id = None
                self.txt_venta_marca.clear()
                self.txt_venta_modelo.clear()
                self.txt_venta_cliente.clear()
                self.txt_venta_tel.clear()
                self.spin_cantidad.setValue(1)
                self.btn_confirmar_venta.setEnabled(False)
                self.cargar_datos()

                # --- LANZAR EL GENERADOR DE TICKETS ---
                GeneradorTicket.generar_ticket(self, venta_id, "DISPLAY")

            except Exception as e:
                QMessageBox.critical(self, "Error BD", f"Error procesando venta:\n{e}")

