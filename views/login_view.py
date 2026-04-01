import random
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QPushButton, QFrame, QSpacerItem, 
                               QSizePolicy, QMessageBox, QDialog)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import qtawesome as qta

from database.connection import get_asset_path, get_connection
from views.main_window import MainWindow

# Importamos nuestro nuevo enviador de correos
from utils.email_sender import EmailSender


# ================= MODAL PARA INGRESAR CÓDIGO DE 4 DÍGITOS =================
class CodigoVerificacionDialog(QDialog):
    def __init__(self, codigo_real, parent=None):
        super().__init__(parent)
        self.codigo_real = str(codigo_real)
        self.exito = False
        
        self.setWindowTitle("Verificar Código")
        self.setFixedSize(320, 200)
        self.setStyleSheet("background-color: #1a1a1a; color: white;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        lbl_instrucciones = QLabel("Ingresa el código de 4 dígitos\nenviado a tu correo electrónico:")
        lbl_instrucciones.setAlignment(Qt.AlignCenter)
        lbl_instrucciones.setStyleSheet("font-size: 14px; font-weight: bold; color: #ccc;")
        layout.addWidget(lbl_instrucciones)
        
        lay_inputs = QHBoxLayout()
        lay_inputs.setSpacing(15)
        lay_inputs.setAlignment(Qt.AlignCenter)
        
        self.inputs = []
        estilo_input = """
            QLineEdit {
                background-color: #2b2b2b; border: 2px solid #555; 
                border-radius: 5px; font-size: 24px; font-weight: bold; color: #00e6e6;
            }
            QLineEdit:focus { border: 2px solid #00e6e6; }
        """
        
        # Crear los 4 campos de texto
        for i in range(4):
            inp = QLineEdit()
            inp.setMaxLength(1)
            inp.setFixedSize(50, 50)
            inp.setAlignment(Qt.AlignCenter)
            inp.setStyleSheet(estilo_input)
            lay_inputs.addWidget(inp)
            self.inputs.append(inp)
            
        # Conectar el evento de escritura para hacer el "Auto-Focus"
        self.inputs[0].textChanged.connect(lambda t: self.mover_foco(t, 0))
        self.inputs[1].textChanged.connect(lambda t: self.mover_foco(t, 1))
        self.inputs[2].textChanged.connect(lambda t: self.mover_foco(t, 2))
        self.inputs[3].textChanged.connect(lambda t: self.mover_foco(t, 3))
        
        layout.addLayout(lay_inputs)
        
        self.btn_verificar = QPushButton("VERIFICAR CÓDIGO")
        self.btn_verificar.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.btn_verificar.setCursor(Qt.PointingHandCursor)
        self.btn_verificar.clicked.connect(self.verificar_codigo)
        layout.addWidget(self.btn_verificar)
        
    def mover_foco(self, texto, index):
        # Si se escribió un número, pasar al siguiente input
        if len(texto) == 1 and index < 3:
            self.inputs[index+1].setFocus()
        # Si se borró (backspace), regresar al input anterior
        elif len(texto) == 0 and index > 0:
            self.inputs[index-1].setFocus()
        # Si estamos en el último y escribimos, enfocar el botón
        elif len(texto) == 1 and index == 3:
            self.btn_verificar.setFocus()
            
    def verificar_codigo(self):
        codigo_ingresado = "".join([inp.text() for inp in self.inputs])
        if codigo_ingresado == self.codigo_real:
            self.exito = True
            self.accept() # Cierra el modal con éxito
        else:
            QMessageBox.warning(self, "Error", "El código ingresado es incorrecto. Inténtalo de nuevo.")
            for inp in self.inputs:
                inp.clear()
            self.inputs[0].setFocus()


# ================= VISTA PRINCIPAL DEL LOGIN =================
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cell Store - Acceso")
        self.resize(1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.logo_label = QLabel()
        pixmap = QPixmap(get_asset_path("assets/images/iconosinBG.png")) 
        self.logo_label.setPixmap(pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.logo_label)

        self.login_box = QFrame()
        self.login_box.setObjectName("LoginBox")
        self.login_box.setFixedSize(400, 370) 
        
        login_layout = QVBoxLayout(self.login_box)
        login_layout.setContentsMargins(40, 30, 40, 30)

        lbl_title = QLabel("INICIAR SESIÓN")
        lbl_title.setObjectName("Title")
        lbl_title.setAlignment(Qt.AlignCenter)
        login_layout.addWidget(lbl_title)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("ejemplo@email.com")
        login_layout.addWidget(QLabel("Correo Electrónico"))
        login_layout.addWidget(self.txt_email)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("••••••••")
        self.txt_password.setEchoMode(QLineEdit.Password)
        
        self.accion_ojo = self.txt_password.addAction(qta.icon('fa5s.eye', color='#aaaaaa'), QLineEdit.TrailingPosition)
        self.accion_ojo.triggered.connect(self.toggle_password)
        
        login_layout.addWidget(QLabel("Contraseña"))
        login_layout.addWidget(self.txt_password)

        # --- BOTÓN OLVIDÓ CONTRASEÑA ---
        self.btn_olvido = QPushButton("¿Olvidó su contraseña?")
        self.btn_olvido.setStyleSheet("background: transparent; color: #2077D4; text-decoration: underline;")
        self.btn_olvido.setCursor(Qt.PointingHandCursor)
        self.btn_olvido.clicked.connect(self.recuperar_contrasena)
        
        lay_olvido = QHBoxLayout()
        lay_olvido.addStretch()
        lay_olvido.addWidget(self.btn_olvido)
        login_layout.addLayout(lay_olvido)

        self.btn_login = QPushButton("INICIAR SESIÓN")
        self.btn_login.setObjectName("BtnPrimary")
        self.btn_login.clicked.connect(self.verificar_login)
        login_layout.addSpacing(10)
        login_layout.addWidget(self.btn_login)

        box_layout = QHBoxLayout()
        box_layout.addStretch()
        box_layout.addWidget(self.login_box)
        box_layout.addStretch()
        main_layout.addLayout(box_layout)
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def toggle_password(self):
        if self.txt_password.echoMode() == QLineEdit.Password:
            self.txt_password.setEchoMode(QLineEdit.Normal)
            self.accion_ojo.setIcon(qta.icon('fa5s.eye-slash', color='#2077D4'))
        else:
            self.txt_password.setEchoMode(QLineEdit.Password)
            self.accion_ojo.setIcon(qta.icon('fa5s.eye', color='#aaaaaa'))

    def verificar_login(self):
        correo = self.txt_email.text().strip()
        contrasena = self.txt_password.text()

        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM usuarios WHERE correo = ? AND contrasena = ? AND activo = 1", (correo, contrasena))
            usuario = cursor.fetchone()
            conn.close()

            if usuario:
                usuario_id, nombre_usuario = usuario
                self.main_window = MainWindow(usuario_id, nombre_usuario)
                self.main_window.show()
                self.close()
            else:
                QMessageBox.critical(self, "Error", "Credenciales incorrectas.")

        except Exception as e:
            QMessageBox.critical(self, "Error BD", f"Error de conexión:\n{e}")

    def recuperar_contrasena(self):
        correo = self.txt_email.text().strip()
        
        if not correo:
            QMessageBox.warning(self, "Correo requerido", "Para recuperar tu cuenta, primero ingresa tu correo electrónico en el campo superior.")
            self.txt_email.setFocus()
            return
            
        try:
            # Verificar si el correo existe en la base de datos
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM usuarios WHERE correo = ? AND activo = 1", (correo,))
            usuario = cursor.fetchone()
            conn.close()
            
            if not usuario:
                QMessageBox.critical(self, "Error", "El correo ingresado no está registrado en el sistema.")
                return
                
            # Generar código de 4 dígitos
            codigo_generado = f"{random.randint(1000, 9999)}"
            
            # Informar al usuario para que espere
            QMessageBox.information(self, "Enviando", "Se está enviando el código a tu correo. Haz clic en OK y espera un momento...")
            
            # Enviar el correo usando nuestra nueva clase
            exito, msj = EmailSender.enviar_codigo(correo, codigo_generado)
            
            if exito:
                # Mostrar el modal de los 4 dígitos
                dialog = CodigoVerificacionDialog(codigo_generado, self)
                if dialog.exec() and dialog.exito:
                    # El código fue correcto
                    QMessageBox.information(self, "¡Login Exitoso!", "¡Login exitoso!!\n\nPor favor, no olvide cambiar su contraseña desde el panel de Usuarios.")
                    
                    # Iniciar sesión automáticamente
                    usuario_id, nombre_usuario = usuario
                    self.main_window = MainWindow(usuario_id, nombre_usuario)
                    self.main_window.show()
                    self.close()
            else:
                QMessageBox.critical(self, "Error de Envío", f"No se pudo enviar el correo de recuperación:\n{msj}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error BD", f"Ocurrió un error al procesar la solicitud:\n{e}")