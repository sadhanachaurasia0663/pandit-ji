from django import forms


class BookingRequestForm(forms.Form):
    name = forms.CharField(min_length=2, max_length=100)
    phone = forms.CharField(min_length=8, max_length=20)
    service = forms.CharField(min_length=2, max_length=100)
    preferred_date = forms.DateField(input_formats=["%Y-%m-%d"])
    details = forms.CharField(min_length=1, max_length=2000)
