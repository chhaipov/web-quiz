"""
Template Views - Cookie/Session Auth (Django templates)
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.template import Template, Context
from django.http import HttpResponse

from .models import Dota2Item, Cart, CartItem, Order, Review
from .forms import RegisterForm


def landing(request):
    return render(request, 'shop/landing.html')


class ShopLoginView(LoginView):
    template_name = 'shop/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('shop:items')


class ShopLogoutView(LogoutView):
    next_page = reverse_lazy('shop:landing')


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'shop/register.html'
    success_url = reverse_lazy('shop:items')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Account created successfully.')
        return redirect(self.success_url)


def items_list(request):
    items = Dota2Item.objects.filter(is_active=True)
    rarity = request.GET.get('rarity', '')
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    if rarity:
        items = items.filter(rarity=rarity)
    if category:
        items = items.filter(category=category)
    if search:
        items = items.filter(name__icontains=search)
    return render(request, 'shop/items_list.html', {
        'items': items,
        'filter_rarity': rarity,
        'filter_category': category,
        'search_query': search,
    })


def item_detail(request, pk):
    item = get_object_or_404(Dota2Item, pk=pk, is_active=True)
    reviews = item.reviews.select_related('user').all()
    if request.method == 'POST' and request.user.is_authenticated:
        text = request.POST.get('text', '')
        rating = request.POST.get('rating', 5)
        if text:
            Review.objects.update_or_create(
                item=item, user=request.user,
                defaults={'text': text, 'rating': int(rating)},
            )
            messages.success(request, 'Review submitted.')
            return redirect('shop:item_detail', pk=pk)
    return render(request, 'shop/item_detail.html', {'item': item, 'reviews': reviews})


@login_required
@require_http_methods(['POST'])
def cart_add(request):
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1) or 1)
    item = get_object_or_404(Dota2Item, id=item_id, is_active=True)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    ci, created = CartItem.objects.get_or_create(cart=cart, item=item, defaults={'quantity': quantity})
    if not created:
        ci.quantity += quantity
        ci.save()
    messages.success(request, f'Added {item.name} to cart.')
    return redirect('shop:items')


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.cart_items.select_related('item').all()
    total = sum(ci.subtotal for ci in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total': total})


@login_required
@require_http_methods(['POST'])
def cart_update(request, pk):
    ci = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    q = int(request.POST.get('quantity', 1) or 1)
    if q <= 0:
        ci.delete()
        messages.success(request, 'Item removed from cart.')
    else:
        ci.quantity = q
        ci.save()
        messages.success(request, 'Cart updated.')
    return redirect('shop:cart')


@login_required
@require_http_methods(['POST'])
def cart_remove(request, pk):
    ci = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    ci.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('shop:cart')


@login_required
@require_http_methods(['POST'])
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = list(cart.cart_items.select_related('item').all())
    if not items:
        messages.error(request, 'Your cart is empty.')
        return redirect('shop:cart')
    total = sum(ci.item.usd_price * ci.quantity for ci in items)
    order = Order.objects.create(user=request.user, total=total)
    for ci in items:
        order.order_items.create(item=ci.item, quantity=ci.quantity, price_snapshot=ci.item.usd_price)
    cart.cart_items.all().delete()
    messages.success(request, f'Order #{order.id} placed successfully!')
    return redirect('shop:orders')


@login_required
def orders_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('order_items__item').order_by('-created_at')
    return render(request, 'shop/orders_list.html', {'orders': orders})


# VULN(CSRF): profile change with no CSRF protection
@login_required
@csrf_exempt
def profile_edit(request):
    """Profile edit page — CSRF protection intentionally disabled"""
    user = request.user
    if request.method == 'POST':
        username = request.POST.get('username', user.username)
        email = request.POST.get('email', user.email)
        user.username = username
        user.email = email
        user.save()
        messages.success(request, 'Profile updated.')
        return redirect('shop:profile')
    return render(request, 'shop/profile.html', {'profile_user': user})


# VULN(SSTI): renders user-supplied template string through Django's template engine
def template_preview(request):
    """Render user-supplied template — for "preview" feature"""
    template_str = request.GET.get('tpl', 'Hello {{ user.username }}!')
    try:
        t = Template(template_str)
        c = Context({'user': request.user, 'request': request})
        rendered = t.render(c)
    except Exception as e:
        rendered = f'Error: {e}'
    return render(request, 'shop/preview.html', {'rendered': rendered, 'template_str': template_str})
