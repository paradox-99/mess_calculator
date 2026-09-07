from django import forms


class DailyEntryForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    lunch = forms.BooleanField(
        required=False,
        label="Lunch",
        widget=forms.CheckboxInput(attrs={"class": "meal-checkbox"}),
    )
    dinner = forms.BooleanField(
        required=False,
        label="Dinner",
        widget=forms.CheckboxInput(attrs={"class": "meal-checkbox"}),
    )
    cost = forms.DecimalField(
        max_digits=8, decimal_places=2, min_value=0, required=False, initial=0
    )


class ExtraMealForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    meal_type = forms.ChoiceField(
        choices=(("lunch", "Lunch"), ("dinner", "Dinner")),
        label="Meal type",
    )
    quantity = forms.DecimalField(
        max_digits=2,
        decimal_places=1,
        min_value=0.1,
        max_value=9.9,
        initial=1,
        label="Extra meals",
    )