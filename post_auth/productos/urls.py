from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista, name='lista'),
    path('<int:pid>/', views.por_id, name='pid')
]
