from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse
from random import uniform
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *


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
                        return HttpResponse("Bought")
                else:
                    return HttpResponse("Not enough money!")
            elif request.POST.get('type') == "sell":
                try:
                    if user.portfolio_set.get(stock=stock_chosen).quantity > quantity:
                        print("creating sell transaction")
                        Transaction.objects.create(
                            user=user, stock=stock_chosen, units=quantity, price_each=stock_chosen.ltp, transaction='sell').save()
                        stock_in_portfolio = user.portfolio_set.get(
                            stock=stock_chosen)
                        stock_in_portfolio.quantity -= quantity
                        change = stock_chosen.ltp*quantity
                        user.accountvalue_set.create(value=(
                            ac_value+change), holdings_value=(latest_account.holdings_value)).save()
                        stock_in_portfolio.save()
                        return HttpResponse("Sold!")
                    else:
                        return HttpResponse("Not holding enough shares!")
                except:
                    return HttpResponse("Not holding enough shares!")
    return HttpResponse("This should never happen. Contact the devs!")


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
    # ensure this is the default value for money on new account
    initial = 10000.0
    gain_percent = ((current+cash)/initial-1)*100.0
    color = "text-success" if gain_percent >= 0 else "text-danger"
    return HttpResponse(f'<p>Holdings Value: ₹{round(current,2)}</p><p class="{color}">▲{round(gain_percent,2)}%</p><p>Cash: ₹{round(cash,2)}</p>')


@login_required
def add_money(request):
    if request.method == 'POST':
        form = MoneyForm(request.POST)
        if form.is_valid():
            money = form.cleaned_data.get('money')
            last_value = request.user.accountvalue_set.all().order_by('-time').first()
            request.user.accountvalue_set.create(
                value=last_value.value+money, holdings_value=last_value.holdings_value).save()
            messages.success(request, f'₹{money} added!')
            return redirect('stocks-dashboard')
    else:
        form = MoneyForm()
    return render(request, 'stocks/money.html', {'form': form})


@login_required
def portfolio(request):
    query = request.user.portfolio_set.all()
    data = [{'name': each.stock.name, 'full_name': each.stock.full_name, 'ltp': each.stock.ltp, 'quantity': each.quantity}
            for each in query]
    return render(request, 'stocks/portfolio.html', {'data': data})
