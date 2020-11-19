from django.shortcuts import render
from django.http import JsonResponse
from random import uniform
from django.contrib.auth.decorators import login_required
from .models import *


def home(request):
    return render(request, 'stocks/home.html')


def about(request):
    return render(request, 'stocks/about.html')


@login_required
def dashboard(request):
    stocks = []
    for stock in Stock.objects.all():
        stocks.append(stock)
    context = {
        'stocks': stocks
    }
    print(context['stocks'])
    return render(request, 'stocks/dashboard.html', context)


@login_required
def dashboard(request):
    stocks = Stock.objects.order_by("name")
    return render(request, "stocks/dashboard.html", {"stocks": stocks})


@login_required
def ltp_update(request):
    for stock in Stock.objects.all():
        new_ltp = round(
            (stock.ltp) * (uniform(stock.variance_lower_bound, stock.variance_upper_bound)), 2)
        new_stock_price = StockPrice.objects.create(
            stock=stock, price=new_ltp)
        new_stock_price.save()
        setattr(stock, 'ltp', new_ltp)
        stock.save()
    for user in User.objects.all():
        total = 0.0
        for item in user.portfolio_set.all():
            total += item.quantity*item.stock.ltp
        new_account_value = AccountValue.objects.create(
            user=user, value=round(total, 2))
        new_account_value.save()
    json_data = {}
    for stock in Stock.objects.order_by("name"):
        json_data[stock.name] = stock.ltp
    # json_data['account_value'] = request.user.accountvalue_set.all().order_by(
    #     '-time').first().value
    return JsonResponse(json_data)


@login_required
def transact(request):
    if request.method == "POST":
        stock_chosen = Stock.objects.get(name=request.POST.get('dropdown'))
        quantity = int(request.POST.get('quantity'))
        user = request.user
        ac_value = request.user.accountvalue_set.all().order_by('-time').first().value
        if quantity > 0:
            if request.POST.get('button') == "buy":
                if stock_chosen.ltp*quantity <= ac_value:
                    Transaction.objects.create(
                        user=user, stock=stock_chosen, units=quantity, price_each=stock_chosen.ltp, transaction='buy').save()
                # only update portfolio account value would be automatically updated
                try:
                    stock_in_portfolio = user.portfolio_set.get(
                        stock=stock_chosen)
                    stock_in_portfolio.quantity += quantity
                    stock_in_portfolio.save()
                except portfolio.DoesNotExist:
                    user.portfolio_set.create(
                        stock=stock_chosen, quantity=quantity).save()
            elif request.POST.get('button') == "sell":
                if user.portfolio_set.get(stock=stock_chosen).exists() and user.portfolio_set.get(stock=stock_chosen).quantity < quantity:
                    Transaction.objects.create(
                        user=user, stock=stock_chosen, units=quantity, price_each=stock_chosen.ltp, transaction='sell').save()
                    stock_in_portfolio = user.portfolio_set.get(
                        stock=stock_chosen)
                    stock_in_portfolio.quantity -= quantity
                    stock_in_portfolio.save()
