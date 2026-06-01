from decimal import Decimal

from django.contrib.auth.models import User

from shop.models import UserProfile, Wallet, WalletTransaction


USERNAME = "testuser"
PASSWORD = "Test123456!"
EMAIL = "testuser@example.com"
DEPOSIT_AMOUNT = Decimal("500.00")


user, created = User.objects.get_or_create(
    username=USERNAME,
    defaults={"email": EMAIL},
)

if created:
    user.set_password(PASSWORD)
    user.save()
else:
    if user.email != EMAIL:
        user.email = EMAIL
        user.save(update_fields=["email"])

profile, _ = UserProfile.objects.get_or_create(user=user)
wallet, _ = Wallet.objects.get_or_create(user=user, defaults={"balance": Decimal("0.00")})

wallet.balance += DEPOSIT_AMOUNT
wallet.save(update_fields=["balance"])

WalletTransaction.objects.create(
    wallet=wallet,
    type="deposit",
    amount=DEPOSIT_AMOUNT,
    balance_after=wallet.balance,
    reference="Scripted test deposit",
)

print(f"User: {user.username}")
print(f"Created: {created}")
print(f"Password: {PASSWORD}")
print(f"Deposited: {DEPOSIT_AMOUNT}")
print(f"New balance: {wallet.balance}")
