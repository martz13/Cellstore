from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                               QDialog, QFormLayout, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
import qtawesome as qta
import sqlite3
import random
from database.connection import get_connection
from utils.email_sender import EmailSender

# ================= 1. DIÁLOGO (MODAL) PARA CREAR/EDITAR USUARIO =================
class UsuarioDialog(QDialog):
    def __init__(self, parent=None, usuario_data=None):
        super().__init__(parent)
        self.usuario_id = usuario_data[0] if usuario_data else None
        
        titulo = "Editar Usuario" if self.usuario_id else "Nuevo Usuario"
        self.setWindowTitle(titulo)
        self.setFixedSize(350, 250)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.txt_nombre = QLineEdit()
        self.txt_correo = QLineEdit()
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)

        # Estilos rápidos para los inputs del modal
        estilo_input = "background-color: #2b2b2b; border: 1px solid #2077D4; padding: 5px; border-radius: 3px;"
        self.txt_nombre.setStyleSheet(estilo_input)
        self.txt_correo.setStyleSheet(estilo_input)
        self.txt_pass.setStyleSheet(estilo_input)

        if usuario_data:
            self.txt_nombre.setText(usuario_data[1])
            self.txt_correo.setText(usuario_data[2])
            self.txt_pass.setPlaceholderText("Dejar en blanco para no cambiar")

        layout.addRow("Nombre:", self.txt_nombre)
        layout.addRow("Correo:", self.txt_correo)
        layout.addRow("Contraseña:", self.txt_pass)

        # Botones
        botones_layout = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_guardar.setStyleSheet("background-color: #2077D4; padding: 8px; border-radius: 4px; font-weight: bold;")
        btn_guardar.clicked.connect(self.accept) # Cierra con QDialog.Accepted
        
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background-color: #555; padding: 8px; border-radius: 4px;")
        btn_cancelar.clicked.connect(self.reject) # Cierra con QDialog.Rejected

        botones_layout.addWidget(btn_cancelar)
        botones_layout.addWidget(btn_guardar)
        
        layout.addRow(botones_layout)

    def get_data(self):
        return {
            "nombre": self.txt_nombre.text().strip(),
            "correo": self.txt_correo.text().strip(),
            "contrasena": self.txt_pass.text()
        }

# ================= 2. VISTA PRINCIPAL DE USUARIOS =================
class UsuariosView(QWidget):
    def __init__(self, usuario_id=1):
        super().__init__()
        self.usuario_id = usuario_id # Guardamos el ID del usuario logueado
        
        layout = QVBoxLayout(self)
        
        header_layout = QHBoxLayout()
        title = QLabel("Gestión de Usuarios")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        
        btn_add = QPushButton(" Añadir Nuevo Usuario")
        btn_add.setObjectName("BtnPrimary")
        btn_add.setIcon(qta.icon('fa5s.plus', color='white'))
        btn_add.clicked.connect(lambda: self.abrir_modal())
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_add)
        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Correo", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        self.table.setRowCount(0)
        try:
            conn = get_connection()
            cursor = conn.cursor()
            # Filtro: Solo traer los que tengan activo = 1
            cursor.execute("SELECT id, nombre, correo FROM usuarios WHERE activo = 1")
            usuarios = cursor.fetchall()
            conn.close()

            for row_idx, usuario in enumerate(usuarios):
                self.table.insertRow(row_idx)
                for col_idx, data in enumerate(usuario):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
                
                acciones_widget = QWidget()
                acciones_layout = QHBoxLayout(acciones_widget)
                acciones_layout.setContentsMargins(0, 0, 0, 0)
                
                # REGLA: Mostrar botón Editar SOLO si es el perfil del usuario logueado
                if usuario[0] == self.usuario_id:
                    btn_edit = QPushButton()
                    btn_edit.setIcon(qta.icon('fa5s.edit', color='#2077D4'))
                    btn_edit.setCursor(Qt.PointingHandCursor)
                    btn_edit.setStyleSheet("background: transparent; border: none;")
                    btn_edit.clicked.connect(lambda *args, u=usuario: self.abrir_modal(u))
                    acciones_layout.addWidget(btn_edit)
                else:
                    # Rellenar el espacio vacío para que el botón de basura no se mueva
                    acciones_layout.addStretch()

                # Botón Eliminar para TODOS
                btn_delete = QPushButton()
                btn_delete.setIcon(qta.icon('fa5s.trash-alt', color='red'))
                btn_delete.setCursor(Qt.PointingHandCursor)
                btn_delete.setStyleSheet("background: transparent; border: none;")
                btn_delete.clicked.connect(lambda *args, uid=usuario[0]: self.eliminar_usuario(uid))
                
                acciones_layout.addWidget(btn_delete)
                self.table.setCellWidget(row_idx, 3, acciones_widget)

        except Exception as e:
            print("Error cargando usuarios:", e)

    def eliminar_usuario(self, usuario_id_eliminar):
        # Prevención: No dejaremos que el usuario se elimine a sí mismo mientras está logueado
        if usuario_id_eliminar == self.usuario_id:
            QMessageBox.warning(self, "Acción denegada", "No puedes eliminar tu propio usuario mientras tienes la sesión activa.")
            return

        respuesta = QMessageBox.question(self, "Confirmar Eliminación", 
                                         "¿Solicitar permiso para eliminar este usuario?\n\nSe enviará un código de seguridad al administrador del sistema.", 
                                         QMessageBox.Yes | QMessageBox.No)
        
        if respuesta == QMessageBox.Yes:
            try:
                # 1. Generar código y enviar correo
                codigo_generado = f"{random.randint(1000, 9999)}"
                correo_admin = "martzm4118@gmail.com"
                
                QMessageBox.information(self, "Enviando...", "Se está enviando el código de seguridad a martzm4118@gmail.com. Por favor, espera...")
                
                exito, msj = EmailSender.enviar_codigo(correo_admin, codigo_generado)
                
                if exito:
                    # Importación local para evitar errores de referencia circular
                    from views.login_view import CodigoVerificacionDialog
                    
                    dialog = CodigoVerificacionDialog(codigo_generado, self)
                    if dialog.exec() and dialog.exito:
                        # 2. BORRADO LÓGICO
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE usuarios SET activo = 0 WHERE id=?", (usuario_id_eliminar,))
                        
                        # 3. Registrar en historial de movimientos
                        cursor.execute("""
                            INSERT INTO movimientos_log (usuario_id, accion, id_referencia, tipo_referencia)
                            VALUES (?, ?, ?, 'USUARIOS')
                        """, (self.usuario_id, f"Eliminación lógica de usuario ID {usuario_id_eliminar}", usuario_id_eliminar))
                        
                        conn.commit()
                        conn.close()
                        
                        self.cargar_usuarios()
                        QMessageBox.information(self, "Eliminación exitosa", "El usuario ha sido eliminado correctamente del sistema.")
                else:
                    QMessageBox.critical(self, "Error de Envío", f"No se pudo enviar el correo de seguridad:\n{msj}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error BD", str(e))

    def abrir_modal(self, usuario_data=None):
        dialog = UsuarioDialog(self, usuario_data)
        if dialog.exec(): # Si el usuario presionó "Guardar"
            datos = dialog.get_data()
            self.guardar_usuario(dialog.usuario_id, datos)

    def guardar_usuario(self, usuario_id, datos):
        if not datos["nombre"] or not datos["correo"]:
            QMessageBox.warning(self, "Error", "Nombre y correo son obligatorios.")
            return

        try:
            conn = get_connection()
            cursor = conn.cursor()

            if usuario_id: # Es una edición
                if datos["contrasena"]: # Si escribió una nueva contraseña
                    cursor.execute("UPDATE usuarios SET nombre=?, correo=?, contrasena=? WHERE id=?", 
                                   (datos["nombre"], datos["correo"], datos["contrasena"], usuario_id))
                else: # Si dejó la contraseña en blanco, no la actualizamos
                    cursor.execute("UPDATE usuarios SET nombre=?, correo=? WHERE id=?", 
                                   (datos["nombre"], datos["correo"], usuario_id))
            else: # Es un registro nuevo
                if not datos["contrasena"]:
                    QMessageBox.warning(self, "Error", "La contraseña es obligatoria para nuevos usuarios.")
                    return
                cursor.execute("INSERT INTO usuarios (nombre, correo, contrasena, activo) VALUES (?, ?, ?, 1)", 
                               (datos["nombre"], datos["correo"], datos["contrasena"]))
            
            conn.commit()
            conn.close()
            self.cargar_usuarios() # Refrescar tabla
            QMessageBox.information(self, "Éxito", "Usuario guardado correctamente.")
            
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "El correo ya está registrado.")
        except Exception as e:
            QMessageBox.critical(self, "Error BD", str(e))