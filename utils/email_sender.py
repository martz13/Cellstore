import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailSender:
    @staticmethod
    def enviar_codigo(destinatario, codigo):
        #remitente = "martzm4118@gmail.com"
        #password = "uwxm nhgn bppy azej"
        remitente = "joseluc0103@gmail.com"
        password = "qqbg mskb oxeg nevx"

        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = destinatario
        msg['Subject'] = "Código de Recuperación - Cell Store Technology"

        # Diseño formal del correo en HTML
        cuerpo = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; padding: 20px;">
            <div style="border: 1px solid #2077D4; border-radius: 8px; padding: 30px; max-width: 500px; margin: auto;">
                <h2 style='color: #2077D4; text-align: center;'>CELL STORE TECHNOLOGY</h2>
                <p style="font-size: 16px;">Hola,</p>
                <p style="font-size: 16px;">Has solicitado iniciar sesión a través del sistema de recuperación. Tu código de verificación de 4 dígitos es:</p>
                
                <div style="background-color: #f4f4f4; padding: 15px; text-align: center; border-radius: 5px; margin: 20px 0;">
                    <h1 style='letter-spacing: 10px; color: #333; margin: 0; font-size: 32px;'>{codigo}</h1>
                </div>
                
                <p style="font-size: 14px; color: #666;">Si no solicitaste este código, puedes ignorar este mensaje de forma segura.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(cuerpo, 'html'))

        try:
            # Configuración para el servidor SMTP de Gmail
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls() # Inicia conexión segura
            server.login(remitente, password)
            server.sendmail(remitente, destinatario, msg.as_string())
            server.quit()
            return True, "Correo enviado exitosamente."
        except Exception as e:
            return False, str(e)