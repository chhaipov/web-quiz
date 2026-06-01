"""
URLs - Django Template Routes (Cookie Auth)
"""
from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.ShopLoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.ShopLogoutView.as_view(), name='logout'),
    path('items/', views.items_list, name='items'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('cart/', views.cart_detail, name='cart'),
    path('cart/add/', views.cart_add, name='cart_add'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('orders/', views.orders_list, name='orders'),
    path('profile/', views.profile_edit, name='profile'),
    path('preview/', views.template_preview, name='preview'),
]
