from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    TradeOrder,
    Profile,
    IdentityVerification,
    PasswordResetRequest,
    UserBankDetail,
    Deposit,
    WithdrawalAddress,
    WithdrawalRequest,
    SubscriptionItem,
    Subscription,
    BannerSet,
    SupportMessage,
)

User = get_user_model()


@admin.register(TradeOrder)
class TradeOrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'pair', 'direction', 'amount', 'created_at', 'expiry_time', 'profit')
    list_filter = ('direction', 'pair', 'created_at')
    search_fields = ('user__username', 'pair')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credit_score', 'total_deposit', 'total_profit', 'total_balance', 'is_approved')
    search_fields = ('user__username', 'invite_code')


@admin.register(IdentityVerification)
class IdentityVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'submitted_at', 'approved')
    search_fields = ('user__username', 'phone')
    list_filter = ('approved',)


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_at', 'is_used')
    search_fields = ('user__username',)
    list_filter = ('is_used',)


@admin.register(UserBankDetail)
class UserBankDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank_type', 'bank_number', 'account_name', 'is_verified')
    search_fields = ('user__username', 'bank_number')
    list_filter = ('is_verified',)


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'amount', 'is_approved', 'created_at')
    list_filter = ('currency', 'is_approved', 'created_at')
    search_fields = ('user__username',)


@admin.register(WithdrawalAddress)
class WithdrawalAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'address', 'network', 'is_active', 'created_at')
    search_fields = ('user__username', 'address')
    list_filter = ('network', 'is_active')


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'address', 'network', 'amount', 'is_approved', 'created_at')
    list_filter = ('currency', 'network', 'is_approved')
    search_fields = ('user__username', 'address')


@admin.register(SubscriptionItem)
class SubscriptionItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available_from', 'available_until', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'subscribed_at')
    search_fields = ('user__username', 'item__name')


@admin.register(BannerSet)
class BannerSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'message', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'message')


