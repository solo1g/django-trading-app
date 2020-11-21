from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='stocks-home'),
    path('about/', views.about, name='stocks-about'),
    path('dashboard/', views.dashboard, name='stocks-dashboard'),
    path('ltp_update/', views.ltp_update, name='ltp-update'),
    path('transact/', views.transact, name='transact'),
    path('chart_query/', views.chart_query, name='chart-query'),
    path('account_value/', views.account_value, name='account-value'),
    path('add_money/', views.add_money, name='add-money'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('transactions/', views.transactions, name='transactions'),
]
