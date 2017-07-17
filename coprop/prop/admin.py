from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Property, Owner, OwnerAddress, PropertyAddress, Account, LienAuction, County


class CountyAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'active')


admin.site.register(Property, VersionAdmin)
admin.site.register(Owner, VersionAdmin)
admin.site.register(OwnerAddress, VersionAdmin)
admin.site.register(PropertyAddress, VersionAdmin)

admin.site.register(Account)
admin.site.register(LienAuction)
admin.site.register(County, CountyAdmin)
