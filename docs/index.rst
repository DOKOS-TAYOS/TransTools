TransTools Documentation
========================

TransTools es una aplicacion de escritorio para seguimiento local y privado durante la transicion. Su alcance actual combina registros diarios, un modulo de acompanamiento personal, revision de datos y exportes locales, todo sin depender de servicios online.

Resumen del producto
--------------------

La aplicacion esta pensada para uso personal. Hoy permite:

- onboarding inicial con nombre y configuracion opcional de salud
- registro de voz con analisis local
- registro de medicacion
- registro de visitas y eventos libres
- diario de habitos adaptativo
- centro de acompanamiento con panel, hoja de ruta, citas y bienestar
- vista de datos con calendario, resumen diario y grafica semanal
- exportacion local a CSV, XLSX, PDF y PNG
- directorio de contactos de apoyo
- configuracion general y transferencia completa del perfil local

Privacidad y datos
------------------

Los principios actuales de la aplicacion son:

- funcionamiento offline
- datos guardados localmente
- metricas sensibles de tono cifradas con clave local
- tono visible solo en agregados semanales
- exportacion e importacion del perfil incluyendo la clave local de voz

Por defecto, los datos se guardan en la carpeta de usuario del sistema:

- Windows: ``%APPDATA%\TransTools``
- Linux: ``${XDG_DATA_HOME:-~/.local/share}/transtools``

Si se define ``FILE_OUTPUT_DIR`` en ``.env``, la app usa esa ruta personalizada.

Puesta en marcha
----------------

Para trabajar directamente desde el repositorio:

- en Windows: ``setup.bat`` y despues ``bin\run.bat``
- en Linux: ``chmod +x setup.sh bin/run.sh`` seguido de ``./setup.sh`` y ``./bin/run.sh``

Detalles utiles del flujo actual:

- ``setup.bat`` y ``setup.sh`` crean o reutilizan ``.venv``, instalan dependencias y preparan ``.env``.
- ``bin\run.bat --check`` y ``./bin/run.sh --check`` validan la instalacion sin abrir la app.
- ``install.bat`` e ``install.sh`` sirven como flujo de clonado + preparacion en un solo paso.

El ``README.md`` del repo contiene la guia mas completa de instalacion, configuracion, solucion de problemas y uso recomendado.

Referencia para desarrollo
--------------------------

La referencia API de Sphinx esta enfocada a desarrollo y mantenimiento del codigo, no a uso final de la aplicacion.

.. toctree::
   :maxdepth: 2
   :caption: Contenido

   api
