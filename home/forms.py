# forms.py
from django import forms

class MyForm(forms.Form):
    my_datetime_field = forms.DateTimeField(
        label='Choose a date and time',
        input_formats=['%Y-%m-%d %H:%M:%S'],  # specify the format of input
        widget=forms.DateTimeInput(attrs={'class': 'datepicker'}),  # you can use a datetime picker widget
    )
