from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.checks import messages
from django.db.models import Sum
from django.http import HttpResponse, request
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, View

from .models import Cart, CartItem, Customer, Item


def init_cart(request: request.HttpRequest):
    try:
        cart_id = request.session["cart_id"]
        cart = Cart.objects.get(pk=cart_id)
    except (KeyError, Cart.DoesNotExist):
        cart = Cart.objects.create()
        cart.save()
        request.session["cart_id"] = cart.id
    count = CartItem.objects.filter(cart=cart).aggregate(Sum("quantity"))[
        "quantity__sum"
    ]
    total_cart_items = count if count else 0
    return cart, total_cart_items


def add_to_cart(request, pk):
    cart, total_cart_items = init_cart(request)
    item = get_object_or_404(Item, pk=pk)

    try:
        cart_item = CartItem.objects.get(item=item, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(item=item, cart=cart)
    return redirect("home:home")


# delete item from cart
def remove_from_cart(request, pk):
    cart, total_cart_items = init_cart(request)
    item = get_object_or_404(Item, pk=pk)

    try:
        cart_item = CartItem.objects.get(item_id=item, cart=cart)
        item_count = cart_item.quantity
        if item_count == 1:
            cart_item.delete()
            pass
        else:
            cart_item.quantity -= 1
            cart_item.save()
    except CartItem.DoesNotExist:
        pass
    return redirect("home:cart")


class HomeView(ListView):
    def get(self, *args, **kwargs):
        cart, total_cart_items = init_cart(self.request)
        context = {
            "items": Item.objects.all(),
            "cart_item_count": total_cart_items,
        }
        return render(self.request, "home.html", context)


class CartView(ListView):
    def get(self, *args, **kwargs):
        cart, total_cart_items = init_cart(self.request)
        context = {
            "cartItems": CartItem.objects.filter(cart=cart),
        }
        return render(self.request, "cart.html", context)


class SignupView(View):
    def get(self, *args, **kwargs):
        cart, total_cart_items = init_cart(self.request)
        context = {
            "cart_item_count": total_cart_items,
        }
        return render(self.request, "signup.html", context)

    def post(self, *args, **kwargs):
        name = self.request.POST.get("name")
        email = self.request.POST.get("email")
        password = self.request.POST.get("password")

        cart = init_cart(self.request)
        user = User.objects.create(username=email, password=password, first_name=name)
        user.save()
        customer = Customer.objects.create(user=user, cart=cart)
        return redirect("home:login")


class LoginView(View):
    def get(self, *args, **kwargs):
        cart, total_cart_items = init_cart(self.request)
        context = {
            "cart_item_count": total_cart_items,
        }
        return render(self.request, "login.html", context)

    def post(self, *args, **kwargs):
        email = self.request.POST.get("email")
        password = self.request.POST.get("password")
        print(email, password)

        user = authenticate(username=email, password=password)

        if user is None:
            # auth err
            return redirect("home:login")

        # just for now
        # return redirect("home:home")

        # make a logic to merge carts
        customer = Customer.objects.get(user=user)
        cust_cart = customer.cart

        # edge case
        if not cust_cart:
            cust_cart = Cart.objects.create()
            cust_cart.save()
            customer.cart = cust_cart
            customer.save()

        cart = init_cart(self.request)
        cart_items = CartItem.objects.filter(cart=cart)
        for cart_item in cart_items:
            try:
                cust_cart_item = CartItem.objects.get(
                    item=cart_item.item, cart=cust_cart
                )
                cust_cart_item.quantity += 1
                cust_cart_item.save()
                # delete item from temp cart
            except CartItem.DoesNotExist:
                cart_item.cart = cust_cart
                cart_item.save()

        return redirect("home:home")
