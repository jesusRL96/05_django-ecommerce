from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from .models import Item, OrderItem, Order, BillingAddress, Payment, Coupon
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib import messages
from .forms import CheckoutForm, CouponForm
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import stripe
# stripe.api_key = settings.STRIPE_SECRET_KEY


# Create your views here.
class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home-page.html"


class CheckoutView(View):
    def get(self, *args, **kwargs):
        # form
        form = CheckoutForm()
        form_coupon = CouponForm
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
            'form': form,
            'order': order,
            'form_coupon': form_coupon,
            'DISPLAY_COUPON_FORM': True,
            }
            return render(self.request,"checkout-page.html", context)
        except ObjectDoesNotExist:
            messages.info(request, "You do not have an active order")
            return redirect('core:home')
        
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                save_info = form.cleaned_data.get('save_info')
                payment_options = form.cleaned_data.get('payment_options')
                
                billing_address = BillingAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                if payment_options == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_options == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request,"Invalid payment option")
                    return redirect('core:check_out')
            messages.warning(self.request,"Failed checkout")
            return redirect('core:check_out')
        except ObjectDoesNotExist:
            messages.error(self.request, "you do not have an active order")
            return redirect("core:order_summary")
    
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM': False,
            }
            return render(self.request, "payment.html", context=context)
        else:
            messages.error(self.request, "You have not added a builling address")
            return redirect('core:check_out')
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        amount = int(order.get_total() * 100)    # cents
        token = self.request.POST.get('stripeToken')
        stripe.api_key = 'sk_test_51Hu8yEA1Ibmmqdn5mUfbdFYPBN6Tb00xHweRDYmQHG2lCDkSPIQ27jVk6V7emyHuVrgKQHuRbFlIbBQdZaIELNgg00CbBAEkph'
        try:
            # Use Stripe's library to make requests...            
            # `source` is obtained with Stripe.js; see https://stripe.com/docs/payments/accept-a-payment-charges#web-create-token
            charge = stripe.Charge.create(
                amount= amount,
                currency='usd',
                description='Example charge',
                source=token,
            )
            # create payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = order.get_total()
            payment.save()
            # assign to the order
            # set ordered items to true
            ordered_items = order.items.all()
            ordered_items.update(ordered=True)
            (item.save for item in ordered_items)
            order.ordered = True
            order.payment = payment
            order.save()
            messages.success(self.request, "the order was succesful")
            return redirect("/")
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            # print('Status is: %s' % e.http_status)
            # print('Code is: %s' % e.code)
            # # param is '' in this case
            # print('Param is: %s' % e.param)
            # print('Message is: %s' % e.user_message)
            messages.error(self.request, f"{e.user_message}")
            return redirect("/")
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, "Rate limit Error")
            return redirect("/")
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, "Invalid request error")
            return redirect("/")
        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request, "Youre not authenticated")
            return redirect("/")
        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, "Connection error")
            return redirect("/")
        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, "Something went wrong")
            return redirect("/")
        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            messages.error(self.request, "Seriour error")
            return redirect("/")


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {'object': order}
        except ObjectDoesNotExist:
            messages.error(self.request, "you do not have an active order")
            return redirect("/")
        return render(self.request, 'order_summary.html', context=context)

class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()   
            order.items.add(order_item)
            messages.info(request, "This item quantity's was updated")     
            return redirect("core:order_summary")    
        else:
            messages.info(request, "This item was added into your cart")
            order.items.add(order_item)
            return redirect("core:order_summary")
    else:
        oredered_date = timezone.now()
        order = Order.objects.create(user=request.user, oredered_date=oredered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added into your cart")
        return redirect("core:product",slug=slug)
    
@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists:
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart")
            
            return redirect("core:order_summary")
        else:
            
            messages.info(request, "This item was not in your cart")
            return redirect("core:product",slug=slug)
    else:
        # add a message saying the order does not exists
        messages.info(request, "You do not have an active order")
        return redirect("core:product",slug=slug)

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists:
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity >1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order_item.delete()
            messages.info(request, "This item was updated")
            
            return redirect("core:order_summary")
        else:
            
            messages.info(request, "This item was not in your cart")
            return redirect("core:order_summary")
    else:
        # add a message saying the order does not exists
        messages.info(request, "You do not have an active order")
        return redirect("core:product",slug=slug)

# handle coupon
def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon

    except ObjectDoesNotExist:
        messages.info(request, "This Coupon does not exist")
        return redirect('core:check_out')

class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Coupon succesfully added")
                return redirect('core:check_out')

            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect('core:check_out')
        
        # TODO: raise an error
        return None
        