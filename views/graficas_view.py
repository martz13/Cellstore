from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QScrollArea, QFrame, QComboBox, 
                               QRadioButton, QButtonGroup, QGridLayout, QMessageBox,QToolTip)
from PySide6.QtCore import Qt, QDate,QPoint,QRect
# Cámbialo para que quede así:
from PySide6.QtGui import QColor, QFont, QPainter,QCursor
from PySide6.QtCharts import (QChart, QChartView, QBarSet, QBarSeries, 
                              QBarCategoryAxis, QValueAxis, QPieSeries)
import qtawesome as qta
from database.connection import get_connection
from datetime import datetime
import calendar

class GraficasView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: transparent;")
        self.layout_container = QVBoxLayout(self.container)
        self.layout_container.setContentsMargins(20, 20, 20, 20)
        self.layout_container.setSpacing(20)

        # TÍTULO
        title = QLabel("GESTIÓN DE GRÁFICAS Y ACLARACIONES")
        title.setStyleSheet("color: #2077D4; font-size: 24px; font-weight: bold;")
        self.layout_container.addWidget(title)

        # ================= SECCIÓN 1: ACLARACIONES =================
        self.setup_aclaraciones_ui()

        # ================= SECCIÓN 2: GRÁFICAS =================
        self.setup_graficas_ui()

        self.layout_container.addStretch()
        self.scroll_area.setWidget(self.container)
        main_layout.addWidget(self.scroll_area)

        # Cargar datos iniciales (Mes actual)
        self.cargar_datos_aclaraciones()
        self.actualizar_graficas()

    # ================= CONSTRUCCIÓN DE INTERFAZ =================

    def setup_aclaraciones_ui(self):
        frame_aclaraciones = QFrame()
        frame_aclaraciones.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: rgba(15,15,20,180);")
        lay_aclaraciones = QVBoxLayout(frame_aclaraciones)
        
        lbl_titulo_aclaraciones = QLabel("ACLARACIONES")
        lbl_titulo_aclaraciones.setStyleSheet("color: white; font-size: 16px; border: none; font-weight: bold;")
        lay_aclaraciones.addWidget(lbl_titulo_aclaraciones)

        # Filtros Aclaraciones
        lay_filtros_aclar = QHBoxLayout()
        lay_filtros_aclar.addWidget(QLabel("Mes:", styleSheet="color: #ccc; border: none;"))
        
        self.cb_mes_aclar = QComboBox()
        self.cb_mes_aclar.addItems(["Hoy", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.cb_mes_aclar.setStyleSheet("background-color: #222; color: white; border: 1px solid #555; padding: 5px;")
        # Seleccionar mes actual por defecto
        mes_actual = QDate.currentDate().month()
        self.cb_mes_aclar.setCurrentIndex(mes_actual)
        
        self.cb_anio_aclar = QComboBox()
        anio_actual = QDate.currentDate().year()
        self.cb_anio_aclar.addItems([str(anio_actual), str(anio_actual - 1)])
        self.cb_anio_aclar.setStyleSheet("background-color: #222; color: white; border: 1px solid #555; padding: 5px;")

        btn_filtrar_aclar = QPushButton("FILTRAR")
        btn_filtrar_aclar.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 5px 15px; border-radius: 3px;")
        btn_filtrar_aclar.setCursor(Qt.PointingHandCursor)
        btn_filtrar_aclar.clicked.connect(self.cargar_datos_aclaraciones)

        lay_filtros_aclar.addWidget(self.cb_mes_aclar)
        lay_filtros_aclar.addWidget(self.cb_anio_aclar)
        lay_filtros_aclar.addStretch()
        lay_filtros_aclar.addWidget(btn_filtrar_aclar)
        lay_aclaraciones.addLayout(lay_filtros_aclar)

        # Tablas
        lay_tablas = QHBoxLayout()
        
        # Tabla Cotizaciones
        lay_cot = QVBoxLayout()
        lay_cot.addWidget(QLabel("RESUMEN DE COTIZACIONES (MES SELECCIONADO)", styleSheet="color: #ccc; border:none;"))
        self.table_cot_aclar = QTableWidget()
        self.table_cot_aclar.setColumnCount(6)
        self.table_cot_aclar.setHorizontalHeaderLabels(["ID", "Fecha", "Cliente", "Inversión", "P. Final", "Ganancia"])
        self.table_cot_aclar.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_cot_aclar.verticalHeader().setVisible(False)
        self.table_cot_aclar.setStyleSheet("background-color: #1a1a1a; gridline-color: #444; border: 1px solid #444; color: white;")
        self.table_cot_aclar.setFixedHeight(150)
        lay_cot.addWidget(self.table_cot_aclar)
        lay_tablas.addLayout(lay_cot, stretch=6)

        # Tabla Gastos
        lay_gas = QVBoxLayout()
        lay_gas.addWidget(QLabel("RESUMEN DE OTROS GASTOS", styleSheet="color: #ccc; border:none;"))
        self.table_gas_aclar = QTableWidget()
        self.table_gas_aclar.setColumnCount(3)
        self.table_gas_aclar.setHorizontalHeaderLabels(["ID", "Descripción", "Monto"])
        self.table_gas_aclar.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_gas_aclar.verticalHeader().setVisible(False)
        self.table_gas_aclar.setStyleSheet("background-color: #1a1a1a; gridline-color: #444; border: 1px solid #444; color: white;")
        self.table_gas_aclar.setFixedHeight(150)
        lay_gas.addWidget(self.table_gas_aclar)
        lay_tablas.addLayout(lay_gas, stretch=4)

        lay_aclaraciones.addLayout(lay_tablas)

        # Cálculo de Ganancias Reales
        lay_calc = QGridLayout()
        lay_calc.addWidget(QLabel("CÁLCULO DE GANANCIAS REALES", styleSheet="color: white; border:none; font-weight:bold;"), 0, 0, 1, 2)
        
        estilo_lbl = "color: #ccc; border: none; font-size: 14px;"
        lay_calc.addWidget(QLabel("Total Ganancias Brutas (Cotizaciones Aceptadas):", styleSheet=estilo_lbl), 1, 0)
        self.lbl_brutas = QLabel("$0.00")
        self.lbl_brutas.setStyleSheet("color: white; border: none; font-size: 14px; font-weight: bold;")
        self.lbl_brutas.setAlignment(Qt.AlignRight)
        lay_calc.addWidget(self.lbl_brutas, 1, 1)

        lay_calc.addWidget(QLabel("Total Gastos Operativos (Otros Gastos):", styleSheet=estilo_lbl), 2, 0)
        self.lbl_gastos = QLabel("$0.00")
        self.lbl_gastos.setStyleSheet("color: #ff4d4d; border: none; font-size: 14px; font-weight: bold;")
        self.lbl_gastos.setAlignment(Qt.AlignRight)
        lay_calc.addWidget(self.lbl_gastos, 2, 1)

        lbl_reales_txt = QLabel("GANANCIAS REALES (Final):")
        lbl_reales_txt.setStyleSheet("color: black; background-color: #00e6e6; padding: 5px; font-weight: bold; font-size: 16px; border-radius: 3px;")
        lay_calc.addWidget(lbl_reales_txt, 3, 0)
        
        self.lbl_reales = QLabel("$0.00")
        self.lbl_reales.setStyleSheet("color: black; background-color: #00e6e6; padding: 5px; font-weight: bold; font-size: 16px; border-radius: 3px;")
        self.lbl_reales.setAlignment(Qt.AlignRight)
        lay_calc.addWidget(self.lbl_reales, 3, 1)

        lay_aclaraciones.addLayout(lay_calc)
        self.layout_container.addWidget(frame_aclaraciones)

    def setup_graficas_ui(self):
        frame_graficas = QFrame()
        frame_graficas.setStyleSheet("border: 1px solid #555; border-radius: 5px; background-color: rgba(15,15,20,180);")
        lay_graficas = QVBoxLayout(frame_graficas)

        lbl_titulo_graficas = QLabel("GRÁFICAS DE DESEMPEÑO")
        lbl_titulo_graficas.setStyleSheet("color: white; font-size: 16px; border: none; font-weight: bold;")
        lay_graficas.addWidget(lbl_titulo_graficas)

        # Filtros Gráficas
        lay_filtros_graf = QHBoxLayout()
        lay_filtros_graf.addWidget(QLabel("Mes:", styleSheet="color: #ccc; border:none;"))
        self.cb_mes_graf = QComboBox()
        self.cb_mes_graf.addItems(["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
        self.cb_mes_graf.setStyleSheet("background-color: #222; color: white; border: 1px solid #555; padding: 5px;")
        self.cb_mes_graf.setCurrentIndex(QDate.currentDate().month() - 1)
        
        # Añadir selector de año para gráficas
        # Añadir selector de año para gráficas
        self.cb_anio_graf = QComboBox()
        anio_actual = QDate.currentDate().year()
        self.cb_anio_graf.addItems([str(anio_actual), str(anio_actual - 1)])
        self.cb_anio_graf.setStyleSheet("background-color: #222; color: white; border: 1px solid #555; padding: 5px;")
        lay_filtros_graf.addWidget(QLabel("Año:", styleSheet="color: #ccc; border:none;"))
        
        
        btn_filtrar_graf = QPushButton("FILTRAR GRÁFICOS")
        btn_filtrar_graf.setStyleSheet("background-color: #00e6e6; color: black; font-weight: bold; padding: 5px 15px; border-radius: 3px;")
        btn_filtrar_graf.setCursor(Qt.PointingHandCursor)
        btn_filtrar_graf.clicked.connect(self.actualizar_graficas)

        lay_filtros_graf.addWidget(self.cb_mes_graf)
        lay_filtros_graf.addWidget(self.cb_anio_graf)
        lay_filtros_graf.addStretch()
        lay_filtros_graf.addWidget(btn_filtrar_graf)
        lay_graficas.addLayout(lay_filtros_graf)
        

        # Contenedor de las Gráficas
        lay_charts = QHBoxLayout()

# Gráfica 1: Barras (Ganancias vs Reparaciones)
        self.chart_bar_view = QChartView()
        self.chart_bar_view.setRenderHint(QPainter.Antialiasing) # <--- CAMBIO AQUÍ
        #self.chart_bar_view.setStyleSheet("background: transparent; border: none;")
        self.chart_bar_view.setMinimumHeight(300)
        lay_charts.addWidget(self.chart_bar_view, stretch=6)

        # Gráfica 2: Pastel (Gastos)
        self.chart_pie_view = QChartView()
        self.chart_pie_view.setRenderHint(QPainter.Antialiasing) # <--- CAMBIO AQUÍ
        #self.chart_pie_view.setStyleSheet("background: transparent; border: none;")
        self.chart_pie_view.setMinimumHeight(300)
        lay_charts.addWidget(self.chart_pie_view, stretch=4)

        lay_graficas.addLayout(lay_charts)
        self.layout_container.addWidget(frame_graficas)

    # ================= LÓGICA Y BASE DE DATOS =================

    def get_fechas_rango(self, combo_mes, combo_anio=None):
        mes = combo_mes.currentIndex() + 1
        anio = int(combo_anio.currentText()) if combo_anio else QDate.currentDate().year()
        mes_str = f"{anio}-{mes:02d}"
        return mes_str

    def cargar_datos_aclaraciones(self):
        mes_texto = self.cb_mes_aclar.currentText()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # LÓGICA CONDICIONAL: ¿Es "Hoy" o es un Mes?
            if mes_texto == "Hoy":
                query_cot = "SELECT id, DATE(fecha_hora), cliente_nombre, total_inversion, total_precio_final, total_ganancia FROM cotizaciones_maestro WHERE estado = 'Aceptada' AND DATE(fecha_hora) = DATE('now', 'localtime') ORDER BY fecha_hora DESC"
                query_gas = "SELECT id, descripcion, monto FROM otros_gastos WHERE DATE(fecha_hora) = DATE('now', 'localtime') ORDER BY fecha_hora DESC"
                params = ()
            else:
                mes_idx = self.cb_mes_aclar.currentIndex() # "Hoy" es 0, "Enero" es 1
                anio = int(self.cb_anio_aclar.currentText())
                mes_str = f"{anio}-{mes_idx:02d}"
                
                query_cot = "SELECT id, DATE(fecha_hora), cliente_nombre, total_inversion, total_precio_final, total_ganancia FROM cotizaciones_maestro WHERE estado = 'Aceptada' AND strftime('%Y-%m', fecha_hora) = ? ORDER BY fecha_hora DESC"
                query_gas = "SELECT id, descripcion, monto FROM otros_gastos WHERE strftime('%Y-%m', fecha_hora) = ? ORDER BY fecha_hora DESC"
                params = (mes_str,)

            # 1. Cotizaciones (SOLO ACEPTADAS)
            cursor.execute(query_cot, params)
            cotizaciones = cursor.fetchall()

            self.table_cot_aclar.setRowCount(0)
            total_brutas = 0.0

            for idx, cot in enumerate(cotizaciones):
                self.table_cot_aclar.insertRow(idx)
                total_brutas += cot[5] 
                
                f_obj = datetime.strptime(cot[1], '%Y-%m-%d')
                fecha_formateada = f"{f_obj.day} {f_obj.strftime('%b')}, {f_obj.year}"

                items = [
                    QTableWidgetItem(str(cot[0])), QTableWidgetItem(fecha_formateada),
                    QTableWidgetItem(cot[2]), QTableWidgetItem(f"${cot[3]:.2f}"),
                    QTableWidgetItem(f"${cot[4]:.2f}"), QTableWidgetItem(f"${cot[5]:.2f}")
                ]
                for col, item in enumerate(items):
                    self.table_cot_aclar.setItem(idx, col, item)

            # 2. Otros Gastos
            cursor.execute(query_gas, params)
            gastos = cursor.fetchall()

            self.table_gas_aclar.setRowCount(0)
            total_gastos = 0.0

            for idx, gas in enumerate(gastos):
                self.table_gas_aclar.insertRow(idx)
                total_gastos += gas[2]

                items = [
                    QTableWidgetItem(str(gas[0]).zfill(3)),
                    QTableWidgetItem(gas[1]),
                    QTableWidgetItem(f"${gas[2]:.2f}")
                ]
                for col, item in enumerate(items):
                    self.table_gas_aclar.setItem(idx, col, item)

            conn.close()

            # 3. Actualizar Etiquetas de Cálculo
            self.lbl_brutas.setText(f"${total_brutas:.2f}")
            self.lbl_gastos.setText(f"${total_gastos:.2f}")
            
            ganancia_real = total_brutas - total_gastos
            self.lbl_reales.setText(f"${ganancia_real:.2f}")

            if ganancia_real < 0:
                self.lbl_reales.setStyleSheet("color: white; background-color: #dc3545; padding: 5px; font-weight: bold; font-size: 16px; border-radius: 3px;")
            else:
                self.lbl_reales.setStyleSheet("color: black; background-color: #00e6e6; padding: 5px; font-weight: bold; font-size: 16px; border-radius: 3px;")

        except Exception as e:
            QMessageBox.critical(self, "Error BD", f"No se pudieron cargar las aclaraciones:\n{e}")

    def actualizar_graficas(self):
        mes_texto = self.cb_mes_graf.currentText()

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Obtener año desde el combo de gráficas
            anio = int(self.cb_anio_graf.currentText())

            if mes_texto == "Hoy":
                # Datos de hoy agrupados por hora
                cursor.execute("""
                    SELECT strftime('%H:00', fecha_hora) as hora_dia, SUM(total_ganancia), COUNT(id)
                    FROM cotizaciones_maestro
                    WHERE estado = 'Aceptada' AND DATE(fecha_hora) = DATE('now', 'localtime')
                    GROUP BY hora_dia ORDER BY hora_dia ASC
                """)
                datos_barras = cursor.fetchall()
                titulo_barras = "GANANCIAS Y REPARACIONES (HOY)"
                etiq_barras = "Hora"

                # Gastos de hoy
                cursor.execute("""
                    SELECT descripcion, SUM(monto) FROM otros_gastos
                    WHERE DATE(fecha_hora) = DATE('now', 'localtime')
                    GROUP BY descripcion
                """)
                datos_pastel = cursor.fetchall()
                titulo_pastel = "DISTRIBUCIÓN DE GASTOS (HOY)"
            else:
                mes_idx = self.cb_mes_graf.currentIndex()
                mes_str = f"{anio}-{mes_idx+1:02d}"

                # Barras: agrupar por semanas del mes
                cursor.execute("""
                    SELECT strftime('%W', fecha_hora) as semana_anio, SUM(total_ganancia), COUNT(id)
                    FROM cotizaciones_maestro
                    WHERE estado = 'Aceptada' AND strftime('%Y-%m', fecha_hora) = ?
                    GROUP BY semana_anio ORDER BY semana_anio ASC
                """, (mes_str,))
                datos_barras = cursor.fetchall()
                titulo_barras = f"GANANCIAS Y REPARACIONES ({mes_texto.upper()})"
                etiq_barras = "Sem"

                # Pastel: gastos del mes
                cursor.execute("""
                    SELECT descripcion, SUM(monto) FROM otros_gastos
                    WHERE strftime('%Y-%m', fecha_hora) = ?
                    GROUP BY descripcion
                """, (mes_str,))
                datos_pastel = cursor.fetchall()
                titulo_pastel = f"DISTRIBUCIÓN DE GASTOS ({mes_texto.upper()})"

            # ================= GRÁFICA DE BARRAS =================
            chart_bar = QChart()
            chart_bar.setTitle(titulo_barras)
            chart_bar.setTitleFont(QFont("Arial", 12, QFont.Bold))
            chart_bar.setTheme(QChart.ChartThemeDark)
            chart_bar.setBackgroundBrush(QColor(20, 20, 25, 200))

            series = QBarSeries()
            set_ganancias = QBarSet("Ganancias ($)")
            set_ganancias.setColor(QColor("#00e6e6"))
            set_reparaciones = QBarSet("Cant. Reparaciones")
            set_reparaciones.setColor(QColor("#ff7f50"))

            categorias = []
            max_valor = 0

            for i, row in enumerate(datos_barras):
                if mes_texto == "Hoy":
                    nombre_eje = row[0]
                else:
                    nombre_eje = f"{etiq_barras} {i+1}"
                categorias.append(nombre_eje)

                ganancia = row[1] if row[1] is not None else 0.0
                reps = row[2] if row[2] is not None else 0
                set_ganancias.append(ganancia)
                set_reparaciones.append(reps)

                if ganancia > max_valor:
                    max_valor = ganancia
                if reps > max_valor:
                    max_valor = reps

            if not categorias:
                categorias = ["Sin Datos"]
                set_ganancias.append(0)
                set_reparaciones.append(0)

            series.append(set_ganancias)
            series.append(set_reparaciones)
            chart_bar.addSeries(series)

            eje_x = QBarCategoryAxis()
            eje_x.append(categorias)
            chart_bar.addAxis(eje_x, Qt.AlignBottom)
            series.attachAxis(eje_x)

            eje_y = QValueAxis()
            eje_y.setRange(0, max_valor * 1.1 if max_valor > 0 else 100)
            chart_bar.addAxis(eje_y, Qt.AlignLeft)
            series.attachAxis(eje_y)

            # --- Tooltip personalizado para barras ---
            def on_bar_hovered(status, index, barset):
                if status:
                    valor = barset.at(index)
                    tooltip_text = f"{barset.label()}: ${valor:.2f}" if barset == set_ganancias else f"{barset.label()}: {int(valor)}"
                    # Obtener la posición del mouse en pantalla
                    pos = QCursor.pos()
                    # Mostrar tooltip con estilo
                    QToolTip.showText(pos, tooltip_text, None, QRect(), 2000)
                else:
                    QToolTip.hideText()

            series.hovered.connect(on_bar_hovered)

            self.chart_bar_view.setChart(chart_bar)

            # ================= GRÁFICA DE PASTEL =================
            chart_pie = QChart()
            chart_pie.setTitle(titulo_pastel)
            chart_pie.setTitleFont(QFont("Arial", 12, QFont.Bold))
            chart_pie.setTheme(QChart.ChartThemeDark)
            chart_pie.setBackgroundBrush(QColor(20, 20, 25, 200))

            pie_series = QPieSeries()
            colores = ["#2077D4", "#ff7f50", "#00e6e6", "#e68a00", "#9b59b6", "#e74c3c"]

            if not datos_pastel:
                slice_vacio = pie_series.append("Sin Gastos", 1)
                slice_vacio.setColor(QColor("#555555"))
                def on_pie_hovered(slice, state):
                    if state:
                        QToolTip.showText(QCursor.pos(), "No hay gastos registrados", None, QRect(), 2000)
                    else:
                        QToolTip.hideText()
                pie_series.hovered.connect(on_pie_hovered)
            else:
                max_monto = max(row[1] for row in datos_pastel)
                for i, row in enumerate(datos_pastel):
                    desc = row[0]
                    monto = row[1]
                    desc_etiqueta = desc[:15] + "..." if len(desc) > 15 else desc
                    pie_slice = pie_series.append(f"{desc_etiqueta} (${monto:.2f})", monto)
                    pie_slice.setColor(QColor(colores[i % len(colores)]))
                    if monto == max_monto:
                        pie_slice.setExploded(True)
                        pie_slice.setLabelVisible(True)

                def on_pie_hovered(slice, state):
                    if state:
                        # Extraer la descripción original del slice (o usar los datos originales)
                        # El slice.label() ya tiene la descripción truncada, pero podemos mostrarla completa si guardamos la original.
                        # Para simplificar, mostramos el label del slice (que incluye el monto)
                        tooltip_text = slice.label()
                        QToolTip.showText(QCursor.pos(), tooltip_text, None, QRect(), 2000)
                    else:
                        QToolTip.hideText()
                pie_series.hovered.connect(on_pie_hovered)

            chart_pie.addSeries(pie_series)
            self.chart_pie_view.setChart(chart_pie)

            conn.close()

        except Exception as e:
            QMessageBox.critical(self, "Error Gráficas", f"Error al generar gráficas:\n{e}")