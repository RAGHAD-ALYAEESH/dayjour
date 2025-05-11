"""
URL configuration for dayjour project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#from django.contrib import admin
# from django.urls import path

# urlpatterns = [
#     path('admin/', admin.site.urls),
#      path('core/', views.index2)

# ]from django.contrib import admin
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.utils.translation import gettext_lazy as _

urlpatterns = i18n_patterns(
    path(_('admin/'), admin.site.urls),

    path('', include('apps.core.urls')),               # الصفحة الرئيسية وتسجيل الدخول
    path(_('dataset/'), include('apps.dataset.urls')), # رفع البيانات
    path(_('collab/'), include('apps.collab.urls')),   # التعاون
    path(_('train/'), include('apps.train.urls')),     # التدريب والتحليل
    path(_('account/'), include('apps.accounts.urls')), # الحساب
)

# لإتاحة الوصول للملفات عند التطوير
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)