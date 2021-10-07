from django.urls import path
from .views import (
    HomeView, 
    ItemDetailView,
    CheckoutView,
    add_to_cart,
    remove_from_cart,
    OrderSummaryView,
    remove_single_item_from_cart,
    PaymentView,
    AddCouponView,
    )
app_name = 'core'
urlpatterns = [
    path('', HomeView.as_view(), name='item_list'),
    path('check-out/', CheckoutView.as_view(), name='check_out'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('order-summary/', OrderSummaryView.as_view(), name='order_summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('add-coupon/', AddCouponView.as_view, name='add_coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('remove-single-item-from-cart/<slug>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),
]