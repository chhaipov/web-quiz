"""
DRF Serializers for Dota 2 Item Shop API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Dota2Item, Cart, CartItem, Order, OrderItem


class Dota2ItemSerializer(serializers.ModelSerializer):
    image_src = serializers.ReadOnlyField()

    class Meta:
        model = Dota2Item
        fields = ['id', 'name', 'description', 'gold_cost', 'usd_price', 'rarity', 'category', 'image_src', 'is_active']


class CartItemSerializer(serializers.ModelSerializer):
    item = Dota2ItemSerializer(read_only=True)
    item_id = serializers.PrimaryKeyRelatedField(queryset=Dota2Item.objects.filter(is_active=True), write_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_id', 'quantity', 'subtotal']


class CartSerializer(serializers.ModelSerializer):
    cart_items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'cart_items', 'total', 'created_at']


class OrderItemSerializer(serializers.ModelSerializer):
    item = Dota2ItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'quantity', 'price_snapshot']


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'total', 'status', 'created_at', 'order_items']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']
