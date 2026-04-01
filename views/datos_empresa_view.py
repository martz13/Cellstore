from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QTextEdit, QPushButton, QFrame, 
                               QSpacerItem, QSizePolicy, QMessageBox, QScrollArea, QFileDialog)
from PySide6.QtCore import Qt
import qtawesome as qta
from database.connection import get_connection, get_db_path
import shutil
import os
from datetime import datetime

class DatosEmpresaView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area para que todo sea desplazable si la ventana es pequeña
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #2a2a2a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #2077D4;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00e6e6;
            }
        """)
        
        # Contenedor principal dentro del scroll
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)

        # --- ENCABEZADO (TÍTULO Y BOTÓN DE DESCARGA BD) ---
        header_layout = QHBoxLayout()
        
        # Etiqueta invisible a la izquierda para mantener el título exactamente en el centro
        left_spacer = QLabel()
        left_spacer.setFixedWidth(200)
        header_layout.addWidget(left_spacer)
        
        header_layout.addStretch()
        
        title = QLabel("GESTIÓN DE DATOS DE LA EMPRESA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #00e6e6; 
            font-size: 26px; 
            font-weight: bold; 
            letter-spacing: 1px;
            padding: 20px 0px;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()

        self.btn_descargar_bd = QPushButton("  Descargar BD")
        self.btn_descargar_bd.setIcon(qta.icon('fa5s.database', color='white'))
        self.btn_descargar_bd.setFixedWidth(200)
        self.btn_descargar_bd.setStyleSheet("""
            QPushButton {
                background-color: #2077D4; color: white; font-weight: bold;
                padding: 10px 15px; border-radius: 5px; border: none; font-size: 14px;
            }
            QPushButton:hover { background-color: #1a5ea8; }
        """)
        self.btn_descargar_bd.setCursor(Qt.PointingHandCursor)
        self.btn_descargar_bd.clicked.connect(self.descargar_bd)
        header_layout.addWidget(self.btn_descargar_bd)

        container_layout.addLayout(header_layout)

        # --- CONTENEDOR CENTRAL (Formulario) ---
        # Frame que contendrá el formulario centrado
        center_wrapper = QWidget()
        center_wrapper.setStyleSheet("background-color: transparent;")
        center_layout = QHBoxLayout(center_wrapper)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # Frame del formulario con ancho máximo y centrado
        self.frame_form = QFrame()
        self.frame_form.setMaximumWidth(800)
        self.frame_form.setMinimumWidth(400)
        self.frame_form.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 15, 20, 100);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        lay_form = QVBoxLayout(self.frame_form)
        lay_form.setSpacing(20)
        lay_form.setContentsMargins(25, 25, 25, 25)

        # Estilos mejorados
        estilo_input = """
            QLineEdit, QTextEdit {
                background-color: rgba(25, 25, 35, 220);
                border: 2px solid #2077D4;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-size: 14px;
                font-family: 'Segoe UI', Arial;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #00e6e6;
                background-color: rgba(35, 35, 45, 220);
            }
            QTextEdit {
                padding: 8px;
            }
        """
        
        estilo_label = "color: #ccc; font-weight: bold; font-size: 14px; background-color: transparent;"

        # --- 1. NOMBRE LOCAL ---
        lay_nombre = QVBoxLayout()
        lbl_nombre = self.crear_label_con_icono("NOMBRE LOCAL", "fa5s.store")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setStyleSheet(estilo_input)
        self.txt_nombre.setMinimumHeight(45)
        lay_nombre.addWidget(lbl_nombre)
        lay_nombre.addWidget(self.txt_nombre)
        lay_form.addLayout(lay_nombre)

        # --- 2. DIRECCIÓN ---
        lay_direccion = QVBoxLayout()
        lbl_direccion = self.crear_label_con_icono("DIRECCIÓN DE LA EMPRESA", "fa5s.map-marker-alt")
        self.txt_direccion = QTextEdit()
        self.txt_direccion.setStyleSheet(estilo_input)
        self.txt_direccion.setFixedHeight(100)
        self.txt_direccion.setMinimumHeight(80)
        lay_direccion.addWidget(lbl_direccion)
        lay_direccion.addWidget(self.txt_direccion)
        lay_form.addLayout(lay_direccion)

        # --- 3. TELÉFONO ---
        lay_telefono = QVBoxLayout()
        lbl_telefono = self.crear_label_con_icono("TELÉFONO DE CONTACTO", "fa5s.phone-alt")
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setStyleSheet(estilo_input)
        self.txt_telefono.setMinimumHeight(45)
        lay_telefono.addWidget(lbl_telefono)
        lay_telefono.addWidget(self.txt_telefono)
        lay_form.addLayout(lay_telefono)

        # --- 4. SLOGAN ---
        lay_slogan = QVBoxLayout()
        lbl_slogan = self.crear_label_con_icono("SLOGAN", "fa5s.quote-left")
        self.txt_slogan = QLineEdit()
        self.txt_slogan.setStyleSheet(estilo_input)
        self.txt_slogan.setMinimumHeight(45)
        lay_slogan.addWidget(lbl_slogan)
        lay_slogan.addWidget(self.txt_slogan)
        lay_form.addLayout(lay_slogan)

        # Espacio antes del botón
        lay_form.addSpacing(15)

        # --- BOTÓN GUARDAR ---
        self.btn_guardar = QPushButton("  GUARDAR CAMBIOS DE LA EMPRESA")
        self.btn_guardar.setIcon(qta.icon('fa5s.save', color='black'))
        self.btn_guardar.setMinimumHeight(55)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #00e6e6;
                color: black;
                font-weight: bold;
                font-size: 16px;
                padding: 15px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #00cccc;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background-color: #009999;
            }
        """)
        self.btn_guardar.setCursor(Qt.PointingHandCursor)
        self.btn_guardar.clicked.connect(self.guardar_cambios)
        lay_form.addWidget(self.btn_guardar)

        # Espacio inferior
        lay_form.addSpacing(10)

        # Centrar el frame_form horizontalmente
        center_layout.addStretch()
        center_layout.addWidget(self.frame_form)
        center_layout.addStretch()
        
        container_layout.addWidget(center_wrapper)
        container_layout.addStretch()
        
        # Asignar el contenedor al scroll
        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        # Cargar datos
        self.cargar_datos()

    def crear_label_con_icono(self, texto, icono_str):
        """Crea un label con ícono a la izquierda"""
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        lay = QHBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        
        lbl_icono = QLabel()
        icon = qta.icon(icono_str, color='#2077D4')
        lbl_icono.setPixmap(icon.pixmap(22, 22))
        
        lbl_texto = QLabel(texto)
        lbl_texto.setStyleSheet("""
            color: #ccc;
            font-weight: bold;
            font-size: 14px;
            background-color: transparent;
        """)
        
        lay.addWidget(lbl_icono)
        lay.addWidget(lbl_texto)
        lay.addStretch()
        return widget

    def cargar_datos(self):
        """Carga los datos actuales de la empresa desde la BD"""
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, direccion, telefono, slogan FROM datos_empresa WHERE id=1")
            datos = cursor.fetchone()
            conn.close()

            if datos:
                self.txt_nombre.setText(datos[0] if datos[0] else "")
                self.txt_direccion.setText(datos[1] if datos[1] else "")
                self.txt_telefono.setText(datos[2] if datos[2] else "")
                self.txt_slogan.setText(datos[3] if len(datos) > 3 and datos[3] else "")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos:\n{e}")

    def guardar_cambios(self):
        """Guarda los cambios en la base de datos"""
        nombre = self.txt_nombre.text().strip()
        direccion = self.txt_direccion.toPlainText().strip()
        telefono = self.txt_telefono.text().strip()
        slogan = self.txt_slogan.text().strip()

        if not nombre or not direccion:
            QMessageBox.warning(self, "Campos Vacíos", 
                              "El nombre y la dirección son obligatorios.\nPor favor completa estos campos.")
            return

        respuesta = QMessageBox.question(self, "Confirmar Cambios", 
                                       "¿Estás seguro de actualizar los datos de la empresa?\n\n"
                                       "Esta acción actualizará la información que aparecerá en tickets y PDFs.", 
                                       QMessageBox.Yes | QMessageBox.No)
        
        if respuesta == QMessageBox.Yes:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE datos_empresa 
                    SET nombre=?, direccion=?, telefono=?, slogan=? 
                    WHERE id=1
                """, (nombre, direccion, telefono, slogan))
                conn.commit()
                conn.close()

                QMessageBox.information(self, "Éxito", 
                                      "✅ Datos de la empresa actualizados correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error BD", f"Error al guardar los datos:\n{e}")

    def descargar_bd(self):
        """Permite al usuario respaldar la base de datos seleccionando dónde guardarla."""
        ruta_origen = get_db_path()
        
        if not os.path.exists(ruta_origen):
            QMessageBox.warning(self, "Error", "No se encontró el archivo de la base de datos en el sistema.")
            return

        # Generar un nombre sugerido con la fecha y hora actual
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_sugerido = f"respaldo_cellstore_{fecha_str}.db"

        # Abrir diálogo para que el usuario elija dónde guardar
        ruta_destino, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Respaldo de Base de Datos", 
            nombre_sugerido, 
            "Base de Datos SQLite (*.db)"
        )

        if ruta_destino: # Si el usuario no canceló la ventana
            try:
                # Copiar el archivo
                shutil.copy2(ruta_origen, ruta_destino)
                QMessageBox.information(self, "Éxito", f"✅ Base de datos respaldada correctamente en:\n\n{ruta_destino}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Ocurrió un error al copiar la base de datos:\n{e}")