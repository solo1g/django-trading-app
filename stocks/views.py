from django.shortcuts import render, HttpResponse
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
        last_value = 0.0
        try:
            last_value = user.accountvalue_set.all().order_by('-time').first().value
        except:
            user.accountvalue_set.create()
            last_value = user.accountvalue_set.all().order_by('-time').first().value
        new_account_value = AccountValue.objects.create(
            user=user, holdings_value=round(total, 2), value=last_value)
        new_account_value.save()
    json_data = {}
    for stock in Stock.objects.order_by("name"):
        json_data[stock.name] = stock.ltp
    return JsonResponse(json_data)


@login_required
def transact(request):
    if request.method == "POST":
        stock_chosen = Stock.objects.get(name=request.POST.get('stock_name'))
        quantity = int(request.POST.get('quantity'))
        user = request.user
        latest_account = request.user.accountvalue_set.all().order_by('-time').first()
        ac_value = latest_account.value
        if quantity > 0:
            if request.POST.get('type') == "buy":
                if stock_chosen.ltp*quantity <= ac_value:
                    Transaction.objects.create(
                        user=user, stock=stock_chosen, units=quantity, price_each=stock_chosen.ltp, transaction='buy').save()
                    # only update portfolio account value would be automatically updated
                    try:
                        print("Try")
                        stock_in_portfolio = user.portfolio_set.get(
                            stock=stock_chosen)
                        stock_in_portfolio.quantity += quantity
                        stock_in_portfolio.save()
                    except:
                        print("Except")
                        user.portfolio_set.create(
                            stock=stock_chosen, quantity=quantity).save()
                    finally:
                        print("Saving new account value")
                        user.accountvalue_set.create(value=(
                            ac_value-stock_chosen.ltp*quantity), holdings_value=latest_account.holdings_value).save()
                        return HttpResponse("Success")
            elif request.POST.get('button') == "sell":
                if user.portfolio_set.get(stock=stock_chosen).exists() and user.portfolio_set.get(stock=stock_chosen).quantity < quantity:
                    Transaction.objects.create(
                        user=user, stock=stock_chosen, units=quantity, price_each=stock_chosen.ltp, transaction='sell').save()
                    stock_in_portfolio = user.portfolio_set.get(
                        stock=stock_chosen)
                    stock_in_portfolio.quantity -= quantity
                    stock_in_portfolio.save()
                    return HttpResponse("Success")
    return HttpResponse("Fail")


@login_required
def chart_query(request):
    if request.method == "POST":
        stock_object = Stock.objects.get(name=request.POST.get('stock_name'))
        series = [price.price for price in StockPrice.objects.filter(
            stock=stock_object).order_by('-time')[:25]][::-1]
        print(series)
        return JsonResponse(
            {
                'series': series,
            }
        )
    return HttpResponse("chart query fail")


@login_required
def account_value(request):
    latest_account = request.user.accountvalue_set.all().order_by('-time')[0]
    current = latest_account.holdings_value
    cash = latest_account.value
    # endure this is the default value for money on new account
    initial = 10000.0
    gain_percent = ((current+cash)/initial-1)*100.0
    return HttpResponse(f'<span>${round(current,2)} ▲${round(gain_percent,2)}% Cash:${round(cash,2)}')
