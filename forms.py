from django import forms
from .models import Order, Supplier, Transport, Transit, Dispute, ActionPlan, Cause


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        exclude = ["created_at"]
        widgets = {
            "order_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "planned_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "actual_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "observations": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in self.Meta.widgets:
                field.widget.attrs.setdefault("class", "form-control")


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        exclude = ["created_at"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class TransportForm(forms.ModelForm):
    class Meta:
        model = Transport
        fields = "__all__"
        widgets = {
            "planned_departure": forms.DateInput(attrs={"type": "date"}),
            "actual_departure": forms.DateInput(attrs={"type": "date"}),
            "planned_arrival": forms.DateInput(attrs={"type": "date"}),
            "actual_arrival": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class TransitForm(forms.ModelForm):
    class Meta:
        model = Transit
        fields = "__all__"
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "planned_clearance_date": forms.DateInput(attrs={"type": "date"}),
            "actual_clearance_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class DisputeForm(forms.ModelForm):
    class Meta:
        model = Dispute
        fields = "__all__"
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "corrective_action": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ActionPlanForm(forms.ModelForm):
    class Meta:
        model = ActionPlan
        fields = "__all__"
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "action": forms.Textarea(attrs={"rows": 2}),
            "expected_result": forms.Textarea(attrs={"rows": 2}),
            "comment": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ExcelImportForm(forms.Form):
    fichier = forms.FileField(label="Fichier Excel (.xlsx)", widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".xlsx,.xls"}))
