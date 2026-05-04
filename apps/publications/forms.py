from django import forms

from .models import PublicationTreeLayout


class PublicationTreeLayoutForm(forms.ModelForm):
    class Meta:
        model = PublicationTreeLayout
        fields = [
            "title",
            "preset_key",
            "is_active",
            "leaf_count",
            "branch_image",
            "branch_size",
            "branch_position",
            "base_radius",
            "radius_gain",
            "default_leaf_scale",
            "leaf_color",
            "default_leaf_opacity",
            "leaf_1_sdg",
            "leaf_1_x",
            "leaf_1_y",
            "leaf_1_scale",
            "leaf_1_color",
            "leaf_1_opacity",
            "leaf_2_sdg",
            "leaf_2_x",
            "leaf_2_y",
            "leaf_2_scale",
            "leaf_2_color",
            "leaf_2_opacity",
            "leaf_3_sdg",
            "leaf_3_x",
            "leaf_3_y",
            "leaf_3_scale",
            "leaf_3_color",
            "leaf_3_opacity",
            "leaf_4_sdg",
            "leaf_4_x",
            "leaf_4_y",
            "leaf_4_scale",
            "leaf_4_color",
            "leaf_4_opacity",
            "leaf_5_sdg",
            "leaf_5_x",
            "leaf_5_y",
            "leaf_5_scale",
            "leaf_5_color",
            "leaf_5_opacity",
        ]

    def clean_leaf_count(self):
        value = self.cleaned_data["leaf_count"]
        return max(1, min(5, value))

    def clean_leaf_color(self):
        value = (self.cleaned_data.get("leaf_color") or "").strip()
        if not value:
            return "#6e8bdc"
        if not value.startswith("#"):
            value = f"#{value}"
        return value[:7]

    def clean(self):
        cleaned_data = super().clean()
        for index in range(1, 6):
            sdg_key = f"leaf_{index}_sdg"
            color_key = f"leaf_{index}_color"
            value = (cleaned_data.get(color_key) or "").strip()
            if value and not value.startswith("#"):
                value = f"#{value}"
            cleaned_data[color_key] = value[:7]
            sdg_value = cleaned_data.get(sdg_key)
            if sdg_value and not (1 <= sdg_value <= 17):
                self.add_error(sdg_key, "Choose an SDG between 1 and 17.")
        return cleaned_data
