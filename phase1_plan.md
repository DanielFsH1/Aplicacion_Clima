# Fase 1 – Investigación, Arquitectura y Estrategia de Datos para **Atmosfera‑Web**

## Selección de APIs

| API | Datos principales | Características clave | Motivo de selección |
| --- | --- | --- | --- |
| **OpenWeatherMap – One Call API 3.0** | Clima actual, pronósticos minuto a minuto, horarios (48 h) y diarios (8 días) y alertas gubernamentales | La API One Call 3.0 proporciona cinco tipos de datos: clima actual y pronóstico (minuto, horario y diario), archivos históricos y proyecciones de 46 años, agregación diaria para 1,5 años y un resumen de clima legible para humanos【811625734659925†L96-L110】. Las llamadas se realizan con `https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude={part}&appid={API key}` y permiten configurar unidades de medida y excluir secciones que no se requieran【811625734659925†L154-L184】. | Fuente principal de información meteorológica por su amplitud y precisión; actualiza los datos cada 10 minutos【811625734659925†L112-L116】. |
| **OpenWeatherMap – Geocoding API** | Geocodificación directa y reversa | Permite convertir nombres de ciudades o códigos postales en coordenadas con el formato `http://api.openweathermap.org/geo/1.0/direct?q={ciudad}&limit={limit}&appid={API key}`【456237948775165†L92-L104】 y viceversa para obtener nombres cercanos a partir de latitud/longitud. | Se integra naturalmente con One Call API; simplifica la búsqueda de lugares y evita depender de servicios externos. |
| **OpenWeatherMap – Weather Maps (tiles)** | Capas de mapas de nubes, precipitaciones, presión, temperatura y viento | Las capas se sirven como teselas (`tiles`) mediante `https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png?appid={API key}`【27708556232593†L69-L86】. Capas disponibles: `clouds_new`, `precipitation_new`, `pressure_new`, `wind_new` y `temp_new`【27708556232593†L91-L133】. | Permiten superponer datos meteorológicos en mapas interactivos (Leaflet/Mapbox) sin depender de RainViewer (que limita su API desde agosto de 2025【851846622725527†L21-L39】). |
| **OpenAQ API v3** | Calidad del aire y contaminantes (PM₂.₅, PM₁₀, O₃, NO₂, SO₂, CO, etc.) | La API ofrece datos armonizados de criterios de contaminantes; incluye métodos para filtrar ubicaciones cercanas usando parámetros `coordinates` y `radius` en consultas como `https://api.openaq.org/v3/locations?coordinates=lat,lon&radius=12000&limit=1000`【42793328492332†L190-L226】. Posteriormente se pueden obtener las mediciones más recientes por estación mediante `/v3/locations/{id}/latest`【739631172160907†L165-L207】. | Complementa el pronóstico del tiempo con información sobre calidad del aire; API pública y documentada. |

## Arquitectura del Sistema

```
                                    +------------------------------+
                                    |         Usuarios (Web)       |
                                    +---------------+--------------+
                                                    | HTTPS
                                                    v
                                      +-------------+---------------+
                                      |        Frontend (Next.js)    |
                                      |  - UI responsiva             |
                                      |  - Mapa interactivo Leaflet  |
                                      |  - Gráficos con Chart.js     |
                                      +-------------+---------------+
                                                    | REST/HTTP
                                                    v
                                      +-------------+---------------+
                                      |      API Gateway (FastAPI)   |
                                      |  - Autentica solicitudes     |
                                      |  - Enrutamiento de servicios |
                                      |  - Cache con Redis           |
                                      +------+------+---------------+
                                             |      | (async calls)
                                             |      v
                       +---------------------+      +-----------------------------+
                       |  User Service (FastAPI)    | Data Ingestion Service      |
                       |  - Gestiona usuarios       |  (FastAPI + APScheduler)    |
                       |  - Ciudades favoritas      |  - Jobs programados:        |
                       |  - Preferencias            |    • One Call cada 10 min    |
                       +---------------------+      |    • Calidad aire cada hora |
                                                    |  - Normalización/ETL        |
                                                    +--------------+-------------+
                                                                   |
                                                                   v
                                                   +---------------+--------------+
                                                   |      PostgreSQL + PostGIS      |
                                                   |  - Tablas para ubicaciones     |
                                                   |  - Datos actuales y pronósticos|
                                                   |  - Calidad del aire           |
                                                   |  - Usuarios y favoritos       |
                                                   +-------------------------------+
```

### Descripción de los componentes

1. **Frontend (Next.js/React)** – Se construirá con Next.js para aprovechar el renderizado híbrido. Integrará:
   - **Barra de búsqueda inteligente:** usa la Geocoding API para sugerir ciudades.
   - **Mapa interactivo (Leaflet):** superpone capas de OWM (`clouds_new`, `precipitation_new`, etc.) mediante teselas【27708556232593†L69-L133】. Permite hacer clic para obtener el clima de cualquier coordenada.
   - **Gráficos (Chart.js/D3.js):** muestran series temporales de temperatura, precipitación y viento para 48 horas y 7 días.
   - **Módulos de datos adicionales:** tarjetas para fases lunares, índice UV, humedad, presión, visibilidad, amanecer/atardecer.
   - **Fondos animados dinámicos:** cambian según el estado del tiempo (sol, nubes, lluvia) y la hora del día.
   - **Gestión de favoritos:** listas de ciudades almacenadas localmente (o en BBDD si hay login).

2. **API Gateway (FastAPI)** – Proporciona endpoints RESTful bien documentados:
   - **`GET /api/search?q=...`** – Devuelve coincidencias de ciudades usando la Geocoding API.
   - **`GET /api/weather?lat=...&lon=...`** – Combina datos actuales, pronóstico horario/diario y alertas de One Call API (minuto, hora y día)【811625734659925†L154-L204】, así como calidad del aire desde OpenAQ.
   - **`GET /api/map-layer?type={clouds|precipitation|wind|temp}&z={z}&x={x}&y={y}`** – Proxy seguro a las teselas de OWM.
   - **`POST /api/favorites` y `GET /api/favorites`** – Gestionan favoritos del usuario.
   - Implementa **caché con Redis** para respuestas frecuentes y evita exceder límites de solicitudes.

3. **User Service** – Maneja autenticación y datos de usuario: registro/login (JWT), ajustes de unidades (métrico/imperial) y persistencia de favoritos. Permite almacenamiento seguro en PostgreSQL y consulta desde el API Gateway.

4. **Data Ingestion Service** – Programa tareas con **APScheduler** para actualizar la base de datos:
   - **Clima:** Llama a la One Call API cada 10 min para las ubicaciones más consultadas, obteniendo clima actual, pronóstico horario (48 h) y diario (8 días)【811625734659925†L96-L104】.
   - **Calidad del aire:** Usa OpenAQ para encontrar estaciones cercanas (`/locations?coordinates=lat,lon&radius=...`【42793328492332†L190-L226】) y luego recupera las mediciones más recientes por estación (`/locations/{id}/latest`【739631172160907†L165-L207】). Normaliza los valores de PM₂.₅, PM₁₀, O₃, NO₂ y SO₂.
   - **Almacenamiento:** Inserta/actualiza registros en las tablas correspondientes de PostgreSQL.
   - Maneja errores, reintentos y control de tasa para no superar los límites de cada API.

5. **Base de datos (PostgreSQL + PostGIS)** – Se definirá un esquema relacional normalizado:

| Tabla | Campos relevantes | Descripción |
| --- | --- | --- |
| `locations` | `id (PK)`, `name`, `country`, `lat`, `lon`, `slug` | Ciudades/ubicaciones soportadas; con índice espacial (PostGIS) para búsquedas rápidas. |
| `current_weather` | `id (PK)`, `location_id (FK)`, `timestamp`, `temp`, `feels_like`, `pressure`, `humidity`, `dew_point`, `uvi`, `clouds`, `visibility`, `wind_speed`, `wind_deg`, `wind_gust`, `weather_main`, `weather_description` | Datos actuales de cada ubicación según One Call (campo `current`【811625734659925†L212-L237】). |
| `hourly_forecast` | `id (PK)`, `location_id (FK)`, `forecast_time`, `temp`, `feels_like`, `pressure`, `humidity`, `dew_point`, `uvi`, `clouds`, `visibility`, `wind_speed`, `wind_deg`, `wind_gust`, `pop`, `weather_main`, `weather_description` | Pronóstico horario hasta 48 horas【811625734659925†L245-L268】. |
| `daily_forecast` | `id (PK)`, `location_id (FK)`, `date`, `sunrise`, `sunset`, `moonrise`, `moonset`, `moon_phase`, `temp_min`, `temp_max`, `temp_day`, `temp_night`, `pressure`, `humidity`, `wind_speed`, `wind_deg`, `wind_gust`, `clouds`, `pop`, `rain`, `uvi`, `summary` | Pronóstico diario de 8 días【811625734659925†L271-L312】. |
| `weather_alerts` | `id (PK)`, `location_id (FK)`, `sender_name`, `event`, `start`, `end`, `description` | Alertas gubernamentales que devuelve One Call【811625734659925†L315-L327】. |
| `air_quality` | `id (PK)`, `location_id (FK)`, `pollutant`, `value`, `unit`, `timestamp`, `source_station_id` | Últimas mediciones de contaminantes por ubicación, obtenidas de OpenAQ (PM₂.₅, PM₁₀, O₃, NO₂, SO₂). |
| `users` | `id (PK)`, `username`, `email`, `password_hash`, `preferences_json` | Información del usuario para autenticación y configuración. |
| `favorites` | `user_id (FK)`, `location_id (FK)` | Relación muchos‑a‑muchos entre usuarios y ubicaciones favoritas. |

### Estrategia de Cache

- **Redis** se empleará como capa de cache para consultas comunes (e.g. clima actual de ciudades populares). También almacena resultados de geocodificación y calidad del aire para reducir llamadas externas.
- TTL configurado según la caducidad de cada dato: 10 min para clima actual, 1 h para pronósticos horarios y calidad del aire.

## Estrategia DevOps

- **Docker y Docker Compose:** cada servicio (frontend, API Gateway, User Service, Data Ingestion, base de datos) se empaqueta en un contenedor independiente. Un `docker-compose.yml` facilitará el entorno de desarrollo local.
- **CI/CD con GitHub Actions:** flujos que ejecutan linting (Flake8, ESLint), pruebas unitarias (Pytest/Jest) con cobertura mínima del 80 %, construyen imágenes Docker y publican en GHCR. Las credenciales y claves API se almacenarán como secretos de GitHub.
- **Despliegue cloud:** propondremos Vercel para el frontend (Next.js) y Railway o Render para los servicios backend y PostgreSQL, debido a sus planes gratuitos y facilidad de integración.

## Siguientes Pasos

1. **Crear el repositorio inicial** con la estructura básica (`backend`, `ingestion`, `frontend`, `db`, `docker-compose.yml`). Añadir un README provisional con el diagrama de arquitectura (mermaid) y la descripción del plan de desarrollo.
2. **Configurar la base de datos** (Docker) e implementar un esquema inicial usando SQLAlchemy.
3. **Desarrollar el API Gateway** con FastAPI, incluyendo endpoints `/api/search` y `/api/weather` conectados a la Geocoding API y a One Call API. Implementar caching con Redis.
4. **Construir el servicio de ingesta**: tareas programadas para One Call y OpenAQ. Crear scripts de normalización y almacenamiento en la base de datos.
5. **Diseñar la interfaz de usuario** en Next.js con componentes de mapa, gráficos y tarjetas informativas.
6. **Configurar la integración continua** y preparar el despliegue inicial.

Este plan inicial proporciona una base sólida para construir Atmosfera‑Web como una aplicación de pronóstico del tiempo de clase mundial, combinando fuentes de datos fiables (OpenWeatherMap y OpenAQ) con una arquitectura moderna y escalable.
