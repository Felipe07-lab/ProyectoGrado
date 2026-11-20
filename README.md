# Sistema web para la gestión de inventario y ventas en tiendas de barrio

**Proyecto de Grado — UNAD — Ingeniería de Sistemas (202016907)**
**Autores:** Andrés Felipe Velandia Naranjo, Andrés Felipe Pérez Pérez

Prototipo funcional (Fase 4 — nivel de madurez tecnológica TRL5) del sistema de información
web para la gestión de inventario y ventas dirigido a tiendas de barrio de la localidad de
Suba, Bogotá.

## Funcionalidades

- Registro e inicio de sesión de tenderos.
- Gestión de productos (CRUD): nombre, categoría, precio de compra/venta, stock, stock mínimo,
  fecha de vencimiento.
- Registro de ventas con descuento automático de inventario.
- Alertas automáticas de stock mínimo y de productos próximos a vencer.
- Reportes de ventas por periodo (hoy / 7 días / 30 días) y de rotación de productos.

## Stack tecnológico

- Backend: Python 3 + Flask + Flask-SQLAlchemy
- Base de datos: SQLite (desarrollo) — migrable a PostgreSQL en producción
- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript
- Control de versiones: Git / GitHub

## Instalación y ejecución local

```bash
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La aplicación quedará disponible en `http://127.0.0.1:5000`.

Al ejecutarse por primera vez, se crea automáticamente una cuenta de demostración:

- **Usuario:** `demo`
- **Contraseña:** `demo1234`

con productos de ejemplo precargados para poder probar el sistema de inmediato.

## Estructura del proyecto

```
tienda-suba/
├── app.py              # Rutas y lógica de la aplicación (controlador)
├── models.py           # Modelos de datos (Tendero, Producto, Venta, DetalleVenta)
├── requirements.txt
├── templates/          # Vistas HTML (Jinja2)
└── static/vendor/      # Bootstrap (CSS/JS) servido localmente
```

## Nivel de madurez tecnológica (TRL)

Este prototipo corresponde a un **TRL5**: validación de los componentes del sistema en un
entorno relevante (pruebas con tenderos reales), de acuerdo con la escala de Colciencias (2018)
referenciada en el documento maestro del proyecto.

## Documentación completa

El documento maestro del proyecto (planteamiento del problema, marco teórico/conceptual/
jurídico/tecnológico, metodología de investigación y de desarrollo ágil, diagramas de
arquitectura, modelo entidad-relación, casos de uso y cronograma) se entrega junto al presente
repositorio como anexo de la Fase 4 del curso Proyecto de Grado.
