from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QScrollArea, QFrame, QMessageBox)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QDoubleValidator
import qtawesome as qta
from database.connection import get_connection
from datetime import datetime

class OtrosGastosView(QWidget):
    def __init__(self, usuario_id=1, nombre_usuario="Admin"):
        super().__init__()
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        
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

        # --- TÍTULO ---
        title = QLabel("GESTIÓN DE OTROS GASTOS")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        self.layout_container.addWidget(title)

        # ================= FORMULARIO NUEVO GASTO =================
        lbl_nuevo = QLabel("AGREGAR NUEVO GASTO")
        lbl_nuevo.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        self.layout_container.addWidget(lbl_nuevo)

        frame_form = QFrame()
        frame_form.setStyleSheet("border: 1px solid #2077D4; border-radius: 5px; background-color: rgba(15,15,20,200);")
        lay_form = QVBoxLayout(frame_form)
        lay_form.setContentsMargins(20, 20, 20, 20)

        # Fila 1: Descripción y Monto
        lay_fila1 = QHBoxLayout()
        self.txt_desc = QLineEdit()
        self.txt_desc.setStyleSheet("background-color: rgba(10,10,15,150); border: 1px solid #555; padding: 8px; color: white;")
        
        self.txt_monto = QLineEdit()
        self.txt_monto.setValidator(QDoubleValidator(0.00, 99999.99, 2))
        self.txt_monto.setStyleSheet("background-color: rgba(10,10,15,150); border: 1px solid #555; padding: 8px; color: white;")
        
        lay_col1 = QVBoxLayout()
        lay_col1.addWidget(QLabel("Descripción del Gasto"))
        lay_col1.addWidget(self.txt_desc)
        
        lay_col2 = QVBoxLayout()
        lay_col2.addWidget(QLabel("Monto ($)"))
        lay_col2.addWidget(self.txt_monto)
        
        lay_fila1.addLayout(lay_col1, stretch=3)
        lay_fila1.addLayout(lay_col2, stretch=1)
        lay_form.addLayout(lay_fila1)

        # Fila 2: Fecha y Usuario (Bloqueados)
        lay_fila2 = QHBoxLayout()
        estilo_bloqueado = "background-color: rgba(10,10,15,100); border: 1px solid #444; padding: 8px; color: #888;"
        
        self.txt_fecha = QLineEdit()
        self.txt_fecha.setReadOnly(True)
        self.txt_fecha.setStyleSheet(estilo_bloqueado)
        self.txt_fecha.addAction(qta.icon('fa5s.lock', color='#555'), QLineEdit.LeadingPosition)
        
        self.txt_usuario = QLineEdit(f"{self.nombre_usuario} [Automática]")
        self.txt_usuario.setReadOnly(True)
        self.txt_usuario.setStyleSheet(estilo_bloqueado)
        self.txt_usuario.addAction(qta.icon('fa5s.lock', color='#555'), QLineEdit.LeadingPosition)

        lay_col3 = QVBoxLayout()
        lay_col3.addWidget(QLabel("Fecha (No modificable) [Automática]"))
        lay_col3.addWidget(self.txt_fecha)

        lay_col4 = QVBoxLayout()
        lay_col4.addWidget(QLabel("Usuario (No modificable) [Automática]"))
        lay_col4.addWidget(self.txt_usuario)

        lay_fila2.addLayout(lay_col3)
        lay_fila2.addLayout(lay_col4)
        lay_form.addLayout(lay_fila2)

        # Botón Guardar
        self.btn_guardar = QPushButton("GUARDAR GASTO")
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #00e6e6; color: black; border: none;
                border-radius: 5px; padding: 12px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #00cccc; }
        """)
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self.guardar_gasto)
        lay_form.addWidget(self.btn_guardar)

        self.layout_container.addWidget(frame_form)

        # ================= LISTA DEL MES ACTUAL =================
        self.lbl_mes_actual = QLabel("LISTA DE OTROS GASTOS (MES ACTUAL)")
        self.lbl_mes_actual.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px; margin-top: 10px;")
        self.layout_container.addWidget(self.lbl_mes_actual)

        self.table_mes = QTableWidget()
        self.table_mes.setColumnCount(5)
        self.table_mes.setHorizontalHeaderLabels(["ID Gasto", "Descripción", "Monto", "Fecha", "Usuario"])
        self.table_mes.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_mes.verticalHeader().setVisible(False)
        self.table_mes.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_mes.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #2077D4; border: 1px solid #2077D4;")
        self.table_mes.setFixedHeight(200)
        self.layout_container.addWidget(self.table_mes)

        self.lbl_total_mes = QLabel("Total Gastos Mes: $0.00")
        self.lbl_total_mes.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.lbl_total_mes.setAlignment(Qt.AlignRight)
        self.layout_container.addWidget(self.lbl_total_mes)

        # ================= HISTORIAL MESES PASADOS =================
        lbl_historial = QLabel("HISTORIAL DE OTROS GASTOS")
        lbl_historial.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px; margin-top: 20px;")
        self.layout_container.addWidget(lbl_historial)

        self.historial_layout = QVBoxLayout()
        self.historial_layout.setSpacing(10)
        self.layout_container.addLayout(self.historial_layout)
        
        self.layout_container.addStretch()
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        self.actualizar_reloj()
        self.cargar_datos()

    def actualizar_reloj(self):
        ahora = QDateTime.currentDateTime()
        # Sacamos el texto fuera del formateador de Qt
        fecha_str = ahora.toString("dd MMM, yyyy") + " [Automática]"
        self.txt_fecha.setText(fecha_str)

    def guardar_gasto(self):
        desc = self.txt_desc.text().strip()
        monto_str = self.txt_monto.text().strip()

        if not desc or not monto_str:
            QMessageBox.warning(self, "Campos Vacíos", "Ingrese descripción y monto.")
            return

        try:
            monto = float(monto_str)
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO otros_gastos (usuario_id, descripcion, monto)
                VALUES (?, ?, ?)
            """, (self.usuario_id, desc, monto))
            
            conn.commit()
            conn.close()
            
            self.txt_desc.clear()
            self.txt_monto.clear()
            self.cargar_datos()
            QMessageBox.information(self, "Éxito", "Gasto registrado correctamente.")
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido.")
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))

    def cargar_datos(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Gastos del mes actual
            cursor.execute("""
                SELECT g.id, g.descripcion, g.monto, DATE(g.fecha_hora), u.nombre 
                FROM otros_gastos g
                JOIN usuarios u ON g.usuario_id = u.id
                WHERE strftime('%Y-%m', g.fecha_hora) = strftime('%Y-%m', 'now', 'localtime')
                ORDER BY g.id DESC
            """)
            gastos_mes = cursor.fetchall()

            self.table_mes.setRowCount(0)
            total_mes = 0.0

            for idx, gasto in enumerate(gastos_mes):
                self.table_mes.insertRow(idx)
                total_mes += gasto[2]
                
                # Formatear fecha
                f_obj = datetime.strptime(gasto[3], '%Y-%m-%d')
                f_str = f"{f_obj.day} {f_obj.strftime('%b')}, {f_obj.year}"

                items = [
                    QTableWidgetItem(str(gasto[0]).zfill(3)),
                    QTableWidgetItem(gasto[1]),
                    QTableWidgetItem(f"${gasto[2]:.2f}"),
                    QTableWidgetItem(f_str),
                    QTableWidgetItem(gasto[4])
                ]
                for col, item in enumerate(items):
                    self.table_mes.setItem(idx, col, item)

            self.lbl_total_mes.setText(f"Total Gastos Mes: ${total_mes:.2f}")

            # Limpiar historial
            for i in reversed(range(self.historial_layout.count())): 
                widget = self.historial_layout.itemAt(i).widget()
                if widget is not None: widget.deleteLater()

            # Gastos de meses pasados
            cursor.execute("""
                SELECT strftime('%Y-%m', g.fecha_hora) as mes_anio, g.id, g.descripcion, g.monto, DATE(g.fecha_hora), u.nombre 
                FROM otros_gastos g
                JOIN usuarios u ON g.usuario_id = u.id
                WHERE strftime('%Y-%m', g.fecha_hora) < strftime('%Y-%m', 'now', 'localtime')
                ORDER BY mes_anio DESC, g.id DESC
            """)
            historial = cursor.fetchall()
            conn.close()

            gastos_por_mes = {}
            for fila in historial:
                mes_key = fila[0]
                if mes_key not in gastos_por_mes:
                    gastos_por_mes[mes_key] = []
                gastos_por_mes[mes_key].append(fila)

            for mes_key, gastos in gastos_por_mes.items():
                self.crear_acordeon(mes_key, gastos)

        except Exception as e:
            print(f"Error cargando gastos: {e}")

    def crear_acordeon(self, mes_key, gastos):
        meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        meses_abrev = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        try:
            f_obj = datetime.strptime(mes_key, '%Y-%m')
            nombre_mes = f"{meses_nombres[f_obj.month - 1]}, {f_obj.year}"
        except:
            nombre_mes = mes_key

        tot_mes = sum(g[3] for g in gastos)
        
        btn_header = QPushButton(f"  {nombre_mes} [Total: ${tot_mes:.2f}]")
        btn_header.setIcon(qta.icon('fa5s.chevron-down', color='#00e6e6'))
        btn_header.setStyleSheet("""
            QPushButton {
                background-color: rgba(20, 20, 30, 255); color: white; border: 1px solid #555;
                border-radius: 5px; padding: 10px; text-align: left; font-size: 14px;
            }
            QPushButton:hover { background-color: rgba(0, 230, 230, 0.2); border: 1px solid #00e6e6; }
        """)
        btn_header.setCursor(Qt.PointingHandCursor)

        tabla_contenedor = QWidget()
        tabla_contenedor.setVisible(False)
        lay_tabla = QVBoxLayout(tabla_contenedor)
        lay_tabla.setContentsMargins(0, 0, 0, 10)

        tabla = QTableWidget()
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(["ID Gasto", "Descripción", "Monto", "Fecha", "Usuario"])
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setStyleSheet("background-color: rgba(15,15,20,150); gridline-color: #555; border: 1px solid #555;")
        
        altura = 35 + (len(gastos) * 35)
        tabla.setFixedHeight(altura if altura < 250 else 250)

        tabla.setRowCount(0)
        for idx, g in enumerate(gastos):
            tabla.insertRow(idx)
            f_obj_g = datetime.strptime(g[4], '%Y-%m-%d')
            mes_ab = meses_abrev[f_obj_g.month - 1] # Mes en español asegurado
            
            items = [
                QTableWidgetItem(str(g[1]).zfill(3)),
                QTableWidgetItem(g[2]),
                QTableWidgetItem(f"${g[3]:.2f}"),
                QTableWidgetItem(f"{f_obj_g.day} {mes_ab}"),
                QTableWidgetItem(g[5])
            ]
            for col, item in enumerate(items):
                tabla.setItem(idx, col, item)

        lay_tabla.addWidget(tabla)

        def toggle_acordeon():
            es_visible = tabla_contenedor.isVisible()
            tabla_contenedor.setVisible(not es_visible)
            if es_visible:
                btn_header.setIcon(qta.icon('fa5s.chevron-down', color='#00e6e6'))
            else:
                btn_header.setIcon(qta.icon('fa5s.chevron-up', color='#00e6e6'))

        btn_header.clicked.connect(toggle_acordeon)
        self.historial_layout.addWidget(btn_header)
        self.historial_layout.addWidget(tabla_contenedor)