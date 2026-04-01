from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QFrame)
from PySide6.QtCore import Qt
import qtawesome as qta
from database.connection import get_connection
from datetime import datetime

class MovimientosView(QWidget):
    # --- MODIFICACIÓN: Recibimos el usuario_id ---
    def __init__(self, usuario_id=1):
        super().__init__()
        self.usuario_id = usuario_id
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- TÍTULO ---
        title = QLabel("HISTORIAL DE MOVIMIENTOS DEL SISTEMA")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # --- BARRA DE BÚSQUEDA ---
        frame_busqueda = QFrame()
        frame_busqueda.setStyleSheet("background-color: transparent;")
        lay_busqueda = QHBoxLayout(frame_busqueda)
        lay_busqueda.setContentsMargins(0, 0, 0, 0)

        lbl_buscar = QLabel("BUSCAR MOVIMIENTO:")
        lbl_buscar.setStyleSheet("color: #ccc; font-weight: bold; font-size: 14px;")
        lay_busqueda.addWidget(lbl_buscar)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por acción, usuario o módulo...")
        self.txt_buscar.setStyleSheet("background-color: rgba(15, 15, 20, 200); border: 1px solid #555; padding: 10px; border-radius: 4px; color: white;")
        # Filtrar al presionar Enter
        self.txt_buscar.returnPressed.connect(self.cargar_datos)
        lay_busqueda.addWidget(self.txt_buscar, stretch=1)

        btn_filtrar = QPushButton("  FILTRAR")
        btn_filtrar.setIcon(qta.icon('fa5s.search', color='black'))
        btn_filtrar.setStyleSheet("""
            QPushButton {
                background-color: #00e6e6; color: black; border: none;
                border-radius: 4px; padding: 10px 20px; font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #00cccc; }
        """)
        btn_filtrar.setCursor(Qt.PointingHandCursor)
        btn_filtrar.clicked.connect(self.cargar_datos)
        lay_busqueda.addWidget(btn_filtrar)

        layout.addWidget(frame_busqueda)

        # --- TABLA DE MOVIMIENTOS ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["FECHA / HORA", "USUARIO", "MÓDULO", "ID REF", "DETALLES"])
        
        # Ajustes de las columnas para mejor lectura
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch) # Detalles ocupa el resto
        
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(15,15,20,180); color: white;
                gridline-color: #555; border: 1px solid #555; border-radius: 5px; font-size: 13px;
            }
            QHeaderView::section {
                background-color: rgba(20, 20, 30, 255); color: #2077D4;
                padding: 10px; border: 1px solid #555; font-weight: bold;
            }
        """)
        layout.addWidget(self.table)

        self.cargar_datos()

    def cargar_datos(self):
        filtro = self.txt_buscar.text().strip()
        
        try:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                SELECT m.fecha_hora, u.nombre, m.tipo_referencia, m.id_referencia, m.accion
                FROM movimientos_log m
                JOIN usuarios u ON m.usuario_id = u.id
                WHERE 1=1
            """
            params = []

            # --- MODIFICACIÓN: Si no es el administrador (ID 1), ocultamos los movimientos de Displays ---
            if self.usuario_id != 1:
                query += " AND m.tipo_referencia NOT IN ('DISPLAY', 'VENTA_DISPLAY')"

            # Aplicar filtro si el usuario escribió algo
            if filtro:
                query += " AND (m.accion LIKE ? OR u.nombre LIKE ? OR m.tipo_referencia LIKE ?)"
                p = f"%{filtro}%"
                params.extend([p, p, p])

            query += " ORDER BY m.fecha_hora DESC LIMIT 200" # Límite para rendimiento

            cursor.execute(query, tuple(params))
            movimientos = cursor.fetchall()
            conn.close()

            self.table.setRowCount(0)
            meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

            for idx, mov in enumerate(movimientos):
                self.table.insertRow(idx)
                
                # Formatear la fecha para que se vea como en tu wireframe
                try:
                    f_obj = datetime.strptime(mov[0], "%Y-%m-%d %H:%M:%S")
                    f_str = f"{f_obj.day} {meses[f_obj.month-1]}, {f_obj.year} - {f_obj.strftime('%H:%M')}"
                except:
                    f_str = mov[0]

                items = [
                    QTableWidgetItem(f_str),
                    QTableWidgetItem(mov[1]),
                    QTableWidgetItem(mov[2]),
                    QTableWidgetItem(str(mov[3] or "N/A")), # Evitar 'None' si no hay ID
                    QTableWidgetItem(mov[4])
                ]

                for col, item in enumerate(items):
                    self.table.setItem(idx, col, item)

        except Exception as e:
            print(f"Error cargando movimientos: {e}")