from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MockProductViewSet, MockOrderViewSet, MockReportViewSet

router = DefaultRouter()
router.register(r'products', MockProductViewSet, basename='product')
router.register(r'orders', MockOrderViewSet, basename='order')
router.register(r'reports', MockReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]

