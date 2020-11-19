from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='stocks-home'),
    path('about/', views.about, name='stocks-about'),
    path('dashboard/', views.dashboard, name='stocks-dashboard'),
    path('ltp_update/', views.ltp_update, name='ltp-update'),
]
