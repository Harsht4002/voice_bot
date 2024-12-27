import os
from django.core.asgi import get_asgi_application
from fastapi import FastAPI
import uvicorn
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Create FastAPI app instance
from api.endpoints import app as fastapi_app

# Combine Django and FastAPI apps using ASGI
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": fastapi_app,
})
