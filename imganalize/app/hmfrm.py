from django import forms

class hfrm(forms.Form):
    filepth=forms.FileField(label="Choose File ")