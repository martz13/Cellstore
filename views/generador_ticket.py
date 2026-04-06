import os
import sys
import subprocess
import tempfile
import time
from datetime import datetime
from io import BytesIO

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from PySide6.QtWidgets import (
    QFileDialog, QMessageBox, QApplication,
    QDialog, QLabel, QVBoxLayout, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from database.connection import get_connection, get_asset_path


# ─────────────────────────────────────────────────────────────────
#  CONSTANTES DE PAPEL
# ─────────────────────────────────────────────────────────────────
ANCHO_MM  = 58.0   # ancho del rollo térmico
MARG_MM   =  2.0   # margen lateral (izq y der)
UTIL_MM   = ANCHO_MM - MARG_MM * 2   # 54 mm útiles

# Fuentes modernas, gruesas y elegantes (imprimen negro puro sin verse "gris")
F_NORM = "Helvetica-Bold"
F_BOLD = "Helvetica-Bold"

# Tamaños
FS_SM  =  8   # secundario
FS_MD  =  9   # normal
FS_LG  = 11   # grande (precios, restante)
FS_XL  = 13   # título empresa si no hay logo

# Espaciados verticales (en mm)
IL   = 3.8   # interlineado normal
SEP  = 2.5   # espacio entre bloques
HR   = 4.0   # altura que ocupa un separador


# ─────────────────────────────────────────────────────────────────
#  CLASE
# ─────────────────────────────────────────────────────────────────
class GeneradorTicket:

    # ── Utilidades de dibujo ─────────────────────────────────────

    @staticmethod
    def _hr(c: canvas.Canvas, y: float):
        """Línea punteada horizontal a lo ancho del papel."""
        c.setDash(2, 2)
        c.setLineWidth(0.4)
        c.line(MARG_MM * mm, y, (ANCHO_MM - MARG_MM) * mm, y)
        c.setDash()

    @staticmethod
    def _izq(c, y, txt, font=F_NORM, fs=FS_MD):
        c.setFont(font, fs)
        c.drawString(MARG_MM * mm, y, txt)

    @staticmethod
    def _der(c, y, txt, font=F_NORM, fs=FS_MD):
        c.setFont(font, fs)
        c.drawRightString((ANCHO_MM - MARG_MM) * mm, y, txt)

    @staticmethod
    def _centro(c, y, txt, font=F_NORM, fs=FS_MD):
        c.setFont(font, fs)
        c.drawCentredString((ANCHO_MM / 2) * mm, y, txt)

    @staticmethod
    def _wrap(texto: str, max_chars: int = 28) -> list:
        """Word-wrap simple: devuelve lista de líneas."""
        palabras = texto.split()
        lineas, actual = [], ""
        for p in palabras:
            if len(actual) + len(p) + (1 if actual else 0) <= max_chars:
                actual += (" " if actual else "") + p
            else:
                if actual:
                    lineas.append(actual)
                while len(p) > max_chars:
                    lineas.append(p[:max_chars])
                    p = p[max_chars:]
                actual = p
        if actual:
            lineas.append(actual)
        return lineas or [""]

    # ── Construcción del PDF ──────────────────────────────────────

    @staticmethod
    def _pdf_bytes(empresa, maestro, detalles,
                   cotizacion_id, logo_path) -> bytes:
        """
        Genera el ticket con ReportLab y retorna los bytes del PDF.
        La altura de la página se calcula dinámicamente para que
        siempre sea exactamente 1 hoja, sin espacios en blanco.
        """
        num = str(cotizacion_id).zfill(5)

        try:
            fecha = datetime.strptime(
                maestro[2], "%Y-%m-%d %H:%M:%S"
            ).strftime("%d/%m/%Y %H:%M")
        except Exception:
            fecha = str(maestro[2])

        # Preparar items con wrap
        items = []
        for det in detalles:
            desc = f"{det[0]} {det[1]} - {det[2]}"
            items.append((_wrap(desc), f"${det[3]:.2f}"))

        # ── Calcular altura total necesaria ───────────────────────
        tiene_logo = os.path.exists(logo_path)
        alto = 4 * mm                                # padding top
        alto += (22 if tiene_logo else 0) * mm       # logo
        alto += SEP * mm
        lineas_dir = _wrap(empresa[1], max_chars=32)
        alto += len(lineas_dir) * IL * mm   # dirección (puede ser varias líneas)
        alto += IL * mm                      # tel empresa                         # dir + tel empresa
        alto += SEP * mm
        alto += HR * mm                              # separador
        alto += 4 * 2 * IL * mm                     # ticket/fecha/cliente/tel
        alto += HR * mm
        alto += IL * mm                              # header descripcion
        for lineas, _ in items:
            alto += len(lineas) * IL * mm
            alto += IL * mm                          # precio
            alto += SEP * mm
        alto += HR * mm
        alto += 2 * 2 * IL * mm                     # subtotal + anticipo
        alto += 2 * IL * mm                         # restante (más grande)
        alto += HR * mm
        alto += 3 * IL * mm + SEP * mm              # pie
        alto += 5 * mm                              # padding bottom

        # ── Dibujar ───────────────────────────────────────────────
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=(ANCHO_MM * mm, alto))
        c.setTitle(f"Ticket {num}")
        c.setFillColorRGB(0, 0, 0) # Fuerza el color 100% negro puro

        # y empieza desde arriba
        y = alto - 4 * mm

        # LOGO
        if tiene_logo:
            iw = ih = 20 * mm
            ix = (ANCHO_MM / 2) * mm - iw / 2
            c.drawImage(
                logo_path, ix, y - ih, width=iw, height=ih,
                preserveAspectRatio=True, mask="auto",
            )
            y -= ih + SEP * mm
        else:
            _centro(c, y, empresa[0], F_BOLD, FS_XL)
            y -= IL * mm + SEP * mm

        # Dirección y teléfono de la empresa
        for linea_dir in _wrap(empresa[1], max_chars=32):
            _centro(c, y, linea_dir, F_NORM, FS_SM)
            y -= IL * mm
        _centro(c, y, f"Tel: {empresa[2]}", F_NORM, FS_SM)
        y -= IL * mm + SEP * mm

        # ── Separador ─────────────────────────────────────────────
        _hr(c, y); y -= HR * mm

        # ── Meta (par: label arriba-izq / valor abajo-der) ────────
        def par(label, valor, fs_val=FS_MD):
            nonlocal y
            _izq(c, y, label, F_BOLD, FS_MD)
            y -= IL * mm
            _der(c, y, valor, F_NORM, fs_val)
            y -= IL * mm

        par("Ticket:", num)
        par("Fecha:", fecha)
        par("Cliente:", maestro[0])
        par("Tel:", str(maestro[1]))

        # ── Separador ─────────────────────────────────────────────
        _hr(c, y); y -= HR * mm

        # ── Descripción e items ───────────────────────────────────
        _izq(c, y, "Descripcion", F_BOLD, FS_MD)
        y -= IL * mm

        for lineas, precio in items:
            for ln in lineas:
                _izq(c, y, ln, F_NORM, FS_MD)
                y -= IL * mm
            _der(c, y, precio, F_BOLD, FS_LG)
            y -= IL * mm + SEP * mm

        # ── Separador ─────────────────────────────────────────────
        _hr(c, y); y -= HR * mm

        # ── Totales ───────────────────────────────────────────────
        par("Subtotal:", f"${maestro[3]:.2f}")
        par("Anticipo:", f"-${maestro[4]:.2f}")

        _izq(c, y, "RESTANTE:", F_BOLD, FS_LG)
        y -= IL * mm
        _der(c, y, f"${maestro[5]:.2f}", F_BOLD, FS_LG)
        y -= IL * mm

        # ── Separador ─────────────────────────────────────────────
        _hr(c, y); y -= HR * mm

        # ── Pie ───────────────────────────────────────────────────
        _centro(c, y, f'"{empresa[3]}"', F_NORM, FS_MD)
        y -= IL * mm
        _centro(c, y, "* Gracias por su preferencia *", F_NORM, FS_MD)
        y -= IL * mm
        _centro(c, y, "CELL STORE TECHNOLOGY", F_BOLD, FS_MD)

        c.save()
        return buf.getvalue()

    # ── Atajos de dibujo a nivel módulo (para usar en _pdf_bytes) ─
    # (se usan como funciones locales dentro del método)

    # ── Vista previa ──────────────────────────────────────────────

    @staticmethod
    def _get_poppler_path() -> str | None:
        """
        Devuelve el path a los binarios de Poppler según el entorno.
        - En el ejecutable PyInstaller: busca en assets/tools/poppler
        - En desarrollo Linux: retorna None (usa el del sistema)
        """
        if getattr(sys, "frozen", False):
            # Estamos dentro de un .exe generado por PyInstaller
            base = sys._MEIPASS
            # El YML descomprime en poppler/Release-24.02.0-0/Library/bin
            for sub in [
                os.path.join("assets", "tools", "poppler"),
                os.path.join("assets", "tools", "poppler", "Release-24.02.0-0", "Library", "bin"),
            ]:
                candidate = os.path.join(base, sub)
                if os.path.isdir(candidate):
                    # Buscar subcarpeta /bin si existe
                    bin_path = os.path.join(candidate, "Library", "bin")
                    if os.path.isdir(bin_path):
                        return bin_path
                    return candidate
            return None  # fallback
        # Desarrollo en Linux/macOS: poppler ya está en PATH
        return None

    @staticmethod
    def _previsualizar(parent_widget, pdf_bytes: bytes, num: str):
        try:
            from pdf2image import convert_from_bytes

            poppler_path = GeneradorTicket._get_poppler_path()

            kwargs = {"dpi": 200}
            if poppler_path:
                kwargs["poppler_path"] = poppler_path

            imagenes = convert_from_bytes(pdf_bytes, **kwargs)
            if not imagenes:
                raise RuntimeError("No se renderizó ninguna página.")

            buf2 = BytesIO()
            imagenes[0].save(buf2, format="PNG")
            buf2.seek(0)

            pix = QPixmap()
            pix.loadFromData(buf2.read())

            dlg = QDialog(parent_widget)
            dlg.setWindowTitle(f"Vista previa — Ticket {num}")
            dlg.setModal(True)

            lbl = QLabel()
            lbl.setPixmap(pix)
            lbl.setAlignment(Qt.AlignCenter)

            scroll = QScrollArea()
            scroll.setWidget(lbl)
            scroll.setWidgetResizable(True)
            scroll.setMinimumSize(300, 520)

            btn = QPushButton("Cerrar")
            btn.clicked.connect(dlg.accept)

            lay = QVBoxLayout(dlg)
            lay.addWidget(scroll)
            lay.addWidget(btn)
            dlg.exec()

        except ImportError:
            QMessageBox.information(
                parent_widget,
                "Vista previa no disponible",
                "Instala pdf2image:\n\n  pip install pdf2image",
            )
        except Exception as e:
            QMessageBox.warning(
                parent_widget, "Vista previa", f"No se pudo mostrar:\n{e}"
            )

    # ── Punto de entrada principal ────────────────────────────────

    @staticmethod
    def generar_ticket(parent_widget, cotizacion_id):
        conn = None
        try:
            # 1. Leer BD
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT nombre, direccion, telefono, slogan "
                "FROM datos_empresa WHERE id=1"
            )
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

            # 2. Validar
            if not maestro:
                QMessageBox.warning(
                    parent_widget, "Error", "No se encontró la cotización."
                )
                return

            if not empresa:
                empresa = (
                    "CELL STORE TECHNOLOGY",
                    "Dirección no configurada",
                    "Tel no configurado",
                    "Tu solución tecnológica",
                )

            logo_path = get_asset_path(
                "assets/images/icono2.jpg"
            ).replace("\\", "/")

            num = str(cotizacion_id).zfill(5)

            # 3. Generar PDF en memoria
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                pdf_bytes = GeneradorTicket._pdf_bytes(
                    empresa, maestro, detalles, cotizacion_id, logo_path
                )
            finally:
                QApplication.restoreOverrideCursor()

            # 4. Preguntar al usuario
            msg = QMessageBox(parent_widget)
            msg.setWindowTitle("Finalizar Cotización")
            msg.setIcon(QMessageBox.Question)
            msg.setText(
                f"Cotización {num} generada.\n\n¿Qué desea hacer?"
            )
            btn_print   = msg.addButton("Imprimir Ticket", QMessageBox.ActionRole)
            btn_pdf     = msg.addButton("Guardar PDF",     QMessageBox.ActionRole)
            btn_preview = msg.addButton("Vista Previa",    QMessageBox.ActionRole)
            btn_close   = msg.addButton("Solo Cerrar",     QMessageBox.RejectRole)
            msg.setDefaultButton(btn_print)
            msg.exec()

            clicked = msg.clickedButton()

            # 5. Vista previa
            if clicked == btn_preview:
                GeneradorTicket._previsualizar(parent_widget, pdf_bytes, num)
                return

            if clicked == btn_close:
                return

            # 6. Guardar PDF
            if clicked == btn_pdf:
                ruta, _ = QFileDialog.getSaveFileName(
                    parent_widget,
                    "Guardar Ticket PDF",
                    f"Ticket_{num}.pdf",
                    "Documento PDF (*.pdf)",
                )
                if not ruta:
                    return
                with open(ruta, "wb") as f:
                    f.write(pdf_bytes)

                # Abrir con visor del sistema
                if sys.platform == "win32":
                    os.startfile(ruta)
                elif sys.platform == "darwin":
                    subprocess.call(["open", ruta])
                else:
                    try:
                        subprocess.call(["xdg-open", ruta])
                    except Exception:
                        pass

            # 7. Imprimir directamente
            # 7. Imprimir directamente (Con selección de impresora y SumatraPDF)
            elif clicked == btn_print:
                
                
                # a) Mostrar diálogo para que el usuario elija su impresora
                printer_obj = QPrinter()
                dialog = QPrintDialog(printer_obj, parent_widget)
                dialog.setWindowTitle("Seleccionar Impresora Térmica")
                
                # b) Si el usuario acepta y elige una impresora
                if dialog.exec() == QPrintDialog.DialogCode.Accepted:
                    printer_name = printer_obj.printerName()
                    
                    # Guardamos el PDF temporalmente
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                        tmp.write(pdf_bytes)
                        tmp_path = tmp.name

                    try:
                        if sys.platform == "win32":
                            # Windows: Usar SumatraPDF empacado en nuestro ejecutable
                            sumatra_path = get_asset_path("assets/tools/SumatraPDF.exe").replace("/", "\\")
                            
                            if not os.path.exists(sumatra_path):
                                QMessageBox.warning(parent_widget, "Error", "Motor de impresión (SumatraPDF) no encontrado.")
                                return

                            # Comando para imprimir silenciosamente en la impresora elegida
                            cmd = [sumatra_path, "-print-to", printer_name, "-silent", tmp_path]
                            
                            # creationflags=0x08000000 oculta la consola negra de CMD en Windows
                            subprocess.run(cmd, creationflags=0x08000000)
                            
                        else:
                            # Linux / macOS (Para que siga funcionando en tu entorno de desarrollo)
                            result = subprocess.call(["lp", "-d", printer_name, tmp_path])
                            if result != 0:
                                subprocess.call(["xdg-open", tmp_path])
                    finally:
                        time.sleep(2)
                        try:
                            os.unlink(tmp_path)
                        except Exception:
                            pass

        except Exception as e:
            if conn:
                conn.close()
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(
                parent_widget,
                "Error Crítico",
                f"Ocurrió un error al generar el ticket:\n\n{str(e)}",
            )


# ── Aliases internos para usar dentro de _pdf_bytes ──────────────
# (evita el self. dentro de un @staticmethod)
_hr     = GeneradorTicket._hr
_izq    = GeneradorTicket._izq
_der    = GeneradorTicket._der
_centro = GeneradorTicket._centro
_wrap   = GeneradorTicket._wrap