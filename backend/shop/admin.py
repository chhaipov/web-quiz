"""
Django Admin - Dota 2 Item Shop
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Dota2Item, Cart, CartItem, Order, OrderItem, Review, InventoryItem, Voucher, VoucherClaim, UserProfile


@admin.register(Dota2Item)
class Dota2ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'rarity', 'category', 'gold_cost', 'usd_price', 'is_active', 'image_preview']
    list_filter = ['rarity', 'category', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

    def image_preview(self, obj):
        src = obj.image_src
        if src:
            return format_html('<img src="{}" width="40" height="40" style="object-fit:cover;" />', src)
        return '-'
    image_preview.short_description = 'Image'


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['item', 'quantity']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'updated_at']
    inlines = [CartItemInline]
    readonly_fields = ['created_at', 'updated_at']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['item', 'quantity', 'price_snapshot']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_as_shipped']

    @admin.action(description='Mark selected as Shipped')
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['item', 'user', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['item__name', 'user__username', 'text']


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'quantity', 'acquired_at']
    list_filter = ['item__category', 'item__rarity']
    search_fields = ['user__username', 'item__name']


class VoucherClaimInline(admin.TabularInline):
    model = VoucherClaim
    extra = 0
    readonly_fields = ['user', 'claimed_at']


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'type', 'wallet_amount', 'item', 'max_claims', 'times_claimed', 'is_active']
    list_filter = ['type', 'is_active']
    search_fields = ['code']
    inlines = [VoucherClaimInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'avatar']
    search_fields = ['user__username']
