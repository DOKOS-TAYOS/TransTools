# TransTools

TransTools es una aplicacion de escritorio hecha con Python y Tkinter para llevar un seguimiento local, privado y practico durante la transicion. Reune en una sola app registros cotidianos, recordatorios basicos, un pequeno centro de acompanamiento personal y exportes locales.

La idea del proyecto es sencilla: que una persona pueda guardar informacion util para su proceso sin depender de una cuenta online, sin subir audios a servicios externos y sin tener que repartirse entre varias herramientas pequenas.

## Que es hoy la aplicacion

TransTools esta orientada a uso personal y offline. Su intencion actual no es ser una plataforma clinica ni una red social, sino una herramienta local de apoyo y organizacion.

Hoy cubre estas areas:

- registro de voz con analisis local
- registro de medicacion
- registro de visitas y eventos libres
- diario de habitos adaptativo
- panel de acompanamiento con hoja de ruta, citas y bienestar
- vista unificada de datos con calendario, resumen diario y grafica semanal
- exportes locales
- directorio de contactos de apoyo
- configuracion basica de la app y transferencia completa del perfil local

## Funcionalidades actuales

### 1. Onboarding inicial

En el primer arranque la app abre un onboarding obligatorio de 3 pasos. Ahi se puede guardar:

- nombre de pila
- proxima medicacion
- frecuencia de medicacion
- dosis habitual
- proxima consulta medica
- proxima consulta de psicologia o especialista

Si se cierra ese onboarding sin completarlo, la aplicacion tambien se cierra. La intencion es que el perfil local quede inicializado desde el principio.

### 2. Registros diarios

Salvo la grabacion de voz, los demas registros trabajan con la fecha que elijas en la interfaz.

#### Registro de voz

- Graba desde el microfono del equipo.
- Analiza el audio localmente.
- Guarda energia y metricas automaticas de estado de animo.
- Cifra localmente las metricas sensibles de tono.
- Puede guardar el WAV si asi se configura o se marca en esa grabacion.

Importante: en la interfaz actual la grabacion de voz se registra siempre para el dia de hoy.

#### Registro de medicacion

- fecha
- hora opcional
- dosis opcional
- notas opcionales
- proxima fecha opcional
- check-in de bienestar opcional en el mismo guardado

Ademas, al arrancar la app puede avisar si una toma toca hoy o si ya hay tomas atrasadas.

#### Otros registros

Hay dos bloques dentro del mismo dialogo:

- visitas medicas o de psicologia, con proxima cita opcional
- eventos o notas libres con categoria y etiquetas

Las visitas tambien pueden guardar un check-in de bienestar en el mismo paso.

#### Diario de habitos adaptativo

- La lista sugerida cambia segun el ritmo reciente de cumplimiento.
- La app muestra entre 3 y 8 habitos.
- El catalogo base esta pensado para ser ligero y de baja friccion.
- El progreso se guarda por fecha.

### 3. Mi acompanamiento

El modulo `Mi acompanamiento` es el centro mas orientado a seguimiento personal. Tiene cuatro pestanas:

- `Panel`: muestra siguiente accion sugerida, avisos, citas proximas y resumen semanal.
- `Hoja de ruta`: pasos editables por categorias como salud, voz, documentacion, entorno social, imagen y expresion, cirugias/recuperacion y bienestar.
- `Citas`: preparacion de citas con preguntas, temas a comentar, siguiente paso y notas posteriores.
- `Bienestar`: check-ins con animo, energia, sueno y notas.

Tambien permite cambiar la etapa del proceso entre:

- `Transicion activa`
- `Post-transicion`

Ese cambio ajusta la prioridad de algunos elementos mostrados en el panel.

### 4. Ver mis datos

La vista `Ver mis datos` reune lo mas util para revisar el historial sin ir modulo por modulo:

- pestana de informacion del usuario y salud
- calendario con marcas de actividad
- resumen diario no sensible
- grafica semanal de voz
- pestana de proceso con hoja de ruta y citas
- pestana de bienestar con los ultimos check-ins

La vista diaria no ensena tono de voz detallado. Ese dato se reserva para agregados semanales.

### 5. Exportes locales

Desde `Ver mis datos` se pueden exportar rangos de fechas a:

- `CSV`: resumen diario
- `XLSX`: tablas completas de exportacion
- `PDF`: informe compacto semanal
- `PNG`: grafica semanal de voz

La exportacion respeta la politica de privacidad de la aplicacion: el tono no sale como detalle diario.

### 6. Recursos y configuracion

#### Contactos

La app incluye un directorio de apoyo con:

- contactos nacionales
- contactos por comunidad autonoma

El dataset actual esta claramente orientado a Espana. Desde la tabla puede abrirse la web de un contacto con doble clic cuando existe.

#### Configuracion

Desde `Configuracion` se pueden cambiar:

- idioma (`es` o `en`)
- carpeta de datos
- guardado de audio por defecto
- duracion de grabacion
- nivel de log
- logs en consola
- modo visual (`dark` o `light`)
- tamano global de fuente

Tambien permite:

- exportar el perfil local completo
- importar un perfil exportado
- borrar el perfil local completo

El borrado completo pide escribir `BORRAR` como confirmacion explicita.

## Privacidad y tratamiento de datos

Este es uno de los puntos mas importantes del proyecto.

- La app funciona sin conexion.
- No necesita cuenta de usuario.
- No usa servicios en la nube para analizar la voz.
- Las metricas sensibles de tono se cifran con una clave local.
- La vista diaria y el CSV no exponen tono detallado.
- Las tendencias semanales de voz solo se muestran si esa semana tiene muestras en al menos dos dias distintos.

La exportacion e importacion de perfil no solo mueven los JSON: tambien incluyen la clave local de cifrado para que los registros antiguos sigan siendo legibles en la misma instalacion importada.

## Donde se guardan los datos

Por defecto, TransTools usa una carpeta de usuario del sistema.

- Windows: `%APPDATA%\TransTools`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/transtools`

Si `FILE_OUTPUT_DIR` esta vacio o vale `output`, la app usa esas rutas por usuario. Ese valor `output` ya no significa "guardar dentro del repo", sino "usar la ubicacion por defecto de la plataforma".

Si quieres una carpeta personalizada, define `FILE_OUTPUT_DIR` en `.env`.

Dentro de la carpeta de datos, los ficheros principales son:

- `patient_profile.json`: perfil, configuracion de salud, catalogo de habitos y metadatos
- `patient_history.json`: historial de voz, medicacion, visitas, eventos, habitos, hoja de ruta, citas y bienestar
- `.voice_metrics.key`: clave local de cifrado de voz
- `audio/`: audios WAV guardados, si existe

Si vienes de una version antigua que guardaba en `output/` dentro del proyecto, la app intenta migrar esos ficheros automaticamente al nuevo directorio de usuario.

## Instalacion y arranque

### Requisitos

- Python 3.12 o superior
- Windows 10/11 o una distribucion Linux con Tk disponible

### Opcion recomendada: scripts del repo

#### Windows

```bat
setup.bat
bin\run.bat
```

Notas:

- `setup.bat` crea o reutiliza `.venv`, instala dependencias y prepara `.env` sin depender de activar el entorno en la terminal.
- En Windows tambien intenta crear un acceso directo en el escritorio.
- `bin\run.bat --check` valida la instalacion sin abrir la app.
- Si quieres un flujo de clonado + preparacion en un solo paso, tambien existe `install.bat`.

#### Linux

```bash
chmod +x setup.sh bin/run.sh
./setup.sh
./bin/run.sh
```

Tambien existe `install.sh` para un flujo de clonado + preparacion.
Si solo quieres validar el entorno antes de abrir la app, usa `./bin/run.sh --check`.

### Opcion manual

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python src\main.py
```

#### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python src/main.py
```

TransTools esta pensado para ejecutarse siempre dentro de `.venv`.

### Comprobaciones de desarrollo

Si vas a trabajar sobre el codigo del repo, puedes dejar la misma caja de herramientas que usa CI dentro de tu `.venv`.

#### Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
ruff check .
pip-audit
pyright
pytest -q
```

#### Linux

```bash
source .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pip-audit
pyright
pytest -q
```

## Configuracion rapida (.env)

Variables mas importantes:

| Variable | Que controla | Valor por defecto |
| --- | --- | --- |
| `LANGUAGE` | Idioma de interfaz (`es`, `en`) | `es` |
| `UI_THEME_MODE` | Modo visual (`dark`, `light`) | `dark` |
| `UI_FONT_SIZE` | Tamano global del texto | `16` |
| `FILE_OUTPUT_DIR` | Carpeta de datos; `output` significa "ruta por usuario" | `output` |
| `SAVE_AUDIO` | Guardar audio por defecto | `false` |
| `RECORD_DURATION_SEC` | Duracion de grabacion | `5` |
| `LOG_LEVEL` | Nivel de detalle del log | `INFO` |
| `LOG_FILE` | Fichero de log | `transtools.log` |
| `LOG_CONSOLE` | Tambien mostrar logs en consola | `true` |

La configuracion tambien se puede cambiar desde la propia interfaz. Cuando se guarda desde la app, TransTools se reinicia para aplicar cambios.

## Flujo de uso recomendado

Una forma simple de entender la app es esta:

1. Completar el onboarding.
2. Registrar voz, medicacion, visitas o eventos segun haga falta.
3. Revisar `Mi acompanamiento` para saber que toca ahora.
4. Usar `Ver mis datos` para consultar calendario, resumen diario y evolucion semanal.
5. Exportar un rango de fechas si necesitas compartir o revisar informacion fuera de la app.

## Limites actuales

Conviene dejarlo claro:

- no es una historia clinica
- no sustituye atencion profesional
- no sincroniza entre dispositivos
- no trabaja con cuentas multiusuario
- no sube datos automaticamente a ningun servicio
- el directorio de contactos esta enfocado a recursos de Espana

## Estructura del repo

- `src/`: codigo principal de la aplicacion
- `src/frontend/`: interfaz Tkinter
- `src/core/`: logica de negocio, repositorio, privacidad y exportes
- `src/audio/`: grabacion y analisis
- `src/config/`: entorno, rutas y tema
- `src/locales/`: textos en espanol e ingles
- `src/data/contacts.json`: contactos de apoyo incluidos en la app
- `tests/`: pruebas automatizadas
- `docs/`: documentacion Sphinx
- `images/`: recursos graficos

## Licencias

- Proyecto: MIT ([LICENSE](LICENSE)); avisos y provenance: [NOTICE](NOTICE)
- Dependencias de terceros: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)
- Citacion (opcional): [CITATION.cff](CITATION.cff)

## Nota importante

TransTools es una herramienta de apoyo personal. No sustituye evaluacion, seguimiento ni tratamiento sanitario profesional.
