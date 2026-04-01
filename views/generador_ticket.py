import os
import sys
import subprocess
from datetime import datetime

from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QTextDocument, QPageSize, QPageLayout
from PySide6.QtCore import QSizeF, Qt, QMarginsF

from database.connection import get_connection, get_asset_path

# === CONFIGURACIÓN MILIMÉTRICA EXACTA ===
PAPEL_ANCHO_MM = 58.0
# 215px equivale casi a 58mm reales. Forza al texto a usar TODO el ancho sin márgenes
ANCHO_LOGICO_PX = 215.0 

class GeneradorTicket:

    @staticmethod
    def _build_printer():
        """Crea QPrinter compatible con cualquier build de PySide6."""
        for mode in ("PrinterResolution", "HighResolution"):
            try:
                return QPrinter(getattr(QPrinter, mode))
            except AttributeError:
                continue
        return QPrinter()

    @staticmethod
    def _make_doc(html: str) -> QTextDocument:
        """Construye un solo documento maestro con ancho congelado."""
        doc = QTextDocument()
        doc.setDocumentMargin(0) # Elimina los márgenes ocultos de Qt
        doc.setHtml(html)
        doc.setTextWidth(ANCHO_LOGICO_PX) # Congela el ancho para evitar que se divida en hojas
        return doc

    @staticmethod
    def _altura_mm(doc: QTextDocument) -> float:
        """Calcula la altura exacta basada en la relación ancho-píxel/mm."""
        alto_px = doc.size().height()
        # Relación directa entre píxeles lógicos y milímetros reales
        alto_mm = (alto_px / ANCHO_LOGICO_PX) * PAPEL_ANCHO_MM
        return alto_mm + 5.0  # margen extra para evitar cortes al final

    @staticmethod
    def _fila_meta(label: str, valor: str) -> str:
        """Etiquetas de información."""
        return (
            f'<p style="margin:0px; padding:0px;"><b>{label}</b></p>'
            f'<p style="margin:0px 0px 4px 0px; padding:0px; text-align:right;">{valor}</p>'
        )

    @staticmethod
    def _fila_item(desc: str, precio: str) -> str:
        """Lista de reparaciones."""
        return (
            f'<p style="margin:0px; padding:0px;">{desc}</p>'
            f'<p style="margin:0px 0px 5px 0px; padding:0px; text-align:right;">{precio}</p>'
        )

    @staticmethod
    def _build_html(empresa, maestro, detalles, cotizacion_id, logo_path) -> str:
        """Estructura HTML limpia y al borde."""
        try:
            fecha_formateada = datetime.strptime(
                maestro[2], "%Y-%m-%d %H:%M:%S"
            ).strftime("%d/%m/%Y %H:%M")
        except Exception:
            fecha_formateada = str(maestro[2])

        # 🔥 SOLUCIÓN LOGO: El 'margin-left: -18px' lo obliga a moverse a la izquierda
        if os.path.exists(logo_path):
            logo_html = f'<div style="text-align:center; margin-left:-18px;"><img src="file:///{logo_path}" width="95"></div>'
        else:
            logo_html = (
                f'<div style="text-align:center; font-size:13px; font-weight:bold;">'
                f'{empresa[0]}</div>'
            )

        filas = ""
        for det in detalles:
            desc = f"{det[0]} {det[1]} - {det[2]}"
            filas += GeneradorTicket._fila_item(desc, f"${det[3]:.2f}")

        num = str(cotizacion_id).zfill(5)

        totales_html = (
            GeneradorTicket._fila_meta("Subtotal:", f"${maestro[3]:.2f}") +
            GeneradorTicket._fila_meta("Anticipo:", f"-${maestro[4]:.2f}") +
            f'<p style="margin:0px; padding:0px; font-size:12px;"><b>RESTANTE:</b></p>'
            f'<p style="margin:0px; padding:0px; text-align:right; font-size:12px; font-weight:bold;">${maestro[5]:.2f}</p>'
        )

        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body {{
    font-family: 'Courier New', Courier, monospace;
    font-size: 10px;
    color: #000;
    margin: 0px; 
    padding: 0px; 
}}
p {{ margin: 0px; padding: 0px; }}
.hr {{ border-top: 1px dashed #000; margin: 4px 0px; }}
</style></head>
<body>

{logo_html}
<div style="text-align:center;">
<p>{empresa[1]}</p>
<p>Tel: {empresa[2]}</p>
</div>

<div class="hr"></div>

{GeneradorTicket._fila_meta("Ticket:", num)}
{GeneradorTicket._fila_meta("Fecha:", fecha_formateada)}
{GeneradorTicket._fila_meta("Cliente:", maestro[0])}
{GeneradorTicket._fila_meta("Tel:", str(maestro[1]))}

<div class="hr"></div>

<p><b>Descripción</b></p>
{filas}

<div class="hr"></div>

{totales_html}

<div class="hr"></div>

<div style="text-align:center;">
<p>&quot;{empresa[3]}&quot;</p>
<br>
<p>*** Gracias por su preferencia ***</p>
<p>CELL STORE TECHNOLOGY</p>
</div>

</body></html>"""

    @staticmethod
    def generar_ticket(parent_widget, cotizacion_id):
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT nombre, direccion, telefono, slogan FROM datos_empresa WHERE id=1")
            empresa = cursor.fetchone()

            cursor.execute(
                """SELECT cliente_nombre, cliente_telefono, fecha_hora,
                          total_precio_final, monto_adelanto, monto_restante
                   FROM cotizaciones_maestro WHERE id=?""",
                (cotizacion_id,),
            )
            maestro = cursor.fetchone()

            cursor.execute(
                """SELECT marca, modelo, trabajo_a_realizar, precio_cliente
                   FROM cotizaciones_detalle WHERE cotizacion_id=?""",
                (cotizacion_id,),
            )
            detalles = cursor.fetchall()
            conn.close()
            conn = None

            if not maestro:
                QMessageBox.warning(parent_widget, "Error", "No se encontró la cotización.")
                return

            if not empresa:
                empresa = ("CELL STORE TECHNOLOGY", "Direccion no configurada", "Tel no configurado", "Tu solucion")

            logo_path = get_asset_path("assets/images/icono2.jpg").replace("\\", "/")

            html = GeneradorTicket._build_html(empresa, maestro, detalles, cotizacion_id, logo_path)

            # 🔥 1. CREAMOS EL DOCUMENTO MAESTRO UNA SOLA VEZ
            doc_maestro = GeneradorTicket._make_doc(html)
            # Calculamos la altura perfecta para forzar que sea exactamente 1 sola hoja
            alto_mm = GeneradorTicket._altura_mm(doc_maestro)

            msg = QMessageBox(parent_widget)
            msg.setWindowTitle("Finalizar Cotizacion")
            msg.setIcon(QMessageBox.Question)
            msg.setText(f"Cotizacion {str(cotizacion_id).zfill(5)} generada.\n\n¿Que desea hacer?")
            btn_print = msg.addButton("Imprimir Ticket", QMessageBox.ActionRole)
            btn_pdf   = msg.addButton("Ver/Guardar PDF", QMessageBox.ActionRole)
            btn_close = msg.addButton("Solo Cerrar",     QMessageBox.RejectRole)
            msg.setDefaultButton(btn_print)
            msg.exec()

            clicked = msg.clickedButton()
            if clicked == btn_close:
                return

            # ================= 5. PDF =================
            if clicked == btn_pdf:
                ruta, _ = QFileDialog.getSaveFileName(
                    parent_widget, "Guardar Ticket PDF",
                    f"Ticket_{str(cotizacion_id).zfill(5)}.pdf", "Documento PDF (*.pdf)",
                )
                if not ruta:
                    return

                QApplication.setOverrideCursor(Qt.WaitCursor)
                try:
                    printer = GeneradorTicket._build_printer()
                    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                    printer.setOutputFileName(ruta)
                    
                    # 🔥 2. Aplicamos la misma medida exacta para evitar cortes
                    printer.setPageSize(QPageSize(QSizeF(PAPEL_ANCHO_MM, alto_mm), QPageSize.Unit.Millimeter))
                    printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
                    printer.setFullPage(True)

                    doc_maestro.print_(printer)
                finally:
                    QApplication.restoreOverrideCursor()

                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    subprocess.call(["open", ruta])
                else:
                    try:
                        subprocess.call(["xdg-open", ruta])
                    except Exception:
                        pass

            # ================= 6. IMPRESION DIRECTA =================
            elif clicked == btn_print:
                printer = GeneradorTicket._build_printer()
                dialog = QPrintDialog(printer, parent_widget)
                dialog.setWindowTitle("Imprimir Ticket")

                if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    try:
                        # 🔥 3. Usamos la misma regla para la impresora física
                        printer.setPageSize(QPageSize(QSizeF(PAPEL_ANCHO_MM, alto_mm), QPageSize.Unit.Millimeter))
                        printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
                        printer.setFullPage(True)

                        doc_maestro.print_(printer)
                    finally:
                        QApplication.restoreOverrideCursor()

        except Exception as e:
            if conn:
                conn.close()
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                parent_widget,
                "Error Critico",
                f"Ocurrio un error al generar el ticket:\n\n{str(e)}",
            )