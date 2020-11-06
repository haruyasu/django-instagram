from django.urls import path
from app import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('hash/', views.HashView.as_view(), name='hash'),
]
