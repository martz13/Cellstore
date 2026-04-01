import os
import sys
import subprocess
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QTextDocument, QPageSize
from PySide6.QtPrintSupport import QPrinter
from datetime import datetime
from database.connection import get_connection, get_asset_path


class GeneradorPDF:

    @staticmethod
    def generar_cotizacion(parent_widget, cotizacion_id):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # ================= EMPRESA =================
            cursor.execute("SELECT nombre, direccion, telefono, slogan FROM datos_empresa WHERE id=1")
            empresa = cursor.fetchone()

            if not empresa:
                empresa = ("CELL STORE TECHNOLOGY", 
                          "Av. independencia #27, plaza los arcos, villa cuauhtémoc", 
                          "+52 722 158 0353",
                          "Todo en una solución")

            # ================= MAESTRO =================
            cursor.execute("""
                SELECT cliente_nombre, cliente_telefono, fecha_hora, total_precio_final
                FROM cotizaciones_maestro
                WHERE id=?
            """, (cotizacion_id,))
            maestro = cursor.fetchone()

            if not maestro:
                QMessageBox.warning(parent_widget, "Error", "No se encontró la cotización.")
                return

            cliente, telefono, fecha_hora, total = maestro

            # ================= DETALLE =================
            cursor.execute("""
                SELECT marca, modelo, trabajo_a_realizar, observaciones, precio_cliente
                FROM cotizaciones_detalle
                WHERE cotizacion_id=?
            """, (cotizacion_id,))
            detalles = cursor.fetchall()

            conn.close()

            # ================= FECHA =================
            f = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M:%S")
            fecha = f.strftime("%d/%m/%Y %H:%M")

            # ================= LOGO =================
            logo_path = get_asset_path("assets/images/icono2.jpg")
            logo_path = logo_path.replace('\\', '/')
            
            import os.path
            logo_html = ""
            if os.path.exists(logo_path):
                logo_html = f'<img src="file:///{logo_path}" width="100" style="vertical-align: middle;">'
            else:
                logo_html = "📱"

            # ================= HTML CON LOGO Y MEJOR FORMATO =================
            html = f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: 'Arial', 'Helvetica', sans-serif;
                        font-size: 12pt;
                        margin: 40px;
                        line-height: 1.4;
                    }}
                    .header-table {{
                        width: 100%;
                        margin-bottom: 20px;
                        border-bottom: 2px solid #2077D4;
                        padding-bottom: 15px;
                    }}
                    .logo-cell {{
                        width: 20%;
                        vertical-align: middle;
                    }}
                    .empresa-cell {{
                        width: 50%;
                        vertical-align: middle;
                    }}
                    .cotizacion-cell {{
                        width: 30%;
                        text-align: right;
                        vertical-align: middle;
                    }}
                    .empresa-nombre {{
                        font-size: 22pt;
                        font-weight: bold;
                        color: #2077D4;
                        margin: 0;
                    }}
                    .slogan {{
                        font-size: 11pt;
                        color: #666;
                        font-style: italic;
                        margin-top: 5px;
                    }}
                    .info-cliente {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                        background-color: #f5f5f5;
                    }}
                    .info-cliente td {{
                        padding: 12px;
                        border: 1px solid #ddd;
                    }}
                    .tabla-items {{
                        width: 100%;
                        border-collapse: collapse;
                        margin: 20px 0;
                    }}
                    .tabla-items th {{
                        background-color: #2077D4;
                        color: white;
                        padding: 12px;
                        text-align: left;
                        font-weight: bold;
                    }}
                    .tabla-items td {{
                        padding: 10px;
                        border: 1px solid #ddd;
                        vertical-align: top;
                    }}
                    .observacion {{
                        font-size: 10pt;
                        color: #666;
                        font-style: italic;
                        margin-top: 5px;
                    }}
                    .total {{
                        font-size: 18pt;
                        font-weight: bold;
                        color: #2077D4;
                        text-align: right;
                        margin-top: 20px;
                        padding-top: 15px;
                        border-top: 2px solid #2077D4;
                    }}
                    .condiciones {{
                        margin-top: 40px;
                        padding: 15px;
                        background-color: #f9f9f9;
                        border-left: 4px solid #2077D4;
                        font-size: 10pt;
                        color: #555;
                    }}
                    .footer {{
                        margin-top: 30px;
                        text-align: center;
                        font-size: 9pt;
                        color: #999;
                        border-top: 1px solid #ddd;
                        padding-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <!-- ENCABEZADO CON LOGO -->
                <table class="header-table" cellpadding="0" cellspacing="0">
                    <tr>
                        <td class="logo-cell">
                            {logo_html}
                        </td>
                        <td class="empresa-cell">
                            <div class="empresa-nombre">{empresa[0]}</div>
                            <div class="slogan">"{empresa[3]}"</div>
                        </td>
                        <td class="cotizacion-cell">
                            <div style="font-size: 18pt; font-weight: bold; color: #2077D4;">COTIZACIÓN</div>
                            <div style="font-size: 11pt; margin-top: 5px;"><strong>Folio:</strong> {str(cotizacion_id).zfill(6)}</div>
                            <div style="font-size: 11pt;"><strong>Fecha:</strong> {fecha}</div>
                        </td>
                    </tr>
                </table>

                <!-- INFORMACIÓN DEL CLIENTE -->
                <table class="info-cliente" cellpadding="0" cellspacing="0">
                    <tr>
                        <td width="50%"><strong>Cliente:</strong> {cliente}</td>
                        <td width="50%"><strong>Teléfono:</strong> {telefono}</td>
                    </tr>
                </table>

                <!-- TABLA DE SERVICIOS -->
                <table class="tabla-items" cellpadding="0" cellspacing="0">
                    <thead>
                        <tr>
                            <th width="20%">MARCA</th>
                            <th width="20%">MODELO</th>
                            <th width="45%">TRABAJO A REALIZAR</th>
                            <th width="15%">PRECIO</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for d in detalles:
                marca, modelo, trabajo, obs, precio = d
                html += f"""
                        <tr>
                            <td><strong>{marca}</strong></td>
                            <td>{modelo}</td>
                            <td>
                                {trabajo}
                                {f'<div class="observacion">📝 {obs}</div>' if obs else ''}
                            </td>
                            <td align="right"><strong>${precio:.2f}</strong></td>
                        </tr>
                """

            html += f"""
                    </tbody>
                </table>

                <!-- TOTAL -->
                <div class="total">
                    TOTAL: ${total:.2f}
                </div>

                <!-- TÉRMINOS Y CONDICIONES -->
                <div class="condiciones">
                    <strong>TÉRMINOS Y CONDICIONES:</strong><br>
                    • La garantía cubre únicamente la reparación realizada por un período de 15 días naturales.<br>
                    • No se aceptan devoluciones después de 48 horas de entregado el equipo.<br>
                    • El abono no es reembolsable en caso de cancelación del servicio.<br>
                    • Los precios están sujetos a cambios sin previo aviso.<br>
                    • Se requiere presentar este documento para hacer efectiva la garantía.<br>
                    • El tiempo de reparación es estimado y puede variar según la disponibilidad de piezas.<br>
                    • La tienda no se hace responsable por daños causados por el mal uso del equipo.<br>
                    • Al aceptar este servicio, el cliente acepta los términos aquí establecidos.<br>
                    • Después de 30 dias no nos hacemos responsables por equipos que no hayan pasado a recoger
                </div>

                <!-- FOOTER -->
                <div class="footer">
                    <strong>{empresa[0]}</strong><br>
                    {empresa[1]} | 📞 {empresa[2]}<br>
                    Documento generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}
                </div>
            </body>
            </html>
            """

            # ================= PDF =================
            nombre = f"Cotizacion_{str(cotizacion_id).zfill(6)}.pdf"

            ruta, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Guardar PDF",
                nombre,
                "PDF (*.pdf)"
            )

            if not ruta:
                return

            if not ruta.endswith(".pdf"):
                ruta += ".pdf"

            doc = QTextDocument()
            doc.setHtml(html)

            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(ruta)
            printer.setPageSize(QPageSize(QPageSize.A4))

            doc.print_(printer)

            # abrir
            respuesta = QMessageBox.question(
                parent_widget,
                "PDF Generado",
                f"✅ Cotización generada con éxito!\n\n"
                f"📄 Archivo: {os.path.basename(ruta)}\n"
                f"📁 Ubicación: {os.path.dirname(ruta)}\n\n"
                f"¿Deseas abrir el PDF ahora?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    subprocess.call(["open", ruta])
                else:
                    subprocess.call(["xdg-open", ruta])

        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Hubo un problema al generar el PDF:\n\n{str(e)}")