from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.http import HttpResponse , JsonResponse
from .models import TradeOrder , SupportMessage , BannerSet , SubscriptionItem , Subscription , Deposit , Profile , UserBankDetail , IdentityVerification , WithdrawalRequest
from django.db import transaction
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.db.models import Sum
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from functools import wraps
from .forms import TradeOrderForm , SubscriptionItemForm ,  BannerSetForm , AdminRegisterForm , WithdrawalRequestForm , DepositForm , UserBankDetailForm , PasswordResetForm , IdentityVerificationForm
from django.utils import timezone
from datetime import timedelta


def support_page(request):
    return render(request, 'index/support_page.html')







import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def fetch_price(request):
    symbol = request.GET.get('symbol', 'BTCUSDT')
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    try:
        response = requests.get(url)
        data = response.json()
        return JsonResponse({'price': data.get('price')})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)









def admin_required(function):
    @wraps(function)
    def _wrapped_view(request, *args, **kwargs):
        username = request.user.username.lower()
        
        # Check if 'admin' or 'employee' is in the username
        if not ('admin' in username ):
            return redirect('login')  # Redirect if neither 'admin' nor 'employee' is found in the username
        
        return function(request, *args, **kwargs)
    
    return _wrapped_view


def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists")

        user = User.objects.create_user(username=username, email=email, password=password)
        profile = user.profile  # Access via related name
        login(request, user)  # Login only if you want restricted access
        return redirect('home')
    return render(request, 'authentication/register.html')




def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        captcha_key = request.POST.get('captcha_0')
        captcha_value = request.POST.get('captcha_1')

        try:
            captcha = CaptchaStore.objects.get(hashkey=captcha_key)
            if captcha.response != captcha_value.lower():
                error = "Invalid CAPTCHA"
            else:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('home')
                else:
                    error = "Invalid username or password"
        except CaptchaStore.DoesNotExist:
            error = "CAPTCHA session expired"

    new_captcha = CaptchaStore.generate_key()
    image_url = captcha_image_url(new_captcha)

    return render(request, 'authentication/login.html', {
        'captcha_key': new_captcha,
        'captcha_image': image_url,
        'error': error
    })



def logout_view(request):
    logout(request)
    return redirect('login')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')



@login_required
def home_view(request):
    # Assuming you want to get the latest BannerSet entry
    banner_set = BannerSet.objects.order_by('-uploaded_at').first()
    return render(request, 'main/home.html', {'banner_set': banner_set})





def get_profit_percentage(expiry_time):
    return {
        120: Decimal("0.30"),
        180: Decimal("0.40"),
        300: Decimal("0.50"),
        360: Decimal("0.60")
    }.get(int(expiry_time), Decimal("0.00"))



@login_required
@transaction.atomic
def place_trade(request):
    if request.method == "POST":
        trading_pair = request.POST.get("trading_pair")
        direction = request.POST.get('direction')  # "up" or "down"

        # Handle amount input
        try:
            amount = Decimal(request.POST.get('custom_amount') or "0")
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid amount.'})

        # Handle expiry input
        try:
            expiry_time = int(request.POST.get("expiry_time") or 0)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid expiry time.'})

        # Fetch current price
        try:
            res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={trading_pair}")
            res.raise_for_status()
            locked_price = Decimal(res.json()['price'])  # ✅ Use Decimal not float
        except Exception as e:
            return JsonResponse({"success": False, "error": "Failed to fetch price"})

        # Validate trade inputs
        if amount <= 0 or expiry_time <= 0 or direction not in ["up", "down"]:
            return JsonResponse({'success': False, 'error': 'Invalid trade data.'})

        profile = Profile.objects.select_for_update().get(user=request.user)
        total_balance = profile.total_balance

        # Check if user has enough balance
        if total_balance < amount:
            return JsonResponse({'success': False, 'error': 'Insufficient balance'})

        # Deduct funds in order: credit → deposit → profit
        remaining = amount

        # First: Deduct from deposit
        if remaining > 0:
            if profile.total_deposit >= remaining:
                profile.total_deposit -= remaining
                remaining = 0
            else:
                remaining -= profile.total_deposit
                profile.total_deposit = 0

        # Then: Deduct remaining from profit
        if remaining > 0:
            if profile.total_profit >= remaining:
                profile.total_profit -= remaining
                remaining = 0
            else:
                return JsonResponse({'success': False, 'error': 'Not enough funds in deposit or profit'})

        profile.save()

        # Calculate profit values
        profit_percent = get_profit_percentage(expiry_time)
        potential_profit = round(amount * profit_percent, 2)
        yield_percent = profit_percent * 100  # Convert 0.3 → 30.0

        # ✅ Save trade order
        trade = TradeOrder.objects.create(
            user=request.user,
            pair=trading_pair,
            direction=direction,  # ✅ Keep as "up"/"down"
            amount=amount,
            expiry_time=expiry_time,
            balance=total_balance,
            potential_profit=potential_profit,
            yield_percent=yield_percent,
            entry_price=locked_price,
            expires_at=timezone.now() + timedelta(seconds=expiry_time),
            is_closed=False
        )

        return JsonResponse({
            'success': True,
            'trade_id': trade.id,
            'expires_at': trade.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
            'trade_end_timestamp': int(trade.expires_at.timestamp()),  # 🆕 optional
            'profit_added': str(potential_profit)
        })

    # Only GET request reaches here, no access to 'remaining'
    return render(request, "main/contract.html", {
        'expiry_options': [60, 120, 180, 300, 360],
        'quick_amounts': [10, 25, 50, 100, 250, 500, 1000],
    })





def submit_order(request):
    if request.method == "POST":
        form = TradeOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            return redirect('order_success') 
    return redirect('home')










@login_required
def user_trades(request):  
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    
    trades = TradeOrder.objects.filter(user=request.user).order_by('-created_at')
    profile, _ = Profile.objects.get_or_create(user=request.user)
    total_profit = round(profile.total_profit, 2)
    total_deposit = round(profile.total_deposit, 2)
    total_balance = round(profile.total_balance, 2)  # from @property

    paginator = Paginator(trades, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "main/assets.html", {
        "user_trades": page_obj,
        "total_deposit": total_deposit,
        "total_profit": total_profit,
        "total_balance": total_balance,
        "credit": profile.credit,
        "page_obj": page_obj,
    })








from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import TradeOrder

@login_required
def delete_trade(request, trade_id):
    trade = get_object_or_404(TradeOrder, id=trade_id, user=request.user)

    if request.method == "POST":
        trade.delete()
    
    return redirect('user_trades')  # or another relevant page









@login_required
def profile(request):
    pro = Profile.objects.filter(user=request.user)
    
    # Check if user has an approved verification
    is_verified = IdentityVerification.objects.filter(user=request.user, approved=True).exists()

    return render(request, 'main/profile.html', {
        'pro': pro,
        'user': request.user,
        'is_verified': is_verified,
    })


from decimal import Decimal
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from .models import TradeOrder, Profile

@login_required
def admin_manage_trades(request):
    if not request.user.is_staff:
        return redirect('home')

    search_query = request.GET.get("q", "").strip()

    if request.method == "POST":
        # Handle delete
        if 'delete_trade_id' in request.POST:
            trade_id = request.POST.get("delete_trade_id")
            trade = get_object_or_404(TradeOrder, id=trade_id)
            trade.delete()
            messages.success(request, f"Trade #{trade_id} deleted.")
            return redirect('admin_manage_trades')

        # Handle profit/loss marking
        trade_id = request.POST.get("trade_id")
        action = request.POST.get("action")

        if not trade_id or action not in ["profit", "loss"]:
            messages.error(request, "Invalid action.")
            return redirect('admin_manage_trades')

        trade = get_object_or_404(TradeOrder, id=trade_id)
        profile = get_object_or_404(Profile, user=trade.user)

        # Revert any previous result effect on user's balance
        if trade.result == "profit":
            profile.total_profit -= trade.amount + trade.manual_profit
        elif trade.result == "loss":
            pass  # Nothing to subtract for a loss

        # Apply new result
        if action == "profit":
            profit = (trade.amount * trade.yield_percent) / 100
            trade.manual_profit = profit
            profile.total_profit += profit
            trade.result = "profit"
        elif action == "loss":
            trade.manual_profit = Decimal('0.00')
            trade.yield_percent = Decimal('0.00')
            trade.result = "loss"

        trade.is_closed = True
        trade.save()
        profile.save()

        messages.success(request, f"Trade #{trade_id} marked as {action.upper()}.")
        return redirect('admin_manage_trades')

    trades = TradeOrder.objects.all().order_by('-created_at')
    
    if search_query:
        trades = trades.filter(Q(user__username__icontains=search_query))
    return render(request, "admins/manage_trades.html", {"trades": trades, "search_query":search_query})



@login_required
def verify_identity(request):
    if request.method == 'POST':
        try:
            instance = IdentityVerification.objects.get(user=request.user)
            form = IdentityVerificationForm(request.POST, request.FILES, instance=instance)
        except IdentityVerification.DoesNotExist:
            form = IdentityVerificationForm(request.POST, request.FILES)
        
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            return redirect('profile')
    else:
        try:
            instance = IdentityVerification.objects.get(user=request.user)
            form = IdentityVerificationForm(instance=instance)
        except IdentityVerification.DoesNotExist:
            form = IdentityVerificationForm()

    return render(request, 'index/identity.html', {'form': form})






def verification_list(request):
    query = request.GET.get('q', '')
    verifications = IdentityVerification.objects.select_related('user')

    if query:
        verifications = verifications.filter(user__username__icontains=query)

    verifications = verifications.order_by('-submitted_at')
    paginator = Paginator(verifications, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'index/approve_id.html', {
        'verifications': page_obj,
        'query': query,
        'page_obj': page_obj
    })




def approve_verification(request, pk):
    verification = get_object_or_404(IdentityVerification, pk=pk)
    verification.approved = True
    verification.save()
    return redirect('verification_list')



def real_name_auth(request):
    return render(request , 'index/real_name_auth.html')



def reset_password_view(request):
    if request.method == 'POST':
        form = PasswordResetForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Keeps user logged in
            messages.success(request, 'Your password has been updated successfully.')
            return redirect('profile')
    else:
        form = PasswordResetForm(user=request.user)

    return render(request, 'index/reset_password.html', {'form': form})




def bank_detail_view(request):
    try:
        instance = request.user.userbankdetail
    except UserBankDetail.DoesNotExist:
        instance = None

    if request.method == 'POST':
        form = UserBankDetailForm(request.POST, instance=instance)
        if form.is_valid():
            bank_detail = form.save(commit=False)
            bank_detail.user = request.user
            bank_detail.save()
            return redirect('profile')  # Redirect where appropriate
    else:
        form = UserBankDetailForm(instance=instance)

    return render(request, 'index/bank_detail.html', {'form': form, 'bank': instance})





def approve_bank_detail(request, pk):
    bank = get_object_or_404(UserBankDetail, pk=pk)
    bank.is_verified = True
    bank.save()
    return redirect('bank_detail')




def deposit_create_view(request):
    if request.method == 'POST':
        form = DepositForm(request.POST, request.FILES)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.user = request.user
            deposit.save()
            return redirect('deposit_list')
    else:
        form = DepositForm()
    return render(request, 'index/deposit_form.html', {'form': form})



def deposit_list_view(request):
    deposits = Deposit.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'index/deposit_list.html', {'deposits': deposits})




def admin_deposit_list_view(request):
    search_query = request.GET.get('search', '')
    deposits = Deposit.objects.all().order_by('-created_at')

    if search_query:
        deposits = deposits.filter(user__username__icontains=search_query)

    paginator = Paginator(deposits, 5)  # Show 5 deposits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'deposits': page_obj,
        'search_query': search_query,
    }
    return render(request, 'admins/admin_deposit_list.html', context)



def deposit_approve(request, pk):
    deposit = get_object_or_404(Deposit, pk=pk)
    deposit.is_approved = True
    deposit.save()
    messages.success(request, f'Deposit #{deposit.id} approved successfully.')
    return redirect('deposit_list')





def request_withdrawal(request):
    if request.method == 'POST':
        form = WithdrawalRequestForm(request.POST, user=request.user)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.user = request.user
            withdrawal.save()
            messages.success(request, "Withdrawal request submitted successfully.")
            return redirect('withdrawal_success')
    else:
        form = WithdrawalRequestForm(user=request.user)

    return render(request, 'index/withdrawal_form.html', {'form': form})



def withdrawal_list(request):
    withdrawals = WithdrawalRequest.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(withdrawals, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'index/withdrawal_list.html', {'withdrawal': page_obj})




def admin_withdrawal_list(request):
    search_query = request.GET.get('search', '')
    withdrawals = WithdrawalRequest.objects.all().order_by('-created_at')

    if search_query:
        withdrawals = withdrawals.filter(
            Q(user__username__icontains=search_query)
        )

    paginator = Paginator(withdrawals, 10)  # 10 per page
    page = request.GET.get('page')
    withdrawals_page = paginator.get_page(page)

    return render(request, 'admins/admin_withdrawal_list.html', {
        'withdrawals': withdrawals_page
    })






def set_withdrawal_password(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        if password != confirm:
            messages.error(request, "Passwords do not match.")
        else:
            profile = request.user.profile
            profile.set_withdrawal_password(password)
            profile.save()
            messages.success(request, "Withdrawal password set successfully.")
            return redirect('profile')  # or wherever you want
    return render(request, 'index/change_withdrawal_password.html')






def real_market(request):
    return render(request , 'main/market.html')






from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import TradeOrder, Profile

@transaction.atomic
def mark_trade_result(request, trade_id, outcome):
    trade = get_object_or_404(TradeOrder, id=trade_id)
    profile = trade.user.profile

    # ✅ Exit early if already handled
    if trade.result_handled:
        messages.warning(request, "This trade was already handled.")
        return redirect('admin_manage_trades')

    # ✅ Revert previous automatic result
    if trade.actual_result == "profit":
        reversal = trade.amount + trade.manual_profit
        profile.account_balance -= reversal
        profile.total_profit -= trade.manual_profit
    elif trade.actual_result == "loss":
        profile.account_balance += trade.amount  # refund amount lost

    # ✅ Apply admin override
    if outcome == "profit":
        profit = (trade.amount * trade.yield_percent) / 100
        profile.account_balance += trade.amount + profit
        profile.total_profit += profit
        trade.result = "profit"
        trade.manual_profit = profit
    elif outcome == "loss":
        profile.account_balance -= trade.amount
        trade.result = "loss"
        trade.manual_profit = Decimal('0.00')
        trade.yield_percent = Decimal('0.00')

    trade.result_handled = True
    profile.save()
    trade.save()

    messages.success(request, f"Trade marked as {outcome}.")
    return redirect("admin_manage_trades")








from decimal import Decimal
import requests
from django.utils import timezone

def get_current_price(pair):
    try:
        symbol = pair.replace("/", "")  # e.g. BTC/USDT → BTCUSDT
        res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
        res.raise_for_status()
        return Decimal(res.json()['price'])
    except Exception as e:
        print(f"Error fetching price for {pair}: {e}")
        return None






from decimal import Decimal
from .models import TradeOrder, Profile

def handle_trade_expiry(trade):
    if trade.is_closed:
        return  # Prevent reprocessing

    profile = trade.user.profile

    # Prices
    entry_price = trade.entry_price
    expiry_price = get_current_price(trade.pair)
    direction = trade.direction

    # Save exit price
    trade.exit_price = expiry_price

    # Determine result
    if (direction == "up" and expiry_price > entry_price) or (direction == "down" and expiry_price < entry_price):
        result = "profit"
        profit = (trade.amount * trade.yield_percent) / 100
        total_profit = trade.amount + profit

        # ✅ Update fields on profit
        profile.total_profit += total_profit
        trade.manual_profit = profit
    else:
        result = "loss"
    trade.result = result
    profile.save()
    trade.save()








from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import TradeOrder

@login_required
def check_trade_result(request, trade_id):
    trade = get_object_or_404(TradeOrder, id=trade_id, user=request.user)
    handle_trade_expiry(trade)
    return JsonResponse({
        'success': True,
        'result': trade.result,
        'profit': str(trade.manual_profit),
        'amount': str(trade.amount),
        'entry_price': str(trade.entry_price),
        'exit_price': str(trade.exit_price),
    })








def trade_review_admin(request):
    trades = TradeOrder.objects.all().order_by('-created_at')
    return render(request, 'admins/trade_review.html', {'trades': trades})






@staff_member_required
def admin_dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, 'admins/dashboard.html')



def trade_review_admin(request):
    query = request.GET.get('q', '')
    
    trades = TradeOrder.objects.select_related('user').order_by('-created_at')
    if query:
        trades = trades.filter(user__username__icontains=query)
    
    paginator = Paginator(trades, 10)  # 10 trades per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'trades': page_obj,
        'query': query,
        'page_obj': page_obj
    }
    return render(request, 'admins/trade_review.html', context)





@login_required
@transaction.atomic
def mark_trade_result(request, trade_id, outcome):
    trade = get_object_or_404(TradeOrder, id=trade_id)
    profile = trade.user.profile

    # ✅ Step 1: Revert previous result if already handled
    if trade.result_handled:
        if trade.result == "profit":
            # Remove previously added profit and amount
            profile.total_profit -= trade.manual_profit

        elif trade.result == "loss":
            pass

    # ✅ Step 2: Apply new result
    if outcome == "profit":
        profit = (trade.amount * trade.yield_percent) / 100
        profile.total_balance += trade.amount + profit
        profile.total_profit += profit
        trade.result = "profit"
        trade.manual_profit = profit

    elif outcome == "loss":
        # Do NOT deduct amount again — it was already deducted at trade placement
        trade.result = "loss"
        trade.manual_profit = Decimal('0.00')
        trade.yield_percent = Decimal('0.00')

    trade.result_handled = True
    profile.save()
    trade.save()

    messages.success(request, f"Trade successfully marked as {outcome}.")
    return redirect("admin_manage_trades")







def admin_deposit_list(request):
    query = request.GET.get('q', '')
    deposits = Deposit.objects.filter(is_approved=False).order_by('-created_at')

    if query:
        deposits = deposits.filter(Q(user__username__icontains=query))

    paginator = Paginator(deposits, 10)  # Show 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admins/deposit_review.html', {
        'page_obj': page_obj,
        'query': query
    })




def approve_deposit(request, deposit_id):
    deposit = get_object_or_404(Deposit, id=deposit_id)
    deposit.is_approved = True
    deposit.save()

    profile, _ = Profile.objects.get_or_create(user=deposit.user)
    total = Deposit.objects.filter(user=deposit.user, is_approved=True).aggregate(Sum('amount'))['amount__sum'] or 0
    profile.total_deposit = total
    profile.save()

    messages.success(request, "Deposit approved and balance updated.")
    return redirect('admin_deposits')




def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            Profile.objects.get_or_create(user=user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid credentials or not authorized.")

    return render(request, "admins/admin_login.html")



from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from .forms import AdminRegisterForm
from django.shortcuts import render, redirect

def admin_register_view(request):
    if request.method == 'POST':
        form = AdminRegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_staff = True  # ✅ Mark user as admin/staff
            user.save()

            messages.success(request, 'Admin registered successfully!')
            return redirect('admin_login')
    else:
        form = AdminRegisterForm()

    return render(request, 'admins/admin_register.html', {'form': form})






@staff_member_required
def all_admins_view(request):
    admins = User.objects.filter(is_staff=True)
    if not admins.exists():
        return redirect('admin_register')
    return render(request, 'admins/all_admins.html', {'admins': admins})





@staff_member_required
def delete_admin_view(request, admin_id):
    admin_user = get_object_or_404(User, id=admin_id, is_staff=True)
    
    if request.user == admin_user:
        messages.error(request, "You can't delete yourself.")
    else:
        admin_user.delete()
        messages.success(request, "Admin deleted successfully.")

    return redirect('all_admins')






def create_subscription_item(request):
    if request.method == 'POST':
        form = SubscriptionItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('subscription_list')  # Or wherever you list items
    else:
        form = SubscriptionItemForm()
    
    return render(request, 'index/create_subscriptions.html', {'form': form})



def subscribe_to_item(request, item_id):
    item = get_object_or_404(SubscriptionItem, id=item_id, is_active=True)

    # Check if user already subscribed
    already_subscribed = Subscription.objects.filter(user=request.user, item=item).exists()
    if already_subscribed:
        messages.warning(request, "You are already subscribed to this item.")
    else:
        Subscription.objects.create(user=request.user, item=item)
        messages.success(request, f"Successfully subscribed to {item.name}.")

    return redirect('subscription_list')  # Or the page you want to redirect back to




def subscription_list(request):
    items = SubscriptionItem.objects.filter(is_active=True)
    subscribed_item_ids = []

    if request.user.is_authenticated:
        subscribed_item_ids = list(
            Subscription.objects.filter(user=request.user).values_list('item_id', flat=True)
        )

    return render(request, 'index/subscription_list.html', {
        'items': items,
        'subscribed_item_ids': subscribed_item_ids
    })



@require_POST
def update_trade_profit(request, trade_id):
    trade = get_object_or_404(TradeOrder, id=trade_id)

    try:
        manual_profit = Decimal(request.POST.get('manual_profit'))
    except (ValueError, TypeError):
        manual_profit = Decimal('0.00')

    trade.manual_profit = manual_profit
    trade.save()

    with transaction.atomic():
        profile = Profile.objects.select_for_update().get(user=trade.user)
        profile.total_profit += manual_profit
        profile.save()

    return redirect('admin_trades')





from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from django.shortcuts import get_object_or_404, redirect, render
from .models import Profile
from django.contrib.auth.models import User

@staff_member_required
def all_users_view(request):
    query = request.GET.get('q', '')

    # Exclude staff/admin accounts
    profiles = Profile.objects.select_related('user') \
        .filter(user__is_staff=False, user__is_superuser=False) \
        .filter(Q(user__username__icontains=query)) \
        .order_by('-user__date_joined')

    paginator = Paginator(profiles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        action = request.POST.get('action')
        profile = get_object_or_404(Profile, id=profile_id)

        if action == 'delete':
            user = profile.user
            username = user.username
            user.delete()
            messages.success(request, f"User '{username}' deleted successfully.")
            return redirect('all_users')
        
        elif action == "reset":
            profile_id = request.POST.get("profile_id")
            profile = get_object_or_404(Profile, id=profile_id)
            profile.credit = 0
            profile.total_profit = 0
            profile.total_deposit = 0
            profile.save()
            messages.success(request, f"{profile.user.username}'s balance has been reset.")
            return redirect('all_users')  # ✅ This line fixes the refresh issue


        elif action == 'update':
            updated_fields = []
            try:
                credit = request.POST.get('credit')
                if credit is not None:
                    credit_decimal = Decimal(credit)
                    if credit_decimal != profile.credit:
                        profile.credit += credit_decimal
                        updated_fields.append("Credit")

                profit = request.POST.get('total_profit')
                if profit is not None:
                    profit_decimal = Decimal(profit)
                    if profit_decimal != profile.total_profit:
                        profile.total_profit += profit_decimal
                        updated_fields.append("Profit")

                deposit = request.POST.get('total_deposit')
                if deposit is not None:
                    deposit_decimal = Decimal(deposit)
                    if deposit_decimal != profile.total_deposit:
                        profile.total_deposit += deposit_decimal
                        updated_fields.append("Deposit")

                if updated_fields:
                    profile.save()
                    messages.success(
                        request,
                        f"{profile.user.username}'s " +
                        ", ".join(updated_fields) +
                        " updated successfully."
                    )
                else:
                    messages.info(request, "No changes detected for this user.")
            except (InvalidOperation, ValueError, TypeError):
                messages.error(request, "Invalid input detected. Please enter valid numbers.")

    return render(request, 'admins/all_users.html', {
        'page_obj': page_obj,
        'query': query,
    })


def admin_invite_list(request):
    pending_profiles = Profile.objects.filter(is_approved=False)
    return render(request, 'admins/invite_list.html', {'profiles': pending_profiles})



def approve_user(request, profile_id):
    profile = Profile.objects.get(id=profile_id)
    profile.save()
    return redirect('admin_invite_list')




def language_page(request):
    return render(request, 'index/language.html')




def upload_banner_set(request):
    if request.method == 'POST':
        form = BannerSetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('upload_banner_set')  # Change to your preview url
    else:
        form = BannerSetForm()
    return render(request, 'admins/upload_banner.html', {'form': form})





def support_chat(request):
    admin_users = User.objects.filter(username__istartswith='admin').exclude(id=request.user.id)
    selected_admin_id = request.GET.get('admin_id')
    selected_admin = get_object_or_404(User, id=selected_admin_id) if selected_admin_id else None

    messages = []
    if selected_admin:
        messages = SupportMessage.objects.filter(
            Q(sender=request.user, receiver=selected_admin) |
            Q(sender=selected_admin, receiver=request.user)
        ).order_by('timestamp')

        if request.method == 'POST':
            message = request.POST.get('message')
            if message:
                SupportMessage.objects.create(
                    sender=request.user,
                    receiver=selected_admin,
                    message=message
                )
                return redirect(f"{request.path}?admin_id={selected_admin.id}")

    return render(request, 'index/chat.html', {
        'admin_users': admin_users,
        'selected_admin': selected_admin,
        'messages': messages
    })




def admin_chat_with_user(request, user_id):
    if not request.user.is_staff:
        return redirect('home')

    user = get_object_or_404(User, id=user_id)
    messages = SupportMessage.objects.filter(
        Q(sender=user, receiver=request.user) |
        Q(sender=request.user, receiver=user)
    ).order_by('timestamp')

    if request.method == 'POST':
        msg = request.POST.get('message')
        if msg:
            SupportMessage.objects.create(
                sender=request.user,
                receiver=user,
                message=msg
            )
            return redirect('admin_chat_with_user', user_id=user.id)

    return render(request, 'admins/chat_admin.html', {'messages': messages, 'user': user})




def admin_support_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    query = request.GET.get('q', '')
    users = User.objects.filter(
        Q(sent_messages__receiver=request.user) |
        Q(received_messages__sender=request.user)
    ).distinct()

    if query:
        users = users.filter(username__icontains=query)

    paginator = Paginator(users, 10)  # 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admins/admin_chat.html', {
        'users': page_obj.object_list,
        'page_obj': page_obj,
        'query': query
    })



def mining(request):
    return render(request , 'main/mining.html')


def staking(request):
    return render(request , 'index/staking.html')