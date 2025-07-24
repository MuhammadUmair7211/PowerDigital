from django.db import models
import uuid
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password, check_password


class TradeOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pair = models.CharField(max_length=20)
    direction = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    expiry_time = models.IntegerField()
    balance = models.DecimalField(max_digits=20, decimal_places=8)
    potential_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    expires_at = models.DateTimeField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    yield_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    manual_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    @property
    def single_trade(self):
        return (self.yield_percent or 0) + (self.manual_profit or 0)



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    withdrawal_password = models.CharField(max_length=128)
    total_deposit = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    total_profit = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    credit = models.DecimalField(default=0, max_digits=12, decimal_places=2)
    invite_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = str(uuid.uuid4()).split('-')[0]
        super().save(*args, **kwargs)

    @property
    def total_balance(self):
        return self.total_deposit + self.total_profit + self.credit

    def set_withdrawal_password(self, raw_password):
        self.withdrawal_password = make_password(raw_password)

    def check_withdrawal_password(self, raw_password):
        return check_password(raw_password, self.withdrawal_password)

    def __str__(self):
        return self.user.username




    


class IdentityVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    id_card_front = models.ImageField(upload_to='id_cards/front/')
    id_card_back = models.ImageField(upload_to='id_cards/back/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification for {self.user.username}"
    


class PasswordResetRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)



class UserBankDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bank_type = models.CharField(max_length=100)
    bank_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email}'s Bank Detail"





User = get_user_model()

class Deposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deposits')
    currency = models.CharField(max_length=10, choices=[
        ('USDT', 'USDT'),
        ('BTC', 'BTC'),
        ('ETH', 'ETH'),
        ('TRX', 'TRX'),
        ('ETC', 'ETC'),
        ('BNB', 'BNB'),
        ('DOGE', 'DOGE'),
        ('DOT', 'DOT'),
        ('APT', 'APT'),
        ('TON', 'TON'),
        ('ICP', 'ICP'),
        ('SHIB', 'SHIB'),
        ('ITC', 'ITC'),
        ('HT', 'HT'),
      
    ])
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    payment_proof = models.ImageField(upload_to='deposits/')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.currency} - {self.amount}"
    


class WithdrawalAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    address = models.CharField(max_length=255)
    network = models.CharField(max_length=50, choices=[('TRC20', 'TRC20'), ('ERC20', 'ERC20')])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)



class WithdrawalRequest(models.Model):

    CURRENCY_CHOICES = [
        ('USDT', 'USDT'),
        ('BTC', 'BTC'),
        ('ETH', 'ETH'),
        ('TRX', 'TRX'),
        ('ETC', 'ETC'),
        ('BNB', 'BNB'),
        ('DOGE', 'DOGE'),
        ('DOT', 'DOT'),
        ('APT', 'APT'),
        ('TON', 'TON'),
        ('ICP', 'ICP'),
        ('SHIB', 'SHIB'),
        ('ITC', 'ITC'),
        ('HT', 'HT'),
    ]

    NETWORK_CHOICES = [
        ('TRC20', 'TRC20'),
        ('ERC20', 'ERC20'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.CharField(max_length=10, choices=CURRENCY_CHOICES)
    address = models.CharField(max_length=255)
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.network}"




class SubscriptionItem(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='subscriptions/')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available_from = models.DateTimeField()
    available_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    



class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey('SubscriptionItem', on_delete=models.CASCADE)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} subscribed to {self.item.name}"




class BannerSet(models.Model):
    banner1 = models.ImageField(upload_to='banners/', null=True, blank=True)
    banner2 = models.ImageField(upload_to='banners/', null=True, blank=True)
    banner3 = models.ImageField(upload_to='banners/', null=True, blank=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Banner Set {self.id}"





class SupportMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}: {self.message[:30]}"