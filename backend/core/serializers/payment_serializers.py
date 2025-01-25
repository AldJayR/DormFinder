from rest_framework import serializers
from ..models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'booking', 'amount', 'method', 'reference_number', 'is_verified']
        read_only_fields = ['is_verified']

    def validate(self, data):
        method = data.get('method')
        reference = data.get('reference_number')
        
        # PH payment validation
        if method in ['gcash', 'bank_transfer'] and not reference:
            raise serializers.ValidationError(
                f"Reference number is required for {method} payments."
            )
            
        if method == 'cash' and reference:
            raise serializers.ValidationError(
                "Reference number should not be provided for cash payments."
            )
        
        return data