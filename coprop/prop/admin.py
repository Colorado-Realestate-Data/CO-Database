from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Property, Owner, OwnerAddress, PropertyAddress, \
    Account, LienAuction


admin.site.register(Property, SimpleHistoryAdmin)
admin.site.register(Owner, SimpleHistoryAdmin)
admin.site.register(OwnerAddress, SimpleHistoryAdmin)
admin.site.register(PropertyAddress, SimpleHistoryAdmin)
admin.site.register(Account)
admin.site.register(LienAuction)
