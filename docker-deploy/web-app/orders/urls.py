from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    UserPostListView,
    PostUpdateView,
)
from . import views

urlpatterns = [
    path('', views.ad, name='ups-ad'),
    path('home/', PostListView.as_view(), name='orders-home'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-orders'),
    path('order/<int:pk>/', PostDetailView.as_view(), name='order-detail'),
    path('order/<int:pk>/update/', PostUpdateView.as_view(), name='order-update'),
]

