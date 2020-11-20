from django import forms


class MoneyForm(forms.Form):
    money = forms.FloatField(label='Money')
