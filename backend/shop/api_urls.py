"""
API URLs - JWT Auth (Vite SPA)
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import api_views

urlpatterns = [
    path('health/', api_views.health, name='health'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', api_views.register, name='register'),
    path('auth/profile/', api_views.profile, name='profile'),
    path('auth/change-password/', api_views.change_password, name='change_password'),
    path('auth/check-username/', api_views.check_username, name='check_username'),
    path('auth/forgot-password/', api_views.request_otp, name='request_otp'),
    path('auth/verify-otp/', api_views.verify_otp, name='verify_otp'),
    path('items/', api_views.ItemList.as_view(), name='item_list'),
    path('items/<int:pk>/', api_views.ItemDetail.as_view(), name='item_detail'),
    path('items/<int:pk>/reviews/', api_views.item_reviews, name='item_reviews'),
    path('items/validate-image/', api_views.validate_image_url, name='validate_image'),
    path('preview/', api_views.render_preview, name='render_preview'),
    path('cart/', api_views.cart_detail, name='cart_detail'),
    path('cart/add/', api_views.cart_add, name='cart_add'),
    path('cart/<int:pk>/', api_views.cart_item_update, name='cart_item_update'),
    path('wallet/', api_views.wallet_detail, name='wallet_detail'),
    path('wallet/deposit/', api_views.wallet_deposit, name='wallet_deposit'),
    path('wallet/transfer/', api_views.wallet_transfer, name='wallet_transfer'),
    path('wallet/transactions/', api_views.wallet_transactions, name='wallet_transactions'),
    path('vouchers/', api_views.voucher_list, name='voucher_list'),
    path('vouchers/claim/', api_views.voucher_claim, name='voucher_claim'),
    path('inventory/', api_views.inventory_list, name='inventory_list'),
    path('inventory/send/', api_views.inventory_send, name='inventory_send'),
    path('inventory/trade/', api_views.inventory_trade, name='inventory_trade'),
    path('inventory/user/<str:username>/', api_views.user_inventory_public, name='user_inventory_public'),
    path('orders/', api_views.order_list_create, name='order_list_create'),
    path('orders/<int:pk>/', api_views.order_detail, name='order_detail'),
    path('orders/export/', api_views.export_orders, name='export_orders'),
    path('files/download/', api_views.download_file, name='download_file'),
    path('game/submit/', api_views.game_submit_score, name='game_submit_score'),
]
