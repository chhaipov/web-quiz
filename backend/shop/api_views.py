"""
API Views - JWT Auth (for Vite SPA)
"""
import os
import time
import random
import string
import subprocess
import requests
from decimal import Decimal
from rest_framework import status, generics, serializers as drf_serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from django.conf import settings
from django.http import FileResponse

from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes

from .models import Dota2Item, Cart, CartItem, Order, OrderItem, Wallet, WalletTransaction, Review, PasswordResetOTP, InventoryItem, Voucher, VoucherClaim, UserProfile
from .serializers import (
    Dota2ItemSerializer,
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
    UserSerializer,
)


# =====================================================================
#  Health (deployment / load balancer)
# =====================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """GET /api/health/ - Returns 200 OK for liveness/readiness probes."""
    return Response({'status': 'ok'})


# =====================================================================
#  Items
# =====================================================================

class ItemList(generics.ListAPIView):
    """GET /api/items/ - List items (public). Supports search, ordering, pagination."""
    queryset = Dota2Item.objects.filter(is_active=True)
    serializer_class = Dota2ItemSerializer
    permission_classes = [AllowAny]

    class Meta:
        tags = ['Items']

    @extend_schema(
        tags=['Items'],
        summary='List store items',
        description='Retrieve all active items. Supports filtering by rarity/category, text search, ordering, and pagination.',
        parameters=[
            OpenApiParameter('rarity', str, description='Filter by rarity (common, uncommon, rare, mythical, legendary, immortal, arcana)'),
            OpenApiParameter('category', str, description='Filter by category (consumable, equipment, weapon, armor, accessory, hero_skin)'),
            OpenApiParameter('search', str, description='Text search across name and description'),
            OpenApiParameter('ordering', str, description='Sort field: name, -name, price, -price, rarity, -rarity, gold, -gold'),
            OpenApiParameter('page', int, description='Page number (enables pagination)'),
            OpenApiParameter('page_size', int, description='Items per page (default 12, max 100)'),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        rarity = self.request.query_params.get('rarity')
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search', '').strip()
        ordering = self.request.query_params.get('ordering', '')
        if rarity:
            qs = qs.filter(rarity=rarity)
        if category:
            qs = qs.filter(category=category)
        # VULN(SQLi): raw SQL with string interpolation instead of parameterized ORM query
        if search:
            qs = qs.extra(where=[f"shop_dota2item.name LIKE '%%{search}%%' OR shop_dota2item.description LIKE '%%{search}%%'"])
        allowed_orderings = {
            'name': 'name', '-name': '-name',
            'price': 'usd_price', '-price': '-usd_price',
            'rarity': 'rarity', '-rarity': '-rarity',
            'gold': 'gold_cost', '-gold': '-gold_cost',
        }
        if ordering in allowed_orderings:
            qs = qs.order_by(allowed_orderings[ordering])
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = request.query_params.get('page')
        page_size_param = request.query_params.get('page_size')
        if page is not None:
            try:
                page = max(1, int(page))
                page_size = min(100, max(1, int(page_size_param or 12)))
            except (TypeError, ValueError):
                page, page_size = 1, 12
            total = qs.count()
            start = (page - 1) * page_size
            items = qs[start:start + page_size]
            serializer = self.get_serializer(items, many=True)
            return Response({
                'results': serializer.data,
                'count': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size,
            })
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


@extend_schema(tags=['Items'], summary='Get item details', description='Retrieve a single active item by ID.')
class ItemDetail(generics.RetrieveAPIView):
    """GET /api/items/:id/ - Item detail (public)"""
    queryset = Dota2Item.objects.filter(is_active=True)
    serializer_class = Dota2ItemSerializer
    permission_classes = [AllowAny]


# =====================================================================
#  Cart
# =====================================================================

@extend_schema(
    tags=['Cart'],
    summary='View cart',
    description='Get the current user\'s shopping cart with all items.',
    responses={200: CartSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    """GET /api/cart/ - Current cart with items"""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)


@extend_schema(
    tags=['Cart'],
    summary='Add item to cart',
    description='Add an item to the cart. If the item already exists, its quantity is incremented.',
    request=inline_serializer('CartAddRequest', fields={
        'item_id': drf_serializers.IntegerField(help_text='ID of the item to add'),
        'quantity': drf_serializers.IntegerField(default=1, help_text='Quantity to add'),
    }),
    responses={201: CartItemSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add(request):
    """POST /api/cart/add/ - Add item (item_id, quantity)"""
    item_id = request.data.get('item_id')
    quantity = request.data.get('quantity', 1)
    if not item_id:
        return Response({'error': 'item_id required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        item = Dota2Item.objects.get(id=item_id, is_active=True)
    except Dota2Item.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item, defaults={'quantity': quantity})
    if not created:
        cart_item.quantity += int(quantity)
        cart_item.save()
    serializer = CartItemSerializer(cart_item)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Cart'],
    methods=['PATCH'],
    summary='Update cart item quantity',
    description='Change the quantity of a cart item. Setting quantity to 0 removes it.',
    request=inline_serializer('CartItemUpdateRequest', fields={
        'quantity': drf_serializers.IntegerField(help_text='New quantity (0 to remove)'),
    }),
    responses={200: CartItemSerializer},
)
@extend_schema(
    tags=['Cart'],
    methods=['DELETE'],
    summary='Remove cart item',
    description='Remove an item from the cart.',
    responses={204: None},
)
@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_item_update(request, pk):
    """PATCH /api/cart/:id/ - Update quantity, DELETE - Remove"""
    try:
        # VULN(IDOR): no user ownership check — any authenticated user can modify any cart item
        cart_item = CartItem.objects.get(pk=pk)
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PATCH':
        quantity = request.data.get('quantity')
        if quantity is not None:
            q = int(quantity)
            if q <= 0:
                cart_item.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            cart_item.quantity = q
            cart_item.save()
        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)
    else:
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# =====================================================================
#  Auth
# =====================================================================

DOTA2_HEROES = [
    'abaddon', 'alchemist', 'ancient_apparition', 'anti_mage', 'arc_warden',
    'axe', 'bane', 'batrider', 'beastmaster', 'bloodseeker',
    'bounty_hunter', 'brewmaster', 'bristleback', 'broodmother', 'centaur',
    'chaos_knight', 'chen', 'clinkz', 'crystal_maiden', 'dark_seer',
    'dark_willow', 'dawnbreaker', 'dazzle', 'death_prophet', 'disruptor',
    'doom_bringer', 'dragon_knight', 'drow_ranger', 'earth_spirit', 'earthshaker',
    'elder_titan', 'ember_spirit', 'enchantress', 'enigma', 'faceless_void',
    'furion', 'grimstroke', 'gyrocopter', 'hoodwink', 'huskar',
    'invoker', 'jakiro', 'juggernaut', 'keeper_of_the_light', 'kunkka',
    'legion_commander', 'leshrac', 'lich', 'lina', 'lion',
    'lone_druid', 'luna', 'lycan', 'magnus', 'marci',
    'mars', 'medusa', 'meepo', 'mirana', 'monkey_king',
    'morphling', 'muerta', 'naga_siren', 'necrolyte', 'nevermore',
    'night_stalker', 'nyx_assassin', 'ogre_magi', 'omniknight', 'oracle',
    'pangolier', 'phantom_assassin', 'phantom_lancer', 'phoenix', 'puck',
    'pudge', 'pugna', 'queenofpain', 'razor', 'riki',
    'rubick', 'sand_king', 'shadow_demon', 'shadow_shaman', 'silencer',
    'skeleton_king', 'skywrath_mage', 'slardar', 'slark', 'snapfire',
    'sniper', 'spectre', 'spirit_breaker', 'storm_spirit', 'sven',
    'techies', 'templar_assassin', 'terrorblade', 'tidehunter', 'tinker',
    'tiny', 'treant', 'troll_warlord', 'tusk', 'undying',
    'ursa', 'vengefulspirit', 'venomancer', 'viper', 'visage',
    'void_spirit', 'warlock', 'weaver', 'windrunner', 'winter_wyvern',
    'witch_doctor', 'zeus',
]


def _generate_hero_username():
    """Pick a random Dota 2 hero and append a number suffix to ensure uniqueness."""
    random.shuffle(DOTA2_HEROES)
    for hero in DOTA2_HEROES:
        display = hero.replace('_', ' ').title().replace(' ', '_')
        if not User.objects.filter(username=display).exists():
            return hero, display
    suffix = random.randint(100, 9999)
    hero = random.choice(DOTA2_HEROES)
    display = hero.replace('_', ' ').title().replace(' ', '_') + str(suffix)
    return hero, display


@extend_schema(
    tags=['Auth'],
    summary='Register new user',
    description='Create a new account with a randomly assigned Dota 2 hero name and avatar. Only a password is required. The generated username is returned in the response.',
    request=inline_serializer('RegisterRequest', fields={
        'password': drf_serializers.CharField(help_text='Password for the new account'),
        'email': drf_serializers.EmailField(required=False, default=''),
    }),
    responses={201: inline_serializer('RegisterResponse', fields={
        'access': drf_serializers.CharField(),
        'refresh': drf_serializers.CharField(),
        'user': inline_serializer('RegisterUser', fields={
            'id': drf_serializers.IntegerField(),
            'username': drf_serializers.CharField(help_text='Randomly assigned Dota 2 hero name'),
        }),
        'password': drf_serializers.CharField(help_text='The password you provided (echoed back for confirmation)'),
        'avatar_url': drf_serializers.CharField(help_text='URL of the assigned hero avatar'),
    })},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """POST /api/auth/register/ - Create user with random Dota 2 hero name + random password"""
    email = request.data.get('email', '')

    hero_key, username = _generate_hero_username()
    avatar_path = f'/images/heroes/{hero_key}.png'
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    user = User.objects.create_user(username=username, password=password, email=email)
    Wallet.objects.get_or_create(user=user, defaults={'balance': 0})
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    profile_obj.avatar_static = avatar_path
    profile_obj.save()

    return Response({
        'user': {'id': user.id, 'username': user.username},
        'password': password,
        'avatar_url': avatar_path,
    }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Auth'],
    methods=['GET'],
    summary='Get profile',
    description='Retrieve the authenticated user\'s profile including avatar and bio.',
    responses={200: inline_serializer('ProfileResponse', fields={
        'id': drf_serializers.IntegerField(),
        'username': drf_serializers.CharField(),
        'email': drf_serializers.EmailField(),
        'avatar_url': drf_serializers.CharField(allow_null=True),
        'bio': drf_serializers.CharField(),
    })},
)
@extend_schema(
    tags=['Auth'],
    methods=['PATCH'],
    summary='Update profile',
    description='Update user profile fields (username, email, bio). The backend also accepts a file upload for `avatar` via multipart/form-data, but the frontend does not expose this.',
    request=inline_serializer('ProfileUpdateRequest', fields={
        'username': drf_serializers.CharField(required=False),
        'email': drf_serializers.EmailField(required=False),
        'bio': drf_serializers.CharField(required=False),
    }),
    responses={200: inline_serializer('ProfileUpdateResponse', fields={
        'id': drf_serializers.IntegerField(),
        'username': drf_serializers.CharField(),
        'email': drf_serializers.EmailField(),
        'avatar_url': drf_serializers.CharField(allow_null=True),
        'bio': drf_serializers.CharField(),
    })},
)
@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """GET /api/auth/profile/ - Get profile. PATCH - Update fields."""
    user = request.user
    user_profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'GET':
        data = UserSerializer(user).data
        data['avatar_url'] = user_profile.avatar_url
        data['bio'] = user_profile.bio
        return Response(data)

    # VULN(Mass Assignment): blindly sets any field from request body
    for key, value in request.data.items():
        if key == 'avatar':
            continue
        setattr(user, key, value)
    user.save()

    # VULN(Unrestricted File Upload): no file type/size validation —
    # accepts any file extension, no content-type check, no size limit.
    # The frontend doesn't expose a file input; students must intercept
    # the request and add a file part to exploit this.
    if 'avatar' in request.FILES:
        user_profile.avatar = request.FILES['avatar']
    if 'bio' in request.data:
        user_profile.bio = request.data['bio']
    user_profile.save()

    data = UserSerializer(user).data
    data['avatar_url'] = user_profile.avatar_url
    data['bio'] = user_profile.bio
    return Response(data)


@extend_schema(
    tags=['Auth'],
    summary='Change password',
    description='Change the authenticated user\'s password.',
    request=inline_serializer('ChangePasswordRequest', fields={
        'old_password': drf_serializers.CharField(),
        'new_password': drf_serializers.CharField(help_text='Min 6 characters'),
    }),
    responses={200: inline_serializer('MessageResponse', fields={
        'detail': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """POST /api/auth/change-password/ - Change password"""
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if not old_password or not new_password:
        return Response({'detail': 'old_password and new_password required'}, status=status.HTTP_400_BAD_REQUEST)
    if not request.user.check_password(old_password):
        return Response({'detail': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
    if len(new_password) < 6:
        return Response({'detail': 'New password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
    request.user.set_password(new_password)
    request.user.save()
    return Response({'detail': 'Password changed successfully'})


# =====================================================================
#  Wallet
# =====================================================================

@extend_schema(
    tags=['Wallet'],
    summary='Get wallet balance',
    description='Get the current user\'s wallet balance. Accepts optional `user_id` query param.',
    parameters=[
        OpenApiParameter('user_id', int, description='View another user\'s wallet (IDOR)', required=False),
    ],
    responses={200: inline_serializer('WalletResponse', fields={
        'balance': drf_serializers.CharField(),
    })},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_detail(request):
    """GET /api/wallet/ - Get or create wallet, return balance"""
    # VULN(IDOR): accepts user_id param to view any user's wallet
    user_id = request.query_params.get('user_id', request.user.id)
    wallet, _ = Wallet.objects.get_or_create(user_id=user_id, defaults={'balance': 0})
    return Response({'balance': str(wallet.balance)})


@extend_schema(
    tags=['Wallet'],
    summary='Deposit funds',
    description='Add funds to the wallet. Accepts negative amounts (vulnerability).',
    request=inline_serializer('DepositRequest', fields={
        'amount': drf_serializers.FloatField(help_text='Amount to deposit'),
    }),
    responses={200: inline_serializer('DepositResponse', fields={
        'balance': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wallet_deposit(request):
    """POST /api/wallet/deposit/ - Add funds"""
    amount = request.data.get('amount')
    if amount is None:
        return Response({'error': 'amount required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return Response({'error': 'amount must be a number'}, status=status.HTTP_400_BAD_REQUEST)
    # VULN(Business Logic): no check for amount > 0 — negative deposits allowed
    wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
    wallet.balance += Decimal(str(amount))
    wallet.save()
    WalletTransaction.objects.create(
        wallet=wallet, type='deposit', amount=Decimal(str(amount)),
        balance_after=wallet.balance, reference='Manual deposit',
    )
    return Response({'balance': str(wallet.balance)})


@extend_schema(
    tags=['Wallet'],
    summary='Transfer funds',
    description='Transfer funds to another user. Accepts optional `from_user` to send from a different wallet (IDOR).',
    request=inline_serializer('TransferRequest', fields={
        'recipient': drf_serializers.CharField(help_text='Recipient username'),
        'amount': drf_serializers.FloatField(help_text='Amount to transfer'),
        'from_user': drf_serializers.IntegerField(required=False, help_text='(Hidden) Override sender user ID'),
    }),
    responses={200: inline_serializer('TransferResponse', fields={
        'balance': drf_serializers.CharField(),
        'message': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def wallet_transfer(request):
    """POST /api/wallet/transfer/ - Transfer funds to another user"""
    recipient_username = request.data.get('recipient', '').strip()
    amount = request.data.get('amount')
    # VULN(IDOR): optional from_user param lets attacker transfer FROM any user's wallet
    from_user_id = request.data.get('from_user')
    if not recipient_username:
        return Response({'error': 'recipient username required'}, status=status.HTTP_400_BAD_REQUEST)
    if amount is None:
        return Response({'error': 'amount required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        amount = Decimal(str(float(amount)))
    except (TypeError, ValueError):
        return Response({'error': 'amount must be a number'}, status=status.HTTP_400_BAD_REQUEST)
    if amount <= 0:
        return Response({'error': 'amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        recipient = User.objects.get(username=recipient_username)
    except User.DoesNotExist:
        return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

    if from_user_id:
        sender = User.objects.get(id=from_user_id)
    else:
        sender = request.user

    if recipient.id == sender.id:
        return Response({'error': 'Cannot transfer to yourself'}, status=status.HTTP_400_BAD_REQUEST)

    # VULN(Race Condition): no atomic block, no select_for_update
    # A deliberate sleep widens the window for concurrent exploit
    sender_wallet, _ = Wallet.objects.get_or_create(user=sender, defaults={'balance': 0})
    if sender_wallet.balance < amount:
        return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

    time.sleep(1)

    sender_wallet.balance -= amount
    sender_wallet.save()

    recipient_wallet, _ = Wallet.objects.get_or_create(user=recipient, defaults={'balance': 0})
    recipient_wallet.balance += amount
    recipient_wallet.save()

    WalletTransaction.objects.create(
        wallet=sender_wallet, type='transfer_out', amount=amount,
        balance_after=sender_wallet.balance,
        reference=f'Transfer to {recipient.username}',
    )
    WalletTransaction.objects.create(
        wallet=recipient_wallet, type='transfer_in', amount=amount,
        balance_after=recipient_wallet.balance,
        reference=f'Transfer from {sender.username}',
    )
    return Response({
        'balance': str(sender_wallet.balance),
        'message': f'Transferred ${amount} to {recipient.username}',
    })


@extend_schema(
    tags=['Wallet'],
    summary='Transaction history',
    description='Get the last 50 wallet transactions for the current user.',
    responses={200: inline_serializer('TransactionItem', fields={
        'id': drf_serializers.IntegerField(),
        'type': drf_serializers.CharField(),
        'amount': drf_serializers.CharField(),
        'balance_after': drf_serializers.CharField(),
        'reference': drf_serializers.CharField(),
        'created_at': drf_serializers.DateTimeField(),
    }, many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_transactions(request):
    """GET /api/wallet/transactions/ - Transaction history"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
    txns = wallet.transactions.all()[:50]
    data = [{
        'id': t.id,
        'type': t.type,
        'amount': str(t.amount),
        'balance_after': str(t.balance_after),
        'reference': t.reference,
        'created_at': t.created_at.isoformat(),
    } for t in txns]
    return Response(data)


# =====================================================================
#  Vouchers
# =====================================================================

@extend_schema(
    tags=['Vouchers'],
    summary='List vouchers',
    description='List all active vouchers with their details.',
    responses={200: inline_serializer('VoucherListItem', fields={
        'id': drf_serializers.IntegerField(),
        'code': drf_serializers.CharField(),
        'type': drf_serializers.CharField(),
        'description': drf_serializers.CharField(),
        'remaining': drf_serializers.IntegerField(),
        'max_claims': drf_serializers.IntegerField(),
    }, many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def voucher_list(request):
    """GET /api/vouchers/ - List available vouchers (public info only)"""
    vouchers = Voucher.objects.filter(is_active=True)
    data = [{
        'id': v.id,
        'code': v.code,
        'type': v.type,
        'description': f'${v.wallet_amount} wallet credit' if v.type == 'wallet'
                        else f'{v.item_quantity}x {v.item.name}' if v.item else 'Unknown item',
        'remaining': v.remaining,
        'max_claims': v.max_claims,
    } for v in vouchers]
    return Response(data)


@extend_schema(
    tags=['Vouchers'],
    summary='Claim voucher',
    description='Redeem a voucher code for wallet credit or inventory items.',
    request=inline_serializer('VoucherClaimRequest', fields={
        'code': drf_serializers.CharField(help_text='Voucher code to redeem'),
    }),
    responses={
        200: inline_serializer('VoucherClaimResponse', fields={
            'message': drf_serializers.CharField(),
            'type': drf_serializers.CharField(),
        }),
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def voucher_claim(request):
    """POST /api/vouchers/claim/ - Redeem a voucher code"""
    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'Voucher code required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        voucher = Voucher.objects.get(code=code, is_active=True)
    except Voucher.DoesNotExist:
        return Response({'error': 'Invalid or expired voucher code'}, status=status.HTTP_404_NOT_FOUND)

    # VULN(Race Condition): check is done WITHOUT locking or atomic block.
    # A deliberate sleep between the check and the update widens the window
    # so concurrent requests can all pass the remaining-claims check before
    # any of them increments times_claimed.
    if voucher.times_claimed >= voucher.max_claims:
        return Response({'error': 'Voucher has been fully claimed'}, status=status.HTTP_400_BAD_REQUEST)

    time.sleep(1)

    voucher.times_claimed += 1
    voucher.save()

    VoucherClaim.objects.create(voucher=voucher, user=request.user)

    if voucher.type == 'wallet':
        wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
        wallet.balance += voucher.wallet_amount
        wallet.save()
        WalletTransaction.objects.create(
            wallet=wallet, type='voucher', amount=voucher.wallet_amount,
            balance_after=wallet.balance, reference=f'Voucher: {voucher.code}',
        )
        return Response({
            'message': f'Voucher redeemed! ${voucher.wallet_amount} added to your wallet.',
            'type': 'wallet',
            'amount': str(voucher.wallet_amount),
            'balance': str(wallet.balance),
        })
    elif voucher.type == 'item' and voucher.item:
        inv_entry, created = InventoryItem.objects.get_or_create(
            user=request.user, item=voucher.item,
            defaults={'quantity': voucher.item_quantity}
        )
        if not created:
            inv_entry.quantity += voucher.item_quantity
            inv_entry.save()
        return Response({
            'message': f'Voucher redeemed! {voucher.item_quantity}x {voucher.item.name} added to your inventory.',
            'type': 'item',
            'item_name': voucher.item.name,
            'item_quantity': voucher.item_quantity,
        })
    else:
        return Response({'error': 'Voucher configuration error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================================
#  Inventory
# =====================================================================

@extend_schema(
    tags=['Inventory'],
    summary='List inventory',
    description='Get all items in the authenticated user\'s inventory.',
    responses={200: inline_serializer('InventoryEntry', fields={
        'id': drf_serializers.IntegerField(),
        'item_id': drf_serializers.IntegerField(),
        'name': drf_serializers.CharField(),
        'description': drf_serializers.CharField(),
        'rarity': drf_serializers.CharField(),
        'category': drf_serializers.CharField(),
        'image_src': drf_serializers.CharField(),
        'quantity': drf_serializers.IntegerField(),
        'acquired_at': drf_serializers.DateTimeField(),
    }, many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_list(request):
    """GET /api/inventory/ - List user's inventory items"""
    entries = InventoryItem.objects.filter(
        user=request.user
    ).select_related('item').order_by('-acquired_at')
    data = [{
        'id': e.id,
        'item_id': e.item.id,
        'name': e.item.name,
        'description': e.item.description,
        'rarity': e.item.rarity,
        'category': e.item.category,
        'image_src': e.item.image_src,
        'quantity': e.quantity,
        'acquired_at': e.acquired_at.isoformat(),
    } for e in entries]
    return Response(data)


@extend_schema(
    tags=['Inventory'],
    summary='Send item to user',
    description='Transfer inventory items to another user.',
    request=inline_serializer('InventorySendRequest', fields={
        'inventory_id': drf_serializers.IntegerField(help_text='ID of your inventory entry'),
        'recipient': drf_serializers.CharField(help_text='Recipient username'),
        'quantity': drf_serializers.IntegerField(default=1, help_text='Quantity to send'),
    }),
    responses={200: inline_serializer('InventorySendResponse', fields={
        'message': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inventory_send(request):
    """POST /api/inventory/send/ - Send inventory item(s) to another user"""
    inventory_id = request.data.get('inventory_id')
    recipient_username = request.data.get('recipient', '').strip()
    send_qty = request.data.get('quantity', 1)
    if not inventory_id:
        return Response({'error': 'inventory_id required'}, status=status.HTTP_400_BAD_REQUEST)
    if not recipient_username:
        return Response({'error': 'recipient username required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        send_qty = int(send_qty)
    except (TypeError, ValueError):
        return Response({'error': 'quantity must be a number'}, status=status.HTTP_400_BAD_REQUEST)
    if send_qty <= 0:
        return Response({'error': 'quantity must be positive'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        entry = InventoryItem.objects.select_related('item').get(pk=inventory_id, user=request.user)
    except InventoryItem.DoesNotExist:
        return Response({'error': 'Inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
    if entry.quantity < send_qty:
        return Response({'error': 'Not enough quantity'}, status=status.HTTP_400_BAD_REQUEST)
    if recipient_username == request.user.username:
        return Response({'error': 'Cannot send to yourself'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        recipient = User.objects.get(username=recipient_username)
    except User.DoesNotExist:
        return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        entry.quantity -= send_qty
        if entry.quantity <= 0:
            entry.delete()
        else:
            entry.save()

        recv_entry, created = InventoryItem.objects.get_or_create(
            user=recipient, item=entry.item,
            defaults={'quantity': send_qty}
        )
        if not created:
            recv_entry.quantity += send_qty
            recv_entry.save()

    return Response({
        'message': f'Sent {send_qty}x {entry.item.name} to {recipient.username}',
    })


@extend_schema(
    tags=['Inventory'],
    summary='Trade items',
    description='Execute an instant two-way item trade with another user.',
    request=inline_serializer('InventoryTradeRequest', fields={
        'my_inventory_id': drf_serializers.IntegerField(help_text='Your inventory entry ID'),
        'my_quantity': drf_serializers.IntegerField(default=1),
        'their_username': drf_serializers.CharField(help_text='Other user\'s username'),
        'their_inventory_id': drf_serializers.IntegerField(help_text='Other user\'s inventory entry ID'),
        'their_quantity': drf_serializers.IntegerField(default=1),
    }),
    responses={200: inline_serializer('InventoryTradeResponse', fields={
        'message': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def inventory_trade(request):
    """POST /api/inventory/trade/ - Propose & execute instant trade with another user"""
    my_inventory_id = request.data.get('my_inventory_id')
    my_qty = int(request.data.get('my_quantity', 1))
    their_username = request.data.get('their_username', '').strip()
    their_inventory_id = request.data.get('their_inventory_id')
    their_qty = int(request.data.get('their_quantity', 1))

    if not all([my_inventory_id, their_username, their_inventory_id]):
        return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
    if my_qty <= 0 or their_qty <= 0:
        return Response({'error': 'Quantities must be positive'}, status=status.HTTP_400_BAD_REQUEST)
    if their_username == request.user.username:
        return Response({'error': 'Cannot trade with yourself'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        other_user = User.objects.get(username=their_username)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        try:
            my_entry = InventoryItem.objects.select_for_update().get(pk=my_inventory_id, user=request.user)
        except InventoryItem.DoesNotExist:
            return Response({'error': 'Your inventory item not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            their_entry = InventoryItem.objects.select_for_update().get(pk=their_inventory_id, user=other_user)
        except InventoryItem.DoesNotExist:
            return Response({'error': "Other user's inventory item not found"}, status=status.HTTP_404_NOT_FOUND)

        if my_entry.quantity < my_qty:
            return Response({'error': 'You do not have enough quantity'}, status=status.HTTP_400_BAD_REQUEST)
        if their_entry.quantity < their_qty:
            return Response({'error': 'Other user does not have enough quantity'}, status=status.HTTP_400_BAD_REQUEST)

        my_item = my_entry.item
        their_item = their_entry.item

        my_entry.quantity -= my_qty
        if my_entry.quantity <= 0:
            my_entry.delete()
        else:
            my_entry.save()

        their_entry.quantity -= their_qty
        if their_entry.quantity <= 0:
            their_entry.delete()
        else:
            their_entry.save()

        recv_mine, c = InventoryItem.objects.get_or_create(user=other_user, item=my_item, defaults={'quantity': my_qty})
        if not c:
            recv_mine.quantity += my_qty
            recv_mine.save()

        recv_theirs, c = InventoryItem.objects.get_or_create(user=request.user, item=their_item, defaults={'quantity': their_qty})
        if not c:
            recv_theirs.quantity += their_qty
            recv_theirs.save()

    return Response({
        'message': f'Traded {my_qty}x {my_item.name} for {their_qty}x {their_item.name} with {other_user.username}',
    })


@extend_schema(
    tags=['Inventory'],
    summary='View user inventory',
    description='View another user\'s public inventory (for trading).',
    responses={200: inline_serializer('UserInventoryResponse', fields={
        'username': drf_serializers.CharField(),
        'inventory': drf_serializers.ListField(),
    })},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_inventory_public(request, username):
    """GET /api/inventory/user/:username/ - View another user's inventory (for trading)"""
    try:
        target = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    entries = InventoryItem.objects.filter(user=target).select_related('item')
    data = [{
        'id': e.id,
        'item_id': e.item.id,
        'name': e.item.name,
        'rarity': e.item.rarity,
        'category': e.item.category,
        'image_src': e.item.image_src,
        'quantity': e.quantity,
    } for e in entries]
    return Response({'username': target.username, 'inventory': data})


# =====================================================================
#  Orders
# =====================================================================

@extend_schema(
    tags=['Orders'],
    summary='Get order details',
    description='Retrieve a single order by ID.',
    responses={200: OrderSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    """GET /api/orders/:id/ - Single order detail"""
    try:
        # VULN(IDOR): no user ownership check — any authenticated user can view any order
        order = Order.objects.prefetch_related('order_items__item').get(pk=pk)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = OrderSerializer(order)
    return Response(serializer.data)


@extend_schema(
    tags=['Orders'],
    methods=['GET'],
    summary='List orders',
    description='Get the authenticated user\'s order history.',
    responses={200: OrderSerializer(many=True)},
)
@extend_schema(
    tags=['Orders'],
    methods=['POST'],
    summary='Create order from cart',
    description='Purchase all items in the cart. Deducts wallet balance and adds items to inventory.',
    responses={201: OrderSerializer},
)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_list_create(request):
    """GET /api/orders/ - Order history. POST /api/orders/ - Create order from cart"""
    if request.method == 'GET':
        orders = Order.objects.filter(user=request.user).prefetch_related('order_items__item')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    # POST
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.cart_items.select_related('item').all())
    if not items:
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    total = sum(ci.item.usd_price * ci.quantity for ci in items)
    total_decimal = Decimal(str(total))

    with transaction.atomic():
        wallet = Wallet.objects.select_for_update().get_or_create(
            user=request.user, defaults={'balance': 0}
        )[0]
        if wallet.balance < total_decimal:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
        wallet.balance -= total_decimal
        wallet.save()
        order = Order.objects.create(user=request.user, total=total, status='delivered')
        WalletTransaction.objects.create(
            wallet=wallet, type='purchase', amount=total_decimal,
            balance_after=wallet.balance, reference=f'Order #{order.id}',
        )
        for ci in items:
            OrderItem.objects.create(order=order, item=ci.item, quantity=ci.quantity, price_snapshot=ci.item.usd_price)
            inv_entry, created = InventoryItem.objects.get_or_create(
                user=request.user, item=ci.item, defaults={'quantity': ci.quantity}
            )
            if not created:
                inv_entry.quantity += ci.quantity
                inv_entry.save()
        cart.cart_items.all().delete()
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# =====================================================================
#  Reviews
# =====================================================================

@extend_schema(
    tags=['Items'],
    methods=['GET'],
    summary='List item reviews',
    description='Get all reviews for a specific item.',
    responses={200: inline_serializer('ReviewItem', fields={
        'id': drf_serializers.IntegerField(),
        'user': drf_serializers.CharField(),
        'rating': drf_serializers.IntegerField(),
        'text': drf_serializers.CharField(),
        'created_at': drf_serializers.DateTimeField(),
    }, many=True)},
)
@extend_schema(
    tags=['Items'],
    methods=['POST'],
    summary='Add item review',
    description='Create or update a review for an item. Requires authentication.',
    request=inline_serializer('ReviewRequest', fields={
        'text': drf_serializers.CharField(help_text='Review text'),
        'rating': drf_serializers.IntegerField(default=5, help_text='Rating 1-5'),
    }),
    responses={201: inline_serializer('ReviewCreatedItem', fields={
        'id': drf_serializers.IntegerField(),
        'user': drf_serializers.CharField(),
        'rating': drf_serializers.IntegerField(),
        'text': drf_serializers.CharField(),
        'created_at': drf_serializers.DateTimeField(),
    })},
)
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def item_reviews(request, pk):
    """GET /api/items/:id/reviews/ - List reviews. POST - Create review."""
    try:
        item = Dota2Item.objects.get(pk=pk, is_active=True)
    except Dota2Item.DoesNotExist:
        return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        reviews = item.reviews.select_related('user').all()
        data = [{
            'id': r.id,
            'user': r.user.username,
            'rating': r.rating,
            'text': r.text,
            'created_at': r.created_at.isoformat(),
        } for r in reviews]
        return Response(data)

    # POST - requires auth
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
    text = request.data.get('text', '')
    rating = request.data.get('rating', 5)
    if not text:
        return Response({'error': 'text is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        rating = max(1, min(5, int(rating)))
    except (TypeError, ValueError):
        rating = 5
    review, created = Review.objects.update_or_create(
        item=item, user=request.user,
        defaults={'text': text, 'rating': rating},
    )
    return Response({
        'id': review.id,
        'user': review.user.username,
        'rating': review.rating,
        'text': review.text,
        'created_at': review.created_at.isoformat(),
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


# =====================================================================
#  Tools (SSRF, SSTI, Command Injection, Path Traversal)
# =====================================================================

@extend_schema(
    tags=['Tools'],
    summary='Validate image URL',
    description='Fetches the given URL server-side and reports status (SSRF vector).',
    request=inline_serializer('ValidateImageRequest', fields={
        'url': drf_serializers.URLField(help_text='URL to validate'),
    }),
    responses={200: inline_serializer('ValidateImageResponse', fields={
        'valid': drf_serializers.BooleanField(),
        'status_code': drf_serializers.IntegerField(),
        'content_type': drf_serializers.CharField(),
        'content_length': drf_serializers.IntegerField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_image_url(request):
    """POST /api/items/validate-image/ - Validate an image URL"""
    # VULN(SSRF): fetches any URL the server can reach, including internal services
    url = request.data.get('url', '')
    if not url:
        return Response({'error': 'url required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        resp = requests.get(url, timeout=5)
        return Response({
            'valid': resp.status_code == 200,
            'status_code': resp.status_code,
            'content_type': resp.headers.get('Content-Type', ''),
            'content_length': len(resp.content),
        })
    except Exception as e:
        return Response({'valid': False, 'error': str(e)})


@extend_schema(
    tags=['Tools'],
    summary='Template preview',
    description='Renders a Django template string server-side (SSTI vector).',
    request=inline_serializer('TemplatePreviewRequest', fields={
        'template': drf_serializers.CharField(help_text='Django template string to render'),
    }),
    responses={200: inline_serializer('TemplatePreviewResponse', fields={
        'rendered': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def render_preview(request):
    """POST /api/preview/ - Render a template preview"""
    # VULN(SSTI): renders user-supplied text through Django's template engine
    from django.template import Template, Context
    template_string = request.data.get('template', '')
    if not template_string:
        return Response({'error': 'template required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        t = Template(template_string)
        c = Context({'user': request.user, 'request': request})
        rendered = t.render(c)
        return Response({'rendered': rendered})
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Tools'],
    summary='Export orders',
    description='Export orders to a file (OS command injection vector).',
    request=inline_serializer('ExportRequest', fields={
        'filename': drf_serializers.CharField(default='orders', help_text='Output filename'),
    }),
    responses={200: inline_serializer('ExportResponse', fields={
        'file': drf_serializers.CharField(),
        'message': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_orders(request):
    """POST /api/orders/export/ - Export orders to a file"""
    # VULN(OS Command Injection): user-supplied filename passed to shell command
    filename = request.data.get('filename', 'orders')
    try:
        output = subprocess.check_output(
            f'echo "Order export for {filename}" > export_{filename}.txt && echo export_{filename}.txt',
            shell=True,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return Response({'file': output.strip(), 'message': 'Export complete'})
    except subprocess.CalledProcessError as e:
        return Response({'error': e.output}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Auth'],
    summary='Check username availability',
    description='Check if a username is already registered (user enumeration vector).',
    request=inline_serializer('CheckUsernameRequest', fields={
        'username': drf_serializers.CharField(),
    }),
    responses={200: inline_serializer('CheckUsernameResponse', fields={
        'exists': drf_serializers.BooleanField(),
        'user_id': drf_serializers.IntegerField(required=False),
        'date_joined': drf_serializers.DateTimeField(required=False),
    })},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def check_username(request):
    """POST /api/auth/check-username/ - Check if username exists"""
    # VULN(User Enumeration): reveals whether a username is registered
    username = request.data.get('username', '')
    exists = User.objects.filter(username=username).exists()
    if exists:
        user = User.objects.get(username=username)
        return Response({
            'exists': True,
            'user_id': user.id,
            'date_joined': user.date_joined.isoformat(),
        })
    return Response({'exists': False})


@extend_schema(
    tags=['Auth'],
    summary='Request password reset OTP',
    description='Request a 4-digit OTP for password reset (OTP bruteforce vector).',
    request=inline_serializer('RequestOtpRequest', fields={
        'username': drf_serializers.CharField(),
    }),
    responses={200: inline_serializer('RequestOtpResponse', fields={
        'detail': drf_serializers.CharField(),
        'debug_otp': drf_serializers.CharField(help_text='OTP code (for lab/debug)'),
    })},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    """POST /api/auth/forgot-password/ - Request a 4-digit OTP"""
    # VULN(OTP Bruteforce): only 4 digits (0000-9999), no rate limiting, no expiry check
    username = request.data.get('username', '')
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'detail': 'If account exists, OTP has been sent'})
    code = f'{random.randint(0, 9999):04d}'
    PasswordResetOTP.objects.create(user=user, code=code)
    return Response({
        'detail': 'If account exists, OTP has been sent',
        'debug_otp': code,
    })


@extend_schema(
    tags=['Auth'],
    summary='Verify OTP and reset password',
    description='Verify a 4-digit OTP and set a new password (no rate limiting).',
    request=inline_serializer('VerifyOtpRequest', fields={
        'username': drf_serializers.CharField(),
        'code': drf_serializers.CharField(help_text='4-digit OTP code'),
        'new_password': drf_serializers.CharField(),
    }),
    responses={200: inline_serializer('VerifyOtpResponse', fields={
        'detail': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """POST /api/auth/verify-otp/ - Verify OTP and reset password"""
    # VULN(OTP Bruteforce): no rate limiting, no attempt counter, no expiry
    username = request.data.get('username', '')
    code = request.data.get('code', '')
    new_password = request.data.get('new_password', '')
    if not username or not code or not new_password:
        return Response({'detail': 'username, code, and new_password required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    otp = PasswordResetOTP.objects.filter(user=user, code=code, used=False).first()
    if not otp:
        return Response({'detail': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
    otp.used = True
    otp.save()
    user.set_password(new_password)
    user.save()
    return Response({'detail': 'Password reset successfully'})


@extend_schema(
    tags=['Tools'],
    summary='Download file',
    description='Download a file from the media directory (path traversal vector).',
    parameters=[
        OpenApiParameter('path', str, description='File path relative to media root'),
    ],
)
@api_view(['GET'])
@permission_classes([AllowAny])
def download_file(request):
    """GET /api/files/download/?path=... - Download a file"""
    # VULN(Path Traversal): user-supplied path with no sanitization
    file_path = request.query_params.get('path', '')
    if not file_path:
        return Response({'error': 'path required'}, status=status.HTTP_400_BAD_REQUEST)
    full_path = os.path.join(str(settings.MEDIA_ROOT), file_path)
    try:
        return FileResponse(open(full_path, 'rb'))
    except FileNotFoundError:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =====================================================================
#  Invoker Mini Game
# =====================================================================

INVOKER_SPELLS = {
    'Cold Snap': 'QQQ', 'Ghost Walk': 'QQW', 'Ice Wall': 'QQE',
    'EMP': 'WWW', 'Tornado': 'QWW', 'Alacrity': 'WWE',
    'Sun Strike': 'EEE', 'Forge Spirit': 'QEE', 'Chaos Meteor': 'WEE',
    'Deafening Blast': 'QWE',
}


def _sort_combo(c):
    order = {'Q': 0, 'W': 1, 'E': 2}
    return ''.join(sorted(c, key=lambda x: order.get(x, 9)))


@extend_schema(
    tags=['Tools'],
    summary='Submit Invoker game score',
    description='Submit game results. Server validates each spell/answer pair, calculates the real score, and rewards wallet balance. Reward = $1 per correct spell.',
    request=inline_serializer('GameSubmitRequest', fields={
        'spells': drf_serializers.ListField(
            child=inline_serializer('SpellAttempt', fields={
                'spell': drf_serializers.CharField(help_text='Spell name'),
                'answer': drf_serializers.CharField(help_text='3-char orb combo used (e.g. QQW)'),
                'correct': drf_serializers.BooleanField(),
            }),
            help_text='List of spell attempts in order',
        ),
    }),
    responses={200: inline_serializer('GameSubmitResponse', fields={
        'verified_score': drf_serializers.IntegerField(),
        'correct': drf_serializers.IntegerField(),
        'wrong': drf_serializers.IntegerField(),
        'reward': drf_serializers.CharField(),
        'new_balance': drf_serializers.CharField(),
    })},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_submit_score(request):
    """POST /api/game/submit/ - Validate game results and reward wallet balance"""
    spells = request.data.get('spells', [])
    if not isinstance(spells, list):
        return Response({'error': 'spells must be a list'}, status=status.HTTP_400_BAD_REQUEST)

    # VULN(Business Logic): No limit on how many spells can be submitted.
    # A user can fabricate a request with hundreds of correct spell entries
    # without actually playing, earning unlimited wallet balance.
    # Also no duplicate spell detection -- same spell can appear 100x.
    # Also no game session token -- endpoint can be called directly via curl.
    correct = 0
    wrong = 0
    for attempt in spells:
        spell_name = attempt.get('spell', '')
        answer = attempt.get('answer', '')
        expected = INVOKER_SPELLS.get(spell_name)
        if expected and _sort_combo(answer) == _sort_combo(expected):
            correct += 1
        else:
            wrong += 1

    reward = Decimal(str(correct))

    # VULN(Race Condition): No atomic transaction or select_for_update.
    # Concurrent submissions will read the same balance and each add reward,
    # multiplying the payout.
    wallet, _ = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
    time.sleep(1)
    wallet.balance += reward
    wallet.save()
    if reward > 0:
        WalletTransaction.objects.create(
            wallet=wallet, type='deposit', amount=reward,
            balance_after=wallet.balance,
            reference=f'Invoker Challenge: {correct} correct',
        )

    return Response({
        'verified_score': correct,
        'correct': correct,
        'wrong': wrong,
        'reward': str(reward),
        'new_balance': str(wallet.balance),
    })
