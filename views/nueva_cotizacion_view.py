from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QComboBox, 
                               QScrollArea, QFrame, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QDoubleValidator
import qtawesome as qta
from database.connection import get_connection

class NuevaCotizacionView(QWidget):
    def __init__(self, usuario_id=1):
        super().__init__()
        self.usuario_id = usuario_id # ID del usuario que inició sesión
        self.lista_reparaciones = [] # Memoria temporal para la tabla
        self.cotizacion_editando_id = None # Controla si es nueva o estamos editando

        # Layout principal de la vista
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Crear el Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # Contenedor principal dentro del scroll
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Estilos reutilizables
        self.style_input = "background-color: rgba(15, 15, 20, 200); border: 1px solid #555; padding: 8px; border-radius: 4px; color: white;"
        self.style_readonly = "background-color: rgba(10, 10, 15, 150); border: 1px dashed #555; padding: 8px; border-radius: 4px; color: #aaa;"
        
        # --- TÍTULO ---
        title = QLabel("NUEVA COTIZACIÓN")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # --- SECCIÓN 1: DATOS DEL CLIENTE ---
        lbl_cliente = QLabel("DATOS DEL CLIENTE")
        lbl_cliente.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_cliente)

        grid_cliente = QGridLayout()
        self.txt_cliente_nombre = QLineEdit()
        self.txt_cliente_nombre.setStyleSheet(self.style_input)
        self.txt_cliente_telefono = QLineEdit()
        self.txt_cliente_telefono.setStyleSheet(self.style_input)
        
        grid_cliente.addWidget(QLabel("Nombre"), 0, 0)
        grid_cliente.addWidget(self.txt_cliente_nombre, 0, 1)
        grid_cliente.addWidget(QLabel("Num teléfono"), 0, 2)
        grid_cliente.addWidget(self.txt_cliente_telefono, 0, 3)
        layout.addLayout(grid_cliente)

        # --- SECCIÓN 2: DATOS DE REPARACIÓN ---
        lbl_reparacion = QLabel("DATOS DE REPARACIÓN")
        lbl_reparacion.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_reparacion)

        grid_rep = QGridLayout()
        grid_rep.setSpacing(10)

        # Fila 1: Marca y Modelo
        self.txt_marca = QLineEdit()
        self.txt_marca.setStyleSheet(self.style_input)
        self.txt_modelo = QLineEdit()
        self.txt_modelo.setStyleSheet(self.style_input)
        grid_rep.addWidget(QLabel("Marca"), 0, 0)
        grid_rep.addWidget(self.txt_marca, 0, 1)
        grid_rep.addWidget(QLabel("Modelo"), 0, 2)
        grid_rep.addWidget(self.txt_modelo, 0, 3)

        # Fila 2: Textos amplios (Qué se va a reparar y Observaciones)
        self.txt_reparacion = QTextEdit()
        self.txt_reparacion.setStyleSheet(self.style_input)
        self.txt_reparacion.setFixedHeight(80) # Más espacio
        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setStyleSheet(self.style_input)
        self.txt_observaciones.setFixedHeight(80) # Más espacio
        
        grid_rep.addWidget(QLabel("¿Qué se va a reparar?"), 1, 0)
        grid_rep.addWidget(self.txt_reparacion, 1, 1)
        grid_rep.addWidget(QLabel("Observaciones"), 1, 2)
        grid_rep.addWidget(self.txt_observaciones, 1, 3)

        # Fila 3: Fecha y Hora (Automáticas y Bloqueadas)
        self.txt_fecha = QLineEdit()
        self.txt_fecha.setReadOnly(True)
        self.txt_fecha.setStyleSheet(self.style_readonly)
        
        self.txt_hora = QLineEdit()
        self.txt_hora.setReadOnly(True)
        self.txt_hora.setStyleSheet(self.style_readonly)
        
        # Iconos de candado
        self.txt_fecha.addAction(qta.icon('fa5s.lock', color='#555'), QLineEdit.TrailingPosition)
        self.txt_hora.addAction(qta.icon('fa5s.lock', color='#555'), QLineEdit.TrailingPosition)

        grid_rep.addWidget(QLabel("Fecha: [Automática]"), 2, 0)
        grid_rep.addWidget(self.txt_fecha, 2, 1)
        grid_rep.addWidget(QLabel("Hora: [Automática]"), 2, 2)
        grid_rep.addWidget(self.txt_hora, 2, 3)

        # Fila 4: Precios
        self.txt_inversion = QLineEdit()
        self.txt_precio_final = QLineEdit()
        self.txt_ganancia = QLineEdit()
        
        # Validadores para solo aceptar números decimales
        validator = QDoubleValidator(0.00, 99999.99, 2)
        self.txt_inversion.setValidator(validator)
        self.txt_precio_final.setValidator(validator)
        
        self.txt_inversion.setStyleSheet(self.style_input)
        self.txt_precio_final.setStyleSheet(self.style_input)
        self.txt_ganancia.setStyleSheet(self.style_readonly)
        self.txt_ganancia.setReadOnly(True)
        
        # Conectar eventos para calcular ganancia al vuelo
        self.txt_inversion.textChanged.connect(self.calcular_ganancia_individual)
        self.txt_precio_final.textChanged.connect(self.calcular_ganancia_individual)

        # Layout horizontal para los precios
        lay_precios = QHBoxLayout()
        lay_precios.addWidget(QLabel("Inversión ($):"))
        lay_precios.addWidget(self.txt_inversion)
        lay_precios.addWidget(QLabel("Precio Final ($):"))
        lay_precios.addWidget(self.txt_precio_final)
        lay_precios.addWidget(QLabel("Ganancia ($):"))
        lay_precios.addWidget(self.txt_ganancia)

        layout.addLayout(grid_rep)
        layout.addLayout(lay_precios)

        # --- BOTÓN AGREGAR REPARACIÓN ---
       # --- NUEVO: ESTADO DE EDICIÓN ---
        self.editando_index = None 

        # --- BOTONES DE ACCIÓN PARA REPARACIÓN ---
        botones_layout = QHBoxLayout()
        
        self.btn_cancelar_edicion = QPushButton("CANCELAR EDICIÓN")
        self.btn_cancelar_edicion.setStyleSheet("""
            QPushButton {
                background-color: #555555; color: white; border: none;
                border-radius: 5px; padding: 10px; font-weight: bold;
            }
            QPushButton:hover { background-color: #777777; }
        """)
        self.btn_cancelar_edicion.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar_edicion.hide() # Oculto por defecto
        self.btn_cancelar_edicion.clicked.connect(self.cancelar_edicion)

        self.btn_agregar = QPushButton("  + AGREGAR REPARACIÓN")
        self.style_btn_agregar = """
            QPushButton {
                background-color: rgba(32, 119, 212, 0.8);
                color: white; border: 1px solid #2077D4;
                border-radius: 5px; padding: 10px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #2077D4; }
        """
        self.btn_agregar.setStyleSheet(self.style_btn_agregar)
        self.btn_agregar.setCursor(Qt.PointingHandCursor)
        self.btn_agregar.clicked.connect(self.agregar_reparacion)
        
        botones_layout.addWidget(self.btn_cancelar_edicion)
        botones_layout.addWidget(self.btn_agregar)
        layout.addLayout(botones_layout)
        # --- TABLA DE REPARACIONES ---
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Marca", "Modelo", "Reparación", "Inversión", "P. Final", "Ganancia", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #2077D4; border: 1px solid #2077D4;")
        self.table.setFixedHeight(200) # Altura fija para no ocupar toda la pantalla
        layout.addWidget(self.table)

        # --- SECCIÓN 3: TOTALES Y CIERRE (FOOTER) ---
        footer_frame = QFrame()
        footer_frame.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: rgba(15,15,20,200);")
        footer_layout = QGridLayout(footer_frame)
        footer_layout.setContentsMargins(15, 15, 15, 15)

        self.cb_estado = QComboBox()
        self.cb_estado.addItems(["Pendiente", "Aceptada", "Rechazada"])
        self.cb_estado.setStyleSheet(self.style_input)

        self.txt_total = QLineEdit("0.00")
        self.txt_total.setReadOnly(True)
        self.txt_total.setStyleSheet(self.style_readonly)

        self.txt_adelanto = QLineEdit()
        self.txt_adelanto.setValidator(validator)
        self.txt_adelanto.setStyleSheet(self.style_input)
        self.txt_adelanto.textChanged.connect(self.calcular_restante)

        self.txt_falta = QLineEdit("0.00")
        self.txt_falta.setReadOnly(True)
        self.txt_falta.setStyleSheet(self.style_readonly)

        self.cb_metodo = QComboBox()
        self.cb_metodo.addItems(["Efectivo", "Tarjeta"])
        self.cb_metodo.setStyleSheet(self.style_input)

        footer_layout.addWidget(QLabel("Estado:"), 0, 0)
        footer_layout.addWidget(self.cb_estado, 0, 1)
        footer_layout.addWidget(QLabel("Precio total: $"), 0, 2)
        footer_layout.addWidget(self.txt_total, 0, 3)

        footer_layout.addWidget(QLabel("Adelanto ($):"), 1, 0)
        footer_layout.addWidget(self.txt_adelanto, 1, 1)
        footer_layout.addWidget(QLabel("Falta por pagar: $"), 1, 2)
        footer_layout.addWidget(self.txt_falta, 1, 3)
        footer_layout.addWidget(QLabel("Método de pago:"), 1, 4)
        footer_layout.addWidget(self.cb_metodo, 1, 5)

        layout.addWidget(footer_frame)

        # --- BOTÓN GUARDAR COTIZACIÓN ---
        # --- BOTONES FINALES DE COTIZACIÓN ---
        lay_botones_finales = QHBoxLayout()
        
        self.btn_cancelar_cotizacion = QPushButton("CANCELAR EDICIÓN")
        self.btn_cancelar_cotizacion.setStyleSheet("""
            QPushButton {
                background-color: #555; color: white; border: none;
                border-radius: 5px; padding: 15px; font-weight: bold; font-size: 16px;
            }
            QPushButton:hover { background-color: #777; }
        """)
        self.btn_cancelar_cotizacion.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar_cotizacion.hide() # Oculto por defecto
        self.btn_cancelar_cotizacion.clicked.connect(self.cancelar_edicion_maestra)

        self.btn_guardar = QPushButton("GUARDAR COTIZACIÓN")
        self.estilo_btn_guardar = """
            QPushButton {
                background-color: #2077D4; color: white; border: none;
                border-radius: 5px; padding: 15px; font-weight: bold; font-size: 16px;
            }
            QPushButton:hover { background-color: #1a5ea8; }
        """
        self.btn_guardar.setStyleSheet(self.estilo_btn_guardar)
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self.guardar_cotizacion)
        
        lay_botones_finales.addWidget(self.btn_cancelar_cotizacion)
        lay_botones_finales.addWidget(self.btn_guardar)
        layout.addLayout(lay_botones_finales)
        # Ensamblar Scroll Area
        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        # Iniciar reloj
        self.actualizar_reloj()

    # ================= MÉTODOS DE LÓGICA =================

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        self.txt_fecha.setText(ahora.toString("yyyy-MM-dd"))
        self.txt_hora.setText(ahora.toString("HH:mm:ss"))

    def calcular_ganancia_individual(self):
        try:
            inv = float(self.txt_inversion.text() or 0)
            final = float(self.txt_precio_final.text() or 0)
            ganancia = final - inv
            self.txt_ganancia.setText(f"{ganancia:.2f}")
        except ValueError:
            self.txt_ganancia.setText("0.00")

    def agregar_reparacion(self):
        marca = self.txt_marca.text().strip()
        modelo = self.txt_modelo.text().strip()
        reparacion = self.txt_reparacion.toPlainText().strip()
        inv_str = self.txt_inversion.text()
        final_str = self.txt_precio_final.text()

        if not all([marca, modelo, reparacion, inv_str, final_str]):
            QMessageBox.warning(self, "Campos incompletos", "Llena todos los campos de reparación.")
            return

        try:
            inv = float(inv_str)
            final = float(final_str)
            ganancia = final - inv
            
            rep_data = {
                "marca": marca, "modelo": modelo, "reparacion": reparacion,
                "observaciones": self.txt_observaciones.toPlainText().strip(),
                "inversion": inv, "final": final, "ganancia": ganancia
            }
            
            # --- NUEVO: LÓGICA DE EDICIÓN VS AGREGAR ---
            if self.editando_index is not None:
                self.lista_reparaciones[self.editando_index] = rep_data
                self.cancelar_edicion() # Esto limpia y restaura los botones
            else:
                self.lista_reparaciones.append(rep_data)
                self.limpiar_formulario_reparacion()
            
            self.refrescar_tabla()
            self.calcular_totales_cotizacion()

        except ValueError:
            QMessageBox.warning(self, "Error", "Valores numéricos inválidos.")

    def cargar_reparacion_para_edicion(self, index):
        self.editando_index = index
        rep = self.lista_reparaciones[index]
        
        # Cargar datos a los inputs
        self.txt_marca.setText(rep["marca"])
        self.txt_modelo.setText(rep["modelo"])
        self.txt_reparacion.setText(rep["reparacion"])
        self.txt_observaciones.setText(rep["observaciones"])
        self.txt_inversion.setText(str(rep["inversion"]))
        self.txt_precio_final.setText(str(rep["final"]))
        
        # Cambiar apariencia de botones
        self.btn_agregar.setText("  GUARDAR CAMBIOS")
        self.btn_agregar.setStyleSheet("""
            QPushButton {
                background-color: #e68a00; color: white; border: 1px solid #ff9900;
                border-radius: 5px; padding: 10px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #ff9900; }
        """)
        self.btn_cancelar_edicion.show()
        
    def cancelar_edicion(self):
        self.editando_index = None
        self.limpiar_formulario_reparacion()
        self.btn_agregar.setText("  + AGREGAR REPARACIÓN")
        self.btn_agregar.setStyleSheet(self.style_btn_agregar)
        self.btn_cancelar_edicion.hide()


    def refrescar_tabla(self):
        self.table.setRowCount(0)
        for idx, rep in enumerate(self.lista_reparaciones):
            self.table.insertRow(idx)
            
            # --- NUEVO: REEMPLAZAR \n POR <br> PARA EL HTML ---
            reparacion_formateada = rep['reparacion'].replace('\n', '<br>')
            observaciones_formateadas = rep['observaciones'].replace('\n', '<br>')
            
            tooltip_html = f"""
            <div style='background-color: rgba(20, 20, 25, 250); padding: 10px; border: 2px solid #2077D4; border-radius: 5px;'>
                <h3 style='color: #2077D4; margin-top: 0; margin-bottom: 8px;'>Detalles de Reparación</h3>
                <p style='color: white; margin: 2px;'><b>Marca:</b> {rep['marca']}</p>
                <p style='color: white; margin: 2px;'><b>Modelo:</b> {rep['modelo']}</p>
                <p style='color: white; margin: 2px;'><b>Reparación:</b><br>{reparacion_formateada}</p>
                <hr style='border: 1px solid #555;'>
                <p style='color: #ccc; margin: 2px;'><b>Observaciones:</b><br>{observaciones_formateadas}</p>
            </div>
            """

            items = [
                QTableWidgetItem(str(idx + 1)),
                QTableWidgetItem(rep["marca"]),
                QTableWidgetItem(rep["modelo"]),
                QTableWidgetItem(rep["reparacion"].replace('\n', ' ')), # Quita saltos en la vista de celda
                QTableWidgetItem(f"${rep['inversion']:.2f}"),
                QTableWidgetItem(f"${rep['final']:.2f}"),
                QTableWidgetItem(f"${rep['ganancia']:.2f}")
            ]

            for col_idx, item in enumerate(items):
                item.setToolTip(tooltip_html)
                self.table.setItem(idx, col_idx, item)

            # --- NUEVO: BOTONES EDITAR Y ELIMINAR ---
            btn_edit = QPushButton()
            btn_edit.setIcon(qta.icon('fa5s.edit', color='#2077D4'))
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet("background: transparent; border: none;")
            btn_edit.clicked.connect(lambda *args, index=idx: self.cargar_reparacion_para_edicion(index))

            btn_delete = QPushButton()
            btn_delete.setIcon(qta.icon('fa5s.trash-alt', color='#ff4d4d'))
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.setStyleSheet("background: transparent; border: none;")
            btn_delete.clicked.connect(lambda *args, index=idx: self.eliminar_reparacion(index))
            
            widget_action = QWidget()
            layout_action = QHBoxLayout(widget_action)
            layout_action.setContentsMargins(0,0,0,0)
            layout_action.addWidget(btn_edit)
            layout_action.addWidget(btn_delete)
            self.table.setCellWidget(idx, 7, widget_action)

    def eliminar_reparacion(self, index):
        self.lista_reparaciones.pop(index)
        self.refrescar_tabla()
        self.calcular_totales_cotizacion()

    def limpiar_formulario_reparacion(self):
        self.txt_marca.clear()
        self.txt_modelo.clear()
        self.txt_reparacion.clear()
        self.txt_observaciones.clear()
        self.txt_inversion.clear()
        self.txt_precio_final.clear()
        self.txt_ganancia.clear()
        self.txt_marca.setFocus() # Regresar el cursor

    def calcular_totales_cotizacion(self):
        total_inv = sum(r["inversion"] for r in self.lista_reparaciones)
        total_final = sum(r["final"] for r in self.lista_reparaciones)
        
        self.txt_total.setText(f"{total_final:.2f}")
        self.calcular_restante()

    def calcular_restante(self):
        try:
            total = float(self.txt_total.text() or 0)
            adelanto = float(self.txt_adelanto.text() or 0)
            falta = total - adelanto
            self.txt_falta.setText(f"{falta:.2f}")
        except ValueError:
            pass

    def guardar_cotizacion(self):
        cliente = self.txt_cliente_nombre.text().strip()
        tel = self.txt_cliente_telefono.text().strip()
        
        if not cliente or not tel:
            QMessageBox.warning(self, "Faltan datos", "Agrega el nombre y teléfono del cliente.")
            return
            
        if not self.lista_reparaciones:
            QMessageBox.warning(self, "Sin reparaciones", "Agrega al menos una reparación a la cotización.")
            return

        total_inversion = sum(r["inversion"] for r in self.lista_reparaciones)
        total_final = sum(r["final"] for r in self.lista_reparaciones)
        total_ganancia = sum(r["ganancia"] for r in self.lista_reparaciones)
        estado = self.cb_estado.currentText()
        metodo = self.cb_metodo.currentText()
        adelanto = float(self.txt_adelanto.text() or 0)
        restante = total_final - adelanto

        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if self.cotizacion_editando_id:
                # --- ACTUALIZAR COTIZACIÓN EXISTENTE ---
                cursor.execute("""
                    UPDATE cotizaciones_maestro 
                    SET cliente_nombre=?, cliente_telefono=?, total_inversion=?, total_precio_final=?, 
                        total_ganancia=?, estado=?, metodo_pago=?, monto_adelanto=?, monto_restante=?
                    WHERE id=?
                """, (cliente, tel, total_inversion, total_final, total_ganancia, estado, metodo, adelanto, restante, self.cotizacion_editando_id))
                
                # Eliminar detalles antiguos
                cursor.execute("DELETE FROM cotizaciones_detalle WHERE cotizacion_id=?", (self.cotizacion_editando_id,))
                cotizacion_id = self.cotizacion_editando_id
                
                # Registrar movimiento de edición
                accion_msj = f"Editó la cotización ID {cotizacion_id} (Nuevo estado: {estado})"
                cursor.execute("""
                    INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
                    VALUES (?, ?, ?, 'COTIZACION')
                """, (self.usuario_id, accion_msj, cotizacion_id))
                
                msj = f"Cotización #{cotizacion_id} actualizada correctamente."
                
            else:
                # --- NUEVA COTIZACIÓN ---
                cursor.execute("""
                    INSERT INTO cotizaciones_maestro 
                    (usuario_id, cliente_nombre, cliente_telefono, total_inversion, total_precio_final, total_ganancia, estado, metodo_pago, monto_adelanto, monto_restante)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (self.usuario_id, cliente, tel, total_inversion, total_final, total_ganancia, estado, metodo, adelanto, restante))
                cotizacion_id = cursor.lastrowid
                msj = f"Cotización #{cotizacion_id} guardada correctamente."
            
            # Insertar detalles (común a ambas rutas)
            for r in self.lista_reparaciones:
                cursor.execute("""
                    INSERT INTO cotizaciones_detalle 
                    (cotizacion_id, marca, modelo, trabajo_a_realizar, observaciones, inversion_pieza, precio_cliente, ganancia_neta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (cotizacion_id, r["marca"], r["modelo"], r["reparacion"], r["observaciones"], r["inversion"], r["final"], r["ganancia"]))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Éxito", msj)
            self.cancelar_edicion_maestra()  # Limpia el formulario y vuelve a modo "nuevo"

        except Exception as e:
            QMessageBox.critical(self, "Error BD", f"Error al guardar cotización:\n{e}")   

    # --- NUEVOS MÉTODOS PARA CARGAR Y LIMPIAR LA EDICIÓN ---
    def cargar_cotizacion_existente(self, cot_id):
        self.cotizacion_editando_id = cot_id
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Cargar datos del cliente y estado
            cursor.execute("SELECT cliente_nombre, cliente_telefono, estado, metodo_pago, monto_adelanto FROM cotizaciones_maestro WHERE id=?", (cot_id,))
            maestro = cursor.fetchone()
            if maestro:
                self.txt_cliente_nombre.setText(maestro[0])
                self.txt_cliente_telefono.setText(maestro[1])
                self.cb_estado.setCurrentText(maestro[2])
                self.cb_metodo.setCurrentText(maestro[3])
                self.txt_adelanto.setText(str(maestro[4]))

            # Cargar reparaciones
            cursor.execute("SELECT marca, modelo, trabajo_a_realizar, observaciones, inversion_pieza, precio_cliente, ganancia_neta FROM cotizaciones_detalle WHERE cotizacion_id=?", (cot_id,))
            detalles = cursor.fetchall()
            conn.close()

            self.lista_reparaciones.clear()
            for d in detalles:
                self.lista_reparaciones.append({
                    "marca": d[0], "modelo": d[1], "reparacion": d[2],
                    "observaciones": d[3], "inversion": d[4], "final": d[5], "ganancia": d[6]
                })
            
            self.refrescar_tabla()
            self.calcular_totales_cotizacion()
            
            # Cambiar apariencia de la vista a Modo Edición
            self.btn_guardar.setText("ACTUALIZAR COTIZACIÓN")
            self.btn_guardar.setStyleSheet("""
                QPushButton {
                    background-color: #e68a00; color: white; border: none;
                    border-radius: 5px; padding: 15px; font-weight: bold; font-size: 16px;
                }
                QPushButton:hover { background-color: #ff9900; }
            """)
            self.btn_cancelar_cotizacion.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la cotización: {e}")

    def cancelar_edicion_maestra(self):
        # Restaura la vista a su estado "Nuevo"
        self.cotizacion_editando_id = None
        self.txt_cliente_nombre.clear()
        self.txt_cliente_telefono.clear()
        self.txt_adelanto.clear()
        self.cb_estado.setCurrentIndex(0)
        self.cb_metodo.setCurrentIndex(0)
        self.lista_reparaciones.clear()
        self.refrescar_tabla()
        self.calcular_totales_cotizacion()
        self.actualizar_reloj()
        
        self.btn_guardar.setText("GUARDAR COTIZACIÓN")
        self.btn_guardar.setStyleSheet(self.estilo_btn_guardar)
        self.btn_cancelar_cotizacion.hide()
