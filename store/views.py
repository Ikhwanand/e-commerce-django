from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Order, OrderItem, Favorite
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from .forms import SearchForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




# Create your views here.
def product_list(request):
    products = Product.objects.all()
    form = SearchForm(request.GET or None)
    if form.is_valid():
        query = form.cleaned_data.get('query')
        products = products.filter(name__icontains=query)
    
    paginator = Paginator(products, 9) # Show 9 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
        
    return render(request, 'store/product_list.html', {
        'products': products,
        'form': form,
    })
    

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'store/product_detail.html', {
        'product': product
    })
    
@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order, created = Order.objects.get_or_create(user=request.user, status='Pending')
    order_item, item_created = OrderItem.objects.get_or_create(order=order, product=product)
    if not item_created:
        order_item.quantity += 1
        order_item.save()
    return redirect('store:cart')

@login_required
def remove_from_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    order = Order.objects.filter(user=request.user, status='Pending').first()
    if order:
        order_item = OrderItem.objects.filter(order=order, product=product).first()
        if order_item:
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
    return redirect('store:cart')


@login_required
def cart(request):
    order = Order.objects.filter(user=request.user, status='Pending').first()
    return render(request, 'store/cart.html', {
        'order': order
    })
    

@login_required
def checkout(request):
    order = Order.objects.filter(user=request.user, status='Pending').first()
    if request.method == 'POST':
        stripe.api_key = settings.STRIPE_SECRET_KEY
        token = request.POST.get('stripeToken')
        try:
            charge = stripe.Charge.create(
                amount=int(order.get_total_cost() * 100),
                currency='usd',
                description='Purchase',
                source=token,
            )
            order.status = 'Paid'
            order.save()
            return render(request, 'store/success.html')
        except stripe.error.CardError as e:
            return render(request, 'store/error.html', {
                'error': e
            })
    return render(request, 'store/checkout.html', {
        'order': order
    })
    
    
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).exclude(status='Pending')
    return render(request, 'store/order_history.html', {
        'orders': orders
    })
    

@login_required
def add_to_favorites(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect('store:product_detail', pk=pk)


@login_required
def remove_from_favorites(request, pk):
    product = get_object_or_404(Product, pk=pk)
    Favorite.objects.filter(user=request.user, product=product).delete()
    return redirect('store:product_detail', pk=pk)

@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'store/favorites_list.html', {
        'favorites': favorites
    })