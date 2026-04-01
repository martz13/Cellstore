from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QFrame, QPushButton, QLabel, QStackedWidget,QMessageBox)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QSize
import qtawesome as qta

from database.connection import get_asset_path
from views.usuarios_view import UsuariosView
from views.nueva_cotizacion_view import NuevaCotizacionView
from PySide6.QtWidgets import QButtonGroup
from views.cotizaciones_view import CotizacionesView
from views.otros_gastos_view import OtrosGastosView
from views.graficas_view import GraficasView
from views.movimientos_view import MovimientosView
from views.displays_view import DisplaysView
from views.datos_empresa_view import DatosEmpresaView


class MainWindow(QMainWindow):
    def __init__(self,usuario_id=1, nombre_usuario="Usuario"):
        super().__init__()
        self.usuario_id = usuario_id
        self.nombre_usuario = nombre_usuario
        self.setWindowTitle("Cell Store - Sistema de Gestión")
        self.resize(1100, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- MENÚ LATERAL ---
        self.side_menu = QFrame()
        self.side_menu.setObjectName("SideMenu")
        self.side_menu.setFixedWidth(220)
        self.menu_layout = QVBoxLayout(self.side_menu)
        self.menu_layout.setContentsMargins(10, 20, 10, 20)
        
        self.btn_toggle = QPushButton()
        self.btn_toggle.setIcon(qta.icon('fa5s.bars', color='white'))
        self.btn_toggle.setIconSize(QSize(24, 24))
        self.btn_toggle.setStyleSheet("background: transparent; border: none;")
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_menu)
        
        self.logo_label = QLabel()
        logo_pixmap = QPixmap(get_asset_path("assets/images/iconosinBG.png"))
        self.logo_label.setPixmap(logo_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.logo_label.setAlignment(Qt.AlignCenter)

        self.lbl_usuario = QLabel(f"Hola, {self.nombre_usuario}")
        self.lbl_usuario.setStyleSheet("color: #2077D4; font-weight: bold; font-size: 14px;")
        self.lbl_usuario.setAlignment(Qt.AlignCenter)

        

        top_menu_layout = QHBoxLayout()
        top_menu_layout.addWidget(self.btn_toggle)
        top_menu_layout.addStretch()
        
        self.menu_layout.addLayout(top_menu_layout)
        self.menu_layout.addWidget(self.logo_label)
        self.menu_layout.addWidget(self.lbl_usuario) # <--- Agregamos el label aquí
        self.menu_layout.addSpacing(10)

        # --- NUEVO: GRUPO EXCLUSIVO PARA LOS BOTONES DEL MENÚ ---
        self.menu_btn_group = QButtonGroup(self)
        self.menu_btn_group.setExclusive(True) # Hace que solo uno pueda estar seleccionado
        self.btn_usuarios = self.crear_boton_menu("Usuarios", "fa5s.user")
        self.btn_usuarios.setChecked(True)
        self.btn_nueva_cotizacion = self.crear_boton_menu("Nueva Cotización", "fa5s.file-signature")
        self.btn_cotizaciones = self.crear_boton_menu("Cotizaciones", "fa5s.file-invoice-dollar")

        self.btn_gastos = self.crear_boton_menu("Otros Gastos", "fa5s.money-bill-wave")
        self.btn_graficas = self.crear_boton_menu("Gráficas", "fa5s.chart-bar")
        self.btn_displays = self.crear_boton_menu("Displays", "fa5s.desktop")
        if self.usuario_id != 1:
            self.btn_displays.hide()
        self.btn_movimientos = self.crear_boton_menu("Movimientos", "fa5s.exchange-alt")
        self.btn_datos = self.crear_boton_menu("Datos CellStore", "fa5s.database")

        # Conectar al índice 1 (que es el segundo widget que agregamos)
        self.btn_nueva_cotizacion.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        # (Asegúrate de que el de usuarios apunte al índice 0)
        self.btn_usuarios.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        self.btn_cotizaciones.clicked.connect(self.mostrar_cotizaciones)

        # Conecta el botón a la nueva función que crearemos abajo
        self.btn_gastos.clicked.connect(self.mostrar_gastos)

        # Conecta el botón a la nueva función
        self.btn_graficas.clicked.connect(self.mostrar_graficas)

        # Suponiendo que este sea el índice 5
        self.btn_movimientos.clicked.connect(self.mostrar_movimientos)

        self.btn_displays.clicked.connect(self.mostrar_displays)

        self.btn_datos.clicked.connect(self.mostrar_datos)

        self.menu_layout.addStretch()

        self.btn_logout = QPushButton("  Cerrar Sesión")
        self.btn_logout.setIcon(qta.icon('fa5s.sign-out-alt', color='#ff4d4d'))
        self.btn_logout.setIconSize(QSize(26, 26)) # Icono un poco más grande
        self.btn_logout.setProperty("class", "MenuButton")
        self.btn_logout.setStyleSheet("color: #ff4d4d;") # Texto rojo para destacar
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setToolTip("Cerrar Sesión")
        self.btn_logout.clicked.connect(self.cerrar_sesion)
        self.menu_layout.addWidget(self.btn_logout)

        # --- ÁREA DE PANTALLAS ---
        self.stacked_widget = QStackedWidget()
        
        # Instanciar y agregar vistas
        self.vista_usuarios = UsuariosView(usuario_id=self.usuario_id)
        self.stacked_widget.addWidget(self.vista_usuarios)
        
        self.vista_nueva_cotizacion = NuevaCotizacionView(usuario_id=self.usuario_id) 
        self.stacked_widget.addWidget(self.vista_nueva_cotizacion)

        self.vista_cotizaciones = CotizacionesView(usuario_id=self.usuario_id)
        self.stacked_widget.addWidget(self.vista_cotizaciones)
        self.vista_cotizaciones.senal_editar_cotizacion.connect(self.ir_a_editar_cotizacion)

        self.vista_gastos = OtrosGastosView(usuario_id=self.usuario_id, nombre_usuario=self.nombre_usuario)
        self.stacked_widget.addWidget(self.vista_gastos)

        self.vista_graficas = GraficasView()
        self.stacked_widget.addWidget(self.vista_graficas)

        self.vista_movimientos = MovimientosView(usuario_id=self.usuario_id)
        self.stacked_widget.addWidget(self.vista_movimientos)

        self.vista_displays = DisplaysView(usuario_id=self.usuario_id)
        self.stacked_widget.addWidget(self.vista_displays)
        
        

        self.vista_datos = DatosEmpresaView()
        self.stacked_widget.addWidget(self.vista_datos)
        
        main_layout.addWidget(self.side_menu)
        
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.addWidget(self.stacked_widget)
        main_layout.addWidget(content_container)

    # --- NUEVOS MÉTODOS PARA MAINWINDOW (agrégalos al final de la clase) ---
    def mostrar_cotizaciones(self):
        self.vista_cotizaciones.cargar_datos() # Fuerza a recargar la base de datos
        self.stacked_widget.setCurrentIndex(2)

    def ir_a_editar_cotizacion(self, cot_id):
        self.vista_nueva_cotizacion.cargar_cotizacion_existente(cot_id)
        self.stacked_widget.setCurrentIndex(1)
        self.btn_nueva_cotizacion.setChecked(True) # Remarca el menú de color azul

    # MODIFICACIÓN: Ajustamos tooltips y tamaño de icono
    def crear_boton_menu(self, texto, icono):
        btn = QPushButton(f"  {texto}")
        btn.setIcon(qta.icon(icono, color='white'))
        btn.setIconSize(QSize(26, 26)) # <--- Iconos más grandes (antes 20x20)
        btn.setProperty("class", "MenuButton")
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setToolTip(texto) # <--- Tooltip agregado
        self.menu_layout.addWidget(btn)
        self.menu_btn_group.addButton(btn)
        return btn 

    # MODIFICACIÓN: Ocultar/Mostrar el nombre de usuario al colapsar
    def toggle_menu(self):
        if self.side_menu.width() == 220:
            self.side_menu.setFixedWidth(60)
            self.logo_label.hide()
            self.lbl_usuario.hide() # <--- Ocultamos el nombre
            for btn in self.side_menu.findChildren(QPushButton):
                if btn.property("class") == "MenuButton":
                    btn.setText("")
        else:
            self.side_menu.setFixedWidth(220)
            self.logo_label.show()
            self.lbl_usuario.show()
            self.btn_usuarios.setText("  Usuarios")

            self.btn_nueva_cotizacion.setText("  Nueva Cotización")

            self.btn_cotizaciones.setText("  Cotizaciones")

            self.btn_gastos.setText("  Otros Gastos")

            self.btn_graficas.setText("  Gráficas")


            if self.usuario_id == 1:
                self.btn_displays.setText("  Displays")

            self.btn_movimientos.setText("  Movimientos")

            self.btn_datos.setText("  Datos CellStore") # <--- Mostramos el nombre
            # ... (Resto del código de restaurar textos igual) ...
            self.btn_logout.setText("  Cerrar Sesión") # Restaurar texto de logout

    # NUEVO MÉTODO
    def cerrar_sesion(self):
        respuesta = QMessageBox.question(self, "Cerrar Sesión", "¿Estás seguro que deseas cerrar sesión?", 
                                         QMessageBox.Yes | QMessageBox.No)
        if respuesta == QMessageBox.Yes:
            # Importación local para evitar importaciones circulares
            from views.login_view import LoginWindow 
            self.login = LoginWindow()
            self.login.show()
            self.close()

    def mostrar_gastos(self):
        self.vista_gastos.cargar_datos() # Fuerza a recargar la base de datos
        self.stacked_widget.setCurrentIndex(3) # Asumiendo que es el índice 3

    def mostrar_graficas(self):
        # Actualiza tanto las tablas de aclaraciones como las gráficas
        self.vista_graficas.cargar_datos_aclaraciones()
        self.vista_graficas.actualizar_graficas()
        # El índice debería ser el 4 si seguiste el orden 
        # (0: Usuarios, 1: Nueva Cot, 2: Cotizaciones, 3: Gastos, 4: Graficas)
        self.stacked_widget.setCurrentIndex(4)
    def mostrar_movimientos(self):
        self.vista_movimientos.cargar_datos() # Recarga el historial de la BD
        self.stacked_widget.setCurrentIndex(5)

    def mostrar_displays(self):
        self.vista_displays.cargar_datos()
        self.stacked_widget.setCurrentIndex(6) # Asegúrate que coincida con el orden de tus vistas

    def mostrar_datos(self):
        self.vista_datos.cargar_datos() # Recarga por si se editó la BD
        self.stacked_widget.setCurrentIndex(7) # Asegúrate de poner el índice correcto (el último)