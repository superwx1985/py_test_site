from django.db.models import Transform

class AbsoluteValue(Transform):
    lookup_name = 'abs'
    function = 'ABS'

from django.db.models import IntegerField
IntegerField.register_lookup(AbsoluteValue)