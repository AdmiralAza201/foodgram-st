import base64
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str):
            if data.strip() == "":
                raise serializers.ValidationError(
                    'This field may not be blank.'
                )
            if data.startswith('data:image'):
                header, b64 = data.split(';base64,', 1)
                ext = header.split('/')[-1].lower()
            else:
                b64, ext = data, 'png'
            try:
                decoded = base64.b64decode(b64)
            except Exception:
                raise serializers.ValidationError('Invalid image base64')
            return ContentFile(decoded, name=f'upload.{ext}')
        return super().to_internal_value(data)
