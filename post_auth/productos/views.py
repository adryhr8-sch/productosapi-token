import json
import re
from decimal import Decimal, InvalidOperation

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from signup.models import Token
from .models import Producto

TOKEN_HEADER_PREFIX = 'Token '


def _get_token_value(request: HttpRequest) -> str | None:
    auth = request.headers.get('Authorization', '')
    if auth.startswith(TOKEN_HEADER_PREFIX):
        return auth[len(TOKEN_HEADER_PREFIX):].strip()
    return None


def _authenticate_token(request: HttpRequest):
    token_value = _get_token_value(request)
    if not token_value:
        return None, JsonResponse({'detail': 'Token faltante o inválido.'}, status=401)

    try:
        token = Token.objects.get(token=token_value)
    except Token.DoesNotExist:
        return None, JsonResponse({'detail': 'Token inválido.'}, status=401)

    if token.expires_at <= timezone.now():
        return None, JsonResponse({'detail': 'Token expirado.'}, status=401)

    return token.user, None


def _build_producto_response(producto: Producto) -> dict:
    return {
        'id': producto.id,
        'nombre': producto.nombre,
        'sku': producto.sku,
        'descripción': producto.descripción,
        'precio': str(producto.precio),
        'stock': producto.stock,
        'categoría': producto.categoría,
    }


def _validate_producto_payload(data: dict, product_id: int | None = None) -> tuple[dict, dict]:
    errors = {}
    cleaned = {}

    required_fields = ['nombre', 'sku', 'descripción', 'precio', 'stock', 'categoría']
    for field in required_fields:
        if field not in data:
            errors[field] = 'Este campo es obligatorio.'

    if errors:
        return errors, cleaned

    nombre = data['nombre']
    sku = data['sku']
    descripción = data['descripción']
    categoría = data['categoría']

    if not isinstance(nombre, str) or not nombre.strip():
        errors['nombre'] = 'Nombre debe ser texto y no puede estar vacío.'
    elif len(nombre.strip()) < 3:
        errors['nombre'] = 'Nombre debe tener al menos 3 caracteres.'

    if not isinstance(sku, str) or not sku.strip():
        errors['sku'] = 'SKU debe ser texto y no puede estar vacío.'
    elif len(sku.strip()) < 3:
        errors['sku'] = 'SKU debe tener al menos 3 caracteres.'
    elif Producto.objects.filter(sku__iexact=sku.strip()).exclude(pk=product_id).exists():
        errors['sku'] = 'SKU ya existe.'

    if not isinstance(descripción, str) or not descripción.strip():
        errors['descripción'] = 'Descripción debe ser texto y no puede estar vacía.'
    elif len(descripción.strip()) < 10:
        errors['descripción'] = 'Descripción debe tener al menos 10 caracteres.'
    elif re.search(r'\d{10,}', descripción):
        errors['descripción'] = 'La descripción no puede contener números de 10 dígitos o más.'

    if not isinstance(categoría, str) or not categoría.strip():
        errors['categoría'] = 'Categoría debe ser texto y no puede estar vacía.'
    elif len(categoría.strip()) < 3:
        errors['categoría'] = 'Categoría debe tener al menos 3 caracteres.'

    if not errors.get('nombre') and not errors.get('categoría'):
        if Producto.objects.filter(nombre__iexact=nombre.strip(), categoría__iexact=categoría.strip()).exclude(pk=product_id).exists():
            errors['nombre'] = 'Ya existe un producto con este nombre en la misma categoría.'

    precio = data['precio']
    try:
        precio_decimal = Decimal(str(precio))
        if precio_decimal <= 0:
            errors['precio'] = 'El precio debe ser mayor que 0.'
    except (InvalidOperation, TypeError, ValueError):
        errors['precio'] = 'Precio debe ser un número válido.'

    stock = data['stock']
    try:
        stock_int = int(stock)
        if stock_int < 0:
            errors['stock'] = 'Stock no puede ser negativo.'
    except (TypeError, ValueError):
        errors['stock'] = 'Stock debe ser un número entero válido.'

    if errors:
        return errors, cleaned
    
    cleaned = {
        'nombre': nombre.strip(),
        'sku': sku.strip(),
        'descripción': descripción.strip(),
        'categoría': categoría.strip(),
        'precio': precio_decimal,
        'stock': stock_int,
    }

    return errors, cleaned


@csrf_exempt
def lista(request: HttpRequest) -> JsonResponse:
    if request.method == 'GET':
        productos = [
            _build_producto_response(p)
            for p in Producto.objects.all()
        ]
        return JsonResponse(productos, safe=False)

    if request.method == 'POST':
        _, auth_error = _authenticate_token(request)
        if auth_error is not None:
            return auth_error

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'JSON inválido.'}, status=400)

        errors, valid_data = _validate_producto_payload(payload)
        if errors:
            return JsonResponse({'errors': errors}, status=400)

        producto = Producto.objects.create(**valid_data)
        return JsonResponse(_build_producto_response(producto), status=201)

    return JsonResponse({'detail': 'Method not allowed.'}, status=405)


@csrf_exempt
def por_id(request: HttpRequest, pid: int) -> JsonResponse:
    try:
        producto = Producto.objects.get(pk=pid)
    except Producto.DoesNotExist:
        return JsonResponse({'detail': 'Producto no encontrado.'}, status=404)

    if request.method == 'GET':
        return JsonResponse(_build_producto_response(producto))

    if request.method in ('PUT', 'DELETE'):
        _, auth_error = _authenticate_token(request)
        if auth_error:
            return auth_error

    if request.method == 'PUT':
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'JSON inválido.'}, status=400)

        errors, valid_data = _validate_producto_payload(payload, product_id=producto.pk)
        if errors is not None:
            return JsonResponse({'errors': errors}, status=400)

        for field, value in valid_data.items():
            setattr(producto, field, value)
        producto.save()
        return JsonResponse(_build_producto_response(producto))

    if request.method == 'DELETE':
        producto.delete()
        return JsonResponse({}, status=204)

    return JsonResponse({'detail': 'Method not allowed.'}, status=405)
