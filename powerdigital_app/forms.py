from django import forms
from .models import TradeOrder , IdentityVerification , UserBankDetail , Deposit , WithdrawalRequest , WithdrawalRequest , SubscriptionItem , BannerSet
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.models import User
from django import forms



class TradeOrderForm(forms.ModelForm):
    class Meta:
        model = TradeOrder
        fields = ['pair', 'direction', 'amount']



class IdentityVerificationForm(forms.ModelForm):
    class Meta:
        model = IdentityVerification
        fields = ['phone', 'id_card_front', 'id_card_back']



class PasswordResetForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter new password'})
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )



class UserBankDetailForm(forms.ModelForm):
    class Meta:
        model = UserBankDetail
        fields = ['bank_type', 'bank_number', 'account_name']



class DepositForm(forms.ModelForm):
    class Meta:
        model = Deposit
        fields = ['currency', 'amount', 'payment_proof']




class WithdrawalPasswordSetForm(forms.Form):
    new_password = forms.CharField(
        label="New Withdrawal Password",
        widget=forms.PasswordInput()
    )

    


class WithdrawalRequestForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Withdrawal Password")

    class Meta:
        model = WithdrawalRequest
        fields = ['currency', 'address', 'network', 'amount']
      
        

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data['password']
        profile = self.user.profile

        if not profile.withdrawal_password:
            raise forms.ValidationError("You haven't set a withdrawal password.")

        if not profile.check_withdrawal_password(password):
            raise forms.ValidationError("Incorrect withdrawal password.")

        return password




from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class AdminRegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")

        password = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")
        if password and confirm and password != confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_superuser(
            username=data['username'],
            email=data['email'],
            password=data['password'],
        )
        return user



class SubscriptionItemForm(forms.ModelForm):
    class Meta:
        model = SubscriptionItem
        fields = [
            'name',
            'image',
            'description',
            'price',
            'available_from',
            'available_until',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_from': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'available_until': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }




class BannerSetForm(forms.ModelForm):
    class Meta:
        model = BannerSet
        fields = ['banner1', 'banner2', 'banner3']


