from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin panel URL
    path('',views.home, name='home'),  # Root URL will be handled by the 'home' view
    path('agent/', include('agent.urls')),  # Include 'agent' app URL patterns
]
