# forms.py

from django import forms
from .models import *

class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = ['name', 'start_date', 'end_date', 'active']


class ProductOfferForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.all())
    discount_percentage = forms.IntegerField(min_value=1, max_value=100)


class CategoryOfferForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    discount_percentage = forms.IntegerField(min_value=1, max_value=100)


class ReferralOfferForm(forms.Form):
    reward_amount = forms.DecimalField(min_value=0)
    minimum_purchase_amount = forms.DecimalField(min_value=0)
