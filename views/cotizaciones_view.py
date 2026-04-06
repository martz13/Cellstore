from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QSize
import qtawesome as qta
from database.connection import get_connection
from datetime import datetime
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QColor
from views.generador_pdf import GeneradorPDF
from views.generador_ticket import GeneradorTicket

class CotizacionesView(QWidget):
    senal_editar_cotizacion = Signal(int)
    def __init__(self,usuario_id=1):
        super().__init__()
        self.usuario_id = usuario_id
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area principal
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(20, 20, 20, 20)
        self.layout_container.setSpacing(15)

        # --- TÍTULO ---
        title = QLabel("GESTIÓN DE COTIZACIONES")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        self.layout_container.addWidget(title)

        # ================= SECCIÓN: COTIZACIONES DE HOY =================
        lbl_hoy = QLabel("COTIZACIONES DE HOY")
        lbl_hoy.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        self.layout_container.addWidget(lbl_hoy)

        self.table_hoy = QTableWidget()
        self.table_hoy.setColumnCount(7)
        self.table_hoy.setHorizontalHeaderLabels(["ID", "Cliente", "Usuario", "Inversión", "Precio Total", "Ganancia", "Acciones"])
        self.table_hoy.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_hoy.verticalHeader().setVisible(False)
        self.table_hoy.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_hoy.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #2077D4; border: 1px solid #2077D4;")
        self.table_hoy.setFixedHeight(250)
        self.layout_container.addWidget(self.table_hoy)

        # Caja de totales del día
        self.frame_totales = QFrame()
        self.frame_totales.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: rgba(15,15,20,200);")
        layout_totales = QVBoxLayout(self.frame_totales)
        
        self.lbl_total_reparaciones = QLabel("Total Cotizaciones: 0")
        self.lbl_total_precio = QLabel("Precio Total: $0.00")
        self.lbl_total_ganancia = QLabel("Ganancia Total del Día: $0.00")
        
        estilo_totales = "color: white; font-size: 14px;"
        self.lbl_total_reparaciones.setStyleSheet(estilo_totales)
        self.lbl_total_precio.setStyleSheet(estilo_totales)
        self.lbl_total_ganancia.setStyleSheet(estilo_totales)
        
        layout_totales.addWidget(self.lbl_total_reparaciones)
        layout_totales.addWidget(self.lbl_total_precio)
        layout_totales.addWidget(self.lbl_total_ganancia)

        # Alinear la caja de totales a la derecha
        lay_h_totales = QHBoxLayout()
        lay_h_totales.addStretch()
        lay_h_totales.addWidget(self.frame_totales)
        self.layout_container.addLayout(lay_h_totales)

        # ================= SECCIÓN: HISTORIAL DE COTIZACIONES =================
        lbl_historial = QLabel("HISTORIAL DE COTIZACIONES")
        lbl_historial.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px; margin-top: 20px;")
        self.layout_container.addWidget(lbl_historial)

        # Contenedor dinámico para los acordeones
        self.historial_layout = QVBoxLayout()
        self.historial_layout.setSpacing(10)
        self.layout_container.addLayout(self.historial_layout)
        
        self.layout_container.addStretch() # Empuja todo hacia arriba
        
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        self.cargar_datos()

    def auto_rechazar_pendientes(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM cotizaciones_maestro 
                WHERE estado = 'Pendiente' AND DATE(fecha_hora) < DATE('now', 'localtime')
            """)
            pendientes = cursor.fetchall()

            for p in pendientes:
                c_id = p[0]
                cursor.execute("UPDATE cotizaciones_maestro SET estado = 'Rechazada' WHERE id = ?", (c_id,))
                
                # --- MODIFICACIÓN: Cambiar el "1" duro por self.usuario_id ---
                cursor.execute("""
                    INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
                    VALUES (?, ?, ?, 'COTIZACION')
                """, (self.usuario_id, f"Cotización {c_id} ahora es rechazada por cambio automático", c_id))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error auto-rechazando pendientes: {e}")

    def cargar_datos(self):
        # 1. Ejecutar la regla de negocio de limpieza de días anteriores
        self.auto_rechazar_pendientes()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # --- 2. CARGAR COTIZACIONES DE HOY ---
            # Agregamos c.estado a la consulta
            cursor.execute("""
                SELECT c.id, c.cliente_nombre, u.nombre, c.total_inversion, c.total_precio_final, c.total_ganancia, c.estado 
                FROM cotizaciones_maestro c
                JOIN usuarios u ON c.usuario_id = u.id
                WHERE DATE(c.fecha_hora) = DATE('now', 'localtime')
                ORDER BY c.id DESC
            """)
            cotizaciones_hoy = cursor.fetchall()

            self.table_hoy.setRowCount(0)
            total_reparaciones = 0
            suma_precio = 0.0
            suma_ganancia = 0.0

            for idx, cot in enumerate(cotizaciones_hoy):
                self.table_hoy.insertRow(idx)
                estado = cot[6]

                # Solo sumar si está Aceptada
                if estado == 'Aceptada':
                    total_reparaciones += 1
                    suma_precio += cot[4]
                    suma_ganancia += cot[5]

                item_id = QTableWidgetItem(str(cot[0]))
                
                # Colores desvanecidos según el estado
                if estado == 'Aceptada':
                    item_id.setBackground(QColor(40, 167, 69, 60)) # Verde
                elif estado == 'Rechazada':
                    item_id.setBackground(QColor(220, 53, 69, 60)) # Rojo
                else:
                    item_id.setBackground(QColor(255, 193, 7, 60)) # Amarillo (Pendiente)

                items = [
                    item_id,
                    QTableWidgetItem(cot[1]),
                    QTableWidgetItem(cot[2]),
                    QTableWidgetItem(f"${cot[3]:.2f}"),
                    QTableWidgetItem(f"${cot[4]:.2f}"),
                    QTableWidgetItem(f"${cot[5]:.2f}")
                ]
                for col, item in enumerate(items):
                    self.table_hoy.setItem(idx, col, item)

                # Acciones (Hoy: Ticket, PDF, Editar)
                widget_acciones = QWidget()
                lay_acciones = QHBoxLayout(widget_acciones)
                lay_acciones.setContentsMargins(0,0,0,0)

                btn_ticket = self.crear_boton_accion('fa5s.receipt', '#2077D4', "Ticket")
                btn_pdf = self.crear_boton_accion('fa5s.file-pdf', '#ff4d4d', "PDF")
                btn_editar = self.crear_boton_accion('fa5s.edit', '#f0ad4e', "Editar")

                # REEMPLAZAR ESTO:
                btn_ticket.clicked.connect(lambda *args, cid=cot[0]: GeneradorTicket.generar_ticket(self, cid))
                #btn_pdf.clicked.connect(lambda *args, cid=cot[0]: self.accion_placeholder(f"Generar PDF para ID {cid}"))
                # REEMPLAZA ESTA LÍNEA (Cotizaciones de hoy)
                btn_pdf.clicked.connect(lambda *args, cid=cot[0]: GeneradorPDF.generar_cotizacion(self, cid))
                btn_editar.clicked.connect(lambda *args, cid=cot[0]: self.senal_editar_cotizacion.emit(cid))

                lay_acciones.addWidget(btn_ticket)
                lay_acciones.addWidget(btn_pdf)
                lay_acciones.addWidget(btn_editar)
                self.table_hoy.setCellWidget(idx, 6, widget_acciones)

            # Actualizar caja de totales (Solo refleja Aceptadas)
            self.lbl_total_reparaciones.setText(f"Total Cotizaciones Aceptadas: {total_reparaciones}")
            self.lbl_total_precio.setText(f"Precio Total: ${suma_precio:.2f}")
            self.lbl_total_ganancia.setText(f"Ganancia Total del Día: ${suma_ganancia:.2f}")

            # --- 3. CARGAR HISTORIAL (DÍAS PASADOS) ---
            for i in reversed(range(self.historial_layout.count())): 
                widget = self.historial_layout.itemAt(i).widget()
                if widget is not None: widget.deleteLater()

            # Agregamos c.estado a la consulta del historial
            cursor.execute("""
                SELECT DATE(c.fecha_hora) as fecha, c.id, c.cliente_nombre, u.nombre, c.total_inversion, c.total_precio_final, c.total_ganancia, c.estado 
                FROM cotizaciones_maestro c
                JOIN usuarios u ON c.usuario_id = u.id
                WHERE DATE(c.fecha_hora) < DATE('now', 'localtime')
                ORDER BY fecha DESC, c.id DESC
            """)
            historial = cursor.fetchall()
            conn.close()

            datos_por_fecha = {}
            for fila in historial:
                fecha = fila[0]
                if fecha not in datos_por_fecha:
                    datos_por_fecha[fecha] = []
                datos_por_fecha[fecha].append(fila)

            for fecha, cotizaciones in datos_por_fecha.items():
                self.crear_acordeon(fecha, cotizaciones)

        except Exception as e:
            print(f"Error cargando cotizaciones: {e}")

    def crear_boton_accion(self, icono, color, tooltip):
        btn = QPushButton()
        btn.setIcon(qta.icon(icono, color=color))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("background: transparent; border: none;")
        btn.setToolTip(tooltip)
        return btn

    def accion_placeholder(self, mensaje):
        QMessageBox.information(self, "Acción en Desarrollo", f"{mensaje}\n\nAgregar lógica aquí.")

    def crear_acordeon(self, fecha_str, cotizaciones):
        # Convertir fecha YYYY-MM-DD a un formato amigable
        try:
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            fecha_formateada = f"{fecha_obj.day} de {meses[fecha_obj.month - 1]}, {fecha_obj.year}"
        except:
            fecha_formateada = fecha_str

        # --- MODIFICACIÓN: Calcular totales SOLO de las Aceptadas ---
        aceptadas = [c for c in cotizaciones if c[7] == 'Aceptada']
        tot_rep = len(aceptadas)
        tot_precio = sum(c[5] for c in aceptadas)
        tot_ganancia = sum(c[6] for c in aceptadas)
        texto_resumen = f"[{tot_rep} Reparaciones, ${tot_precio:.2f} Total, ${tot_ganancia:.2f} Ganancia]"

        # Botón Header (El que se presiona para desplegar)
        btn_header = QPushButton(f"  {fecha_formateada}       {texto_resumen}")
        btn_header.setIcon(qta.icon('fa5s.chevron-down', color='#2077D4'))
        btn_header.setStyleSheet("""
            QPushButton {
                background-color: rgba(20, 20, 30, 255); color: white; border: 1px solid #2077D4;
                border-radius: 5px; padding: 10px; text-align: left; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: rgba(32, 119, 212, 100); }
        """)
        btn_header.setCursor(Qt.PointingHandCursor)

        # Contenedor de la tabla
        tabla_contenedor = QWidget()
        tabla_contenedor.setVisible(False)
        lay_tabla = QVBoxLayout(tabla_contenedor)
        lay_tabla.setContentsMargins(0, 0, 0, 10)

        

        tabla = QTableWidget()
        tabla.setColumnCount(7)
        tabla.setHorizontalHeaderLabels(["ID", "Cliente", "Usuario", "Inversión", "Precio Total", "Ganancia", "Acciones"])
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #555; border: 1px solid #555;")
        
        altura_estimada = 35 + (len(cotizaciones) * 35)
        tabla.setFixedHeight(altura_estimada if altura_estimada < 250 else 250)

        # --- MODIFICACIÓN: Llenar la tabla con TODAS las cotizaciones y pintar colores ---
        tabla.setRowCount(0)
        for idx, cot in enumerate(cotizaciones):
            tabla.insertRow(idx)
            estado = cot[7]
            
            item_id = QTableWidgetItem(str(cot[1]))
            # Colorear según estado
            if estado == 'Aceptada':
                item_id.setBackground(QColor(40, 167, 69, 60)) # Verde
            elif estado == 'Rechazada':
                item_id.setBackground(QColor(220, 53, 69, 60)) # Rojo
            else:
                item_id.setBackground(QColor(255, 193, 7, 60)) # Amarillo

            items = [
                item_id,
                QTableWidgetItem(cot[2]),
                QTableWidgetItem(cot[3]),
                QTableWidgetItem(f"${cot[4]:.2f}"),
                QTableWidgetItem(f"${cot[5]:.2f}"),
                QTableWidgetItem(f"${cot[6]:.2f}")
            ]
            for col, item in enumerate(items):
                tabla.setItem(idx, col, item)

            # Acciones (Historial: SOLO Ticket y PDF)
            widget_acciones = QWidget()
            lay_acciones = QHBoxLayout(widget_acciones)
            lay_acciones.setContentsMargins(0,0,0,0)

            btn_ticket = self.crear_boton_accion('fa5s.receipt', '#2077D4', "Ticket")
            btn_pdf = self.crear_boton_accion('fa5s.file-pdf', '#ff4d4d', "PDF")

            # CORRECCIÓN: En el historial, el ID siempre es cot[1]
            btn_ticket.clicked.connect(lambda *args, cid=cot[1]: GeneradorTicket.generar_ticket(self, cid))
            btn_pdf.clicked.connect(lambda *args, cid=cot[1]: GeneradorPDF.generar_cotizacion(self, cid))
            
            lay_acciones.addWidget(btn_ticket)
            lay_acciones.addWidget(btn_pdf)
            lay_acciones.addStretch() 
            
            tabla.setCellWidget(idx, 6, widget_acciones)

        lay_tabla.addWidget(tabla)

        def toggle_acordeon():
            es_visible = tabla_contenedor.isVisible()
            tabla_contenedor.setVisible(not es_visible)
            if es_visible:
                btn_header.setIcon(qta.icon('fa5s.chevron-down', color='#2077D4'))
            else:
                btn_header.setIcon(qta.icon('fa5s.chevron-up', color='#2077D4'))

        btn_header.clicked.connect(toggle_acordeon)

        self.historial_layout.addWidget(btn_header)
        self.historial_layout.addWidget(tabla_contenedor)