from django.urls import path
from . import views

urlpatterns = [
    path('', views.register, name='signup'),
    path('success/', views.success, name='signup_success'),
    path('token/', views.obtain_token, name='obtain_token'),
]
