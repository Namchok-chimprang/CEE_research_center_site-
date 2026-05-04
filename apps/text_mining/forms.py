from django import forms

from .services import SOURCE_FIELD_CHOICES


class TextMiningRunForm(forms.Form):
    title = forms.CharField(max_length=255, required=False)
    source_fields = forms.MultipleChoiceField(
        choices=SOURCE_FIELD_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        initial=["title", "abstract"],
        help_text="Choose which publication fields should be included in the analysis.",
    )
