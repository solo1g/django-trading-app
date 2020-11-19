from django.contrib import admin
from .models import *

admin.site.register(StockPrice)
admin.site.register(Transaction)
admin.site.register(Stock)
admin.site.register(AccountValue)
admin.site.register(Portfolio)
