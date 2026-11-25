from django import forms

from .models import ContactMessage, QuoteRequest


class ContactForm(forms.ModelForm):
    # Honeypot: real visitors never see or fill this; bots usually do.
    website = forms.CharField(required=False)

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write a little more (at least 10 characters).")
        return message


class HoneypotMixin(forms.Form):
    website = forms.CharField(required=False)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""


class QuoteForm(HoneypotMixin):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    service = forms.CharField(max_length=80, required=False)
    budget = forms.ChoiceField(choices=QuoteRequest.BUDGETS)
    deadline = forms.DateField(required=False)
    details = forms.CharField(min_length=10, max_length=5000)

    def clean_deadline(self):
        from django.utils import timezone
        d = self.cleaned_data.get("deadline")
        if d and d < timezone.localdate():
            raise forms.ValidationError("The deadline cannot be in the past.")
        return d


class TestimonialForm(HoneypotMixin):
    name = forms.CharField(max_length=100)
    role = forms.CharField(max_length=100, required=False)
    rating = forms.IntegerField(min_value=1, max_value=5)
    text = forms.CharField(min_length=10, max_length=1000)


class SubscribeForm(HoneypotMixin):
    email = forms.EmailField()
