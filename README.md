# TransTools

Aplicación de escritorio (Tkinter + Python) para acompañar a personas trans durante la transición con registros locales, seguimiento semanal y exportación de informes.

## Características principales

- Onboarding inicial (3 pasos) con nombre y configuración opcional de salud.
- Menú modular:
  - Registro de voz
  - Registro de medicación
  - Otros registros (visitas médicas/psicología + eventos libres)
  - Diario de hábitos adaptativo
  - Información y contactos
  - Información de aplicación
  - Ver mis datos (calendario, resumen diario no sensible y gráficas semanales)
  - Configuración
- Registro de fechas pasadas en todos los módulos de registro.
- Privacidad de voz:
  - Métricas sensibles de tono cifradas localmente.
  - No se muestra tono diario; solo agregados semanales.
- Exportación local: CSV, XLSX, PDF, PNG.
- Sistema de logs configurable.
- Funcionamiento 100% offline.

## Requisitos

- Python 3.12+
- Windows 10/11 o Linux

## Instalación y ejecución

### Windows

```bat
setup.bat
bin\run.bat
```

Opcional (clonado + setup):

```bat
install.bat
```

### Linux

```bash
chmod +x setup.sh bin/run.sh
./setup.sh
./bin/run.sh
```

Opcional (clonado + setup):

```bash
chmod +x install.sh
./install.sh
```

## Entorno virtual obligatorio

Todo se ejecuta sobre `.venv` (no usa el Python global del sistema para correr la app).

## Apariencia

- La interfaz solo permite ajustar `UI_THEME_MODE` (`dark` o `light`) y `UI_FONT_SIZE`.
- El resto del estilo visual se calcula automÃ¡ticamente a partir de esos dos valores.
- La fuente se toma del sistema operativo/Tk para que la app se comporte mejor en Windows y Linux.

## Dónde se guardan los datos

- Por defecto, TransTools guarda los datos de usuario en una carpeta de usuario del sistema:
  - Windows: `%APPDATA%\TransTools`
  - Linux: `${XDG_DATA_HOME:-~/.local/share}/transtools`
- Si antes usabas el directorio legacy `output/` del proyecto, la app migra automáticamente los archivos de datos la primera vez que arranca con la nueva configuración.
- Si defines `FILE_OUTPUT_DIR` en `.env`, ese valor se respeta como carpeta personalizada.

## Estructura técnica

- `src/frontend/`: UI Tkinter (ventanas y diálogos)
- `src/core/`: servicios de dominio, estado versionado, privacidad y exportes
- `src/audio/`: grabación y análisis acústico
- `src/config/`: configuración de entorno y tema

## Licencias

- Proyecto: MIT ([LICENSE](LICENSE))
- Dependencias de terceros: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)

## Atribución

- La organización de UI y scripts toma inspiración estructural de RegressionLab:
  https://github.com/DOKOS-TAYOS/RegressionLab

## Descargo

TransTools no sustituye atención sanitaria profesional y no emite diagnóstico clínico.
