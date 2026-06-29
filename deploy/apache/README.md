# Despliegue con Apache

Hay dos formas viables de usar Apache con esta app.

## Opcion recomendada: Apache como proxy inverso

Usa esta opcion en VPS, servidor propio o cloud con acceso a servicios del sistema.
Apache recibe el dominio publico y Uvicorn ejecuta FastAPI en `127.0.0.1:8000`.

1. Copia el proyecto al servidor, por ejemplo:

   ```bash
   /var/www/SuiteDigitalFresnilloWeb
   ```

2. Crea entorno virtual e instala dependencias:

   ```bash
   cd /var/www/SuiteDigitalFresnilloWeb
   python3 -m venv .venv
   . .venv/bin/activate
   pip install -e .
   ```

3. Prueba Uvicorn local:

   ```bash
   SUITE_HOST=127.0.0.1 SUITE_PORT=8000 python main.py
   ```

4. Instala el servicio:

   ```bash
   sudo cp deploy/systemd/suite-digital-fresnillo.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now suite-digital-fresnillo
   ```

5. Instala el VirtualHost de Apache:

   ```bash
   sudo a2enmod proxy proxy_http headers rewrite ssl
   sudo cp deploy/apache/suite-digital-fresnillo.conf /etc/apache2/sites-available/
   sudo nano /etc/apache2/sites-available/suite-digital-fresnillo.conf
   sudo a2ensite suite-digital-fresnillo
   sudo systemctl reload apache2
   ```

6. Cambia `ejemplo.com` por tu dominio real.

7. Para HTTPS, usa Certbot o el certificado de tu proveedor:

   ```bash
   sudo certbot --apache -d ejemplo.com -d www.ejemplo.com
   ```

## Opcion hosting compartido: Passenger / Python App

Algunos hosts con Apache/cPanel no dejan correr servicios propios, pero ofrecen
`Setup Python App` o Passenger. En ese caso usa:

```text
passenger_wsgi.py
```

Ese archivo adapta FastAPI/ASGI a WSGI usando `a2wsgi`.

Configuracion tipica:

- Application root: carpeta raiz del proyecto.
- Application startup file: `passenger_wsgi.py`.
- Application entry point: `application`.
- Python version: 3.12 o superior.
- Paquetes: instalar con `pip install -e .` o desde el panel del host.

Limitaciones del hosting compartido:

- Debe permitir instalar paquetes con ruedas nativas como `PyMuPDF` y `Pillow`.
- Debe permitir ejecutar LibreOffice si quieres conversion DOCX/XLSX/PPTX.
- Puede limitar tamano de subida y tiempo de ejecucion.

Si el host solo acepta HTML/PHP estatico, el backend no podra funcionar ahi.

