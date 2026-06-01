"""
Dota 2 Item Shop models
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    avatar_static = models.CharField(max_length=255, blank=True, default='')
    bio = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            try:
                return self.avatar.url
            except ValueError:
                pass
        if self.avatar_static:
            return self.avatar_static
        return None


class Dota2Item(models.Model):
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('legendary', 'Legendary'),
    ]
    CATEGORY_CHOICES = [
        ('core', 'Core'),
        ('support', 'Support'),
        ('neutral', 'Neutral'),
        ('consumable', 'Consumable'),
        ('hero_skin', 'Hero Skin'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField()
    gold_cost = models.PositiveIntegerField(help_text='In-game gold cost')
    usd_price = models.DecimalField(max_digits=8, decimal_places=2)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='core')
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True, help_text='External URL fallback')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-rarity', 'name']

    def __str__(self):
        return self.name

    @property
    def image_src(self):
        if self.image:
            return self.image.url
        return self.image_url or ''


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shop_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"

    @property
    def total(self):
        return sum(
            item.item.usd_price * item.quantity
            for item in self.cart_items.select_related('item').all()
        )


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    item = models.ForeignKey(Dota2Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ['cart', 'item']

    def __str__(self):
        return f"{self.quantity}x {self.item.name}"

    @property
    def subtotal(self):
        return self.item.usd_price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_orders')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet of {self.user.username}"


class WalletTransaction(models.Model):
    TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('purchase', 'Purchase'),
        ('transfer_out', 'Transfer Out'),
        ('transfer_in', 'Transfer In'),
        ('voucher', 'Voucher'),
    ]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} {self.amount} for {self.wallet.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(Dota2Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_snapshot = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.item.name}"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP {self.code} for {self.user.username}"


class Review(models.Model):
    item = models.ForeignKey(Dota2Item, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(default=5)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['item', 'user']

    def __str__(self):
        return f"Review by {self.user.username} on {self.item.name}"


class InventoryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Dota2Item, on_delete=models.CASCADE, related_name='inventory_entries')
    quantity = models.PositiveIntegerField(default=1)
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'item']
        ordering = ['-acquired_at']

    def __str__(self):
        return f"{self.quantity}x {self.item.name} ({self.user.username})"


class Voucher(models.Model):
    TYPE_CHOICES = [
        ('wallet', 'Wallet Credit'),
        ('item', 'Item / Skin'),
    ]
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    wallet_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                        help_text='Credit amount (for wallet type)')
    item = models.ForeignKey(Dota2Item, on_delete=models.SET_NULL, null=True, blank=True,
                             help_text='Item to grant (for item type)')
    item_quantity = models.PositiveIntegerField(default=1)
    max_claims = models.PositiveIntegerField(default=1, help_text='Total allowed claims across all users')
    times_claimed = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Voucher {self.code} ({self.type})"

    @property
    def remaining(self):
        return max(0, self.max_claims - self.times_claimed)


class VoucherClaim(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='claims')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voucher_claims')
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-claimed_at']

    def __str__(self):
        return f"{self.user.username} claimed {self.voucher.code}"
