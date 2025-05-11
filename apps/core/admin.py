from django.contrib import admin
from apps.accounts.models import *

# Register your models here.
admin.site.register(AdminOrEmployee)
admin.site.register(AuthenticationLog)
admin.site.register(CustomerOrUserReview)
admin.site.register(DataRecordOrDataset)

admin.site.register(Audit)
admin.site.register(AnalysisReport)
admin.site.register(EncryptionKey)
