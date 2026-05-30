import json
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate, get_user_model
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Token

User = get_user_model()


def register(request: HttpRequest):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        errors = {}

        if not username:
            errors['username'] = 'El nombre de usuario es obligatorio.'
        elif len(username) < 3:
            errors['username'] = 'El nombre de usuario debe tener al menos 3 caracteres.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'Este usuario ya existe.'

        if not password:
            errors['password'] = 'La contraseña es obligatoria.'
        elif len(password) < 6:
            errors['password'] = 'La contraseña debe tener al menos 6 caracteres.'

        if errors:
            return render(request, 'signup.html', {'errors': errors, 'username': username})

        User.objects.create_user(username=username, password=password)
        return render(request, 'success.html', {'username': username})

    return render(request, 'signup.html')


def success(request: HttpRequest):
    return render(request, 'success.html')


@csrf_exempt
def obtain_token(request: HttpRequest) -> JsonResponse:
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'JSON inválido.'}, status=400)

    username = str(data.get('username', '')).strip()
    password = str(data.get('password', ''))

    if not username or not password:
        return JsonResponse({'detail': 'Nombre de usuario y contraseña son obligatorios.'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'detail': 'Credenciales inválidas.'}, status=401)

    token_value = secrets.token_urlsafe(32)
    expires_at = timezone.now() + timedelta(hours=1)
    Token.objects.update_or_create(
        user=user,
        defaults={
            'token': token_value,
            'expires_at': expires_at,
        },
    )

    return JsonResponse({
        'token': token_value,
        'expires_at': expires_at.isoformat(),
    })
