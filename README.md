# PostAuth - API de Productos con Token Temporal

Este proyecto es una aplicación Django que expone una API de productos. La API permite listar, crear, actualizar y eliminar productos, pero solo permite operaciones de escritura (`POST`, `PUT`, `DELETE`) si se envía un token temporal válido en los headers.

La aplicación también incluye una página web de registro de usuario (`/signup/`) para crear un usuario, mostrar una página de éxito y luego permitir la obtención de un token mediante credenciales.

---

## Concepto

- El usuario se registra en la web de `signup` con nombre de usuario y contraseña.
- Tras el registro exitoso, la app muestra una página de confirmación.
- El usuario realiza una petición `POST /signup/token/` con su `username` y `password` para recibir un token temporal.
- El token se usa en las cabeceras de autorización para las peticiones `POST`, `PUT` y `DELETE` de la API de productos.

---

## Rutas principales

### Registro de usuario

- `GET /signup/`
  - Muestra el formulario de registro.
- `POST /signup/`
  - Registra un usuario nuevo.
  - Requiere campos:
    - `username`
    - `password`
  - Retorna la página de éxito si el registro es válido.

### Token temporal

- `POST /signup/token/`
  - Devuelve un token temporal para hojas de petición.
  - Se usa para autenticar las operaciones de escritura en la API de productos.
  - Cuerpo JSON requerido:
    - `username`
    - `password`
  - Respuesta de éxito:
    - `token`
    - `expires_at`

### API de productos

- `GET /productos/`
  - Lista todos los productos. No requiere autenticación.

- `POST /productos/`
  - Crea un producto nuevo. Requiere token en header `Authorization: Token <token>`.

- `GET /productos/<id>/`
  - Devuelve los datos de un producto por su ID. No requiere autenticación.

- `PUT /productos/<id>/`
  - Actualiza un producto existente. Requiere token.

- `DELETE /productos/<id>/`
  - Elimina el producto. Requiere token.

---

## Validaciones y reglas de negocio

### Validaciones básicas

- Campos obligatorios: `nombre`, `sku`, `descripción`, `precio`, `stock`, `categoría`.
- Tipos de datos esperados.
- Longitud mínima para algunos campos.

### Reglas de negocio

- `sku` debe ser único.
- `precio` debe ser mayor que `0`.
- `stock` no puede ser negativo.
- No se permite duplicar `nombre` dentro de la misma `categoría`.
- En `POST` y `PUT`, la `descripción` no puede contener un número de 10 dígitos o más.

---

## Autenticación

Las operaciones de escritura en la API de productos requieren el token temporal, enviado en el header `Authorization` con el prefijo `Token `.

Ejemplo:

```http
Authorization: Token abc123def456...
```

---

## Ejemplos con cURL

### 1. Registrar usuario

```bash
curl -X POST "http://localhost:8000/signup/" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=miusuario" \
  -d "password=miclave123"
```

### 2. Obtener token temporal

```bash
curl -X POST "http://localhost:8000/signup/token/" \
  -H "Content-Type: application/json" \
  -d '{"username": "miusuario", "password": "miclave123"}'
```

Respuesta de ejemplo:

```json
{
  "token": "Z0hGdF8...",
  "expires_at": "2026-05-29T12:34:56.789012"
}
```

### 3. Listar productos

```bash
curl -X GET "http://localhost:8000/productos/"
```

### 4. Crear un producto

```bash
curl -X POST "http://localhost:8000/productos/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token Z0hGdF8..." \
  -d '{
    "nombre": "Zapatos",
    "sku": "ZAP-123",
    "descripción": "Zapatos deportivos cómodos",
    "precio": 59.99,
    "stock": 20,
    "categoría": "Calzado"
  }'
```

### 5. Actualizar un producto

```bash
curl -X PUT "http://localhost:8000/productos/1/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token Z0hGdF8..." \
  -d '{
    "nombre": "Zapatos deportivos",
    "sku": "ZAP-123",
    "descripción": "Zapatos cómodos para correr",
    "precio": 64.99,
    "stock": 18,
    "categoría": "Calzado"
  }'
```

### 6. Eliminar un producto

```bash
curl -X DELETE "http://localhost:8000/productos/1/" \
  -H "Authorization: Token Z0hGdF8..."
```

---

## Errores comunes

### Errores de validación

- `400 Bad Request` con detalles de `errors` si faltan campos o no cumplen las reglas.
- Ejemplo:

```json
{
  "errors": {
    "sku": "SKU ya existe.",
    "precio": "El precio debe ser mayor que 0."
  }
}
```

### Error de autenticación

- `401 Unauthorized` cuando falta el token o es inválido/expirado.
- Ejemplo:

```json
{ "detail": "Token inválido." }
```

### Recurso no encontrado

- `404 Not Found` cuando el producto no existe.
- Ejemplo:

```json
{ "detail": "Producto no encontrado." }
```

### Método no permitido

- `405 Method not allowed.` si se usa un verbo HTTP no soportado.

---

## Instrucciones de ejecución

1. Instala dependencias y activa el entorno virtual.
2. Ejecuta las migraciones.
3. Levanta el servidor con:

```bash
cd post_auth
../.venv/bin/python manage.py runserver
```

4. Accede a:

- `http://localhost:8000/signup/` para registrar usuario.
- `http://localhost:8000/productos/` para consumir la API.

---

## Notas

- El token temporal expira en 1 hora.
- La vista de registro usa Bootstrap 5 para el formulario y los mensajes.
- El endpoint de token está exento de CSRF para facilitar llamadas desde `curl` o clientes externos.
