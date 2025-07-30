from django.urls import path
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('contract/', views.place_trade, name='place_trade'),
    path('submit-order/', views.submit_order, name='submit_order'),
    path("index/", views.profile, name="profile"),
    path("assets/", views.user_trades, name="user_trades"),
    path('verify/', views.verify_identity, name='verify_identity'),
    path('real_name_auth/', views.real_name_auth, name='real_name_auth'),
    path('verifications/', views.verification_list, name='verification_list'),
    path('verifications/approve/<int:pk>/', views.approve_verification, name='approve_verification'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('bank-detail/', views.bank_detail_view, name='bank_detail'),
    path('bank/approve/<int:pk>/', views.approve_bank_detail, name='approve_bank'),
    path('deposit/', views.deposit_create_view, name='deposit_create'),
    path('deposit/list/', views.deposit_list_view, name='deposit_list'),
    path('deposit/approve/<int:pk>/', views.deposit_approve, name='deposit_approve'),
    path('request-withdrawal/', views.request_withdrawal, name='request_withdrawal'),
    path('withdrawal/list/', views.withdrawal_list, name='withdrawal_success'),
    path('set-withdrawal-password/', views.set_withdrawal_password, name='set_withdrawal_password'),
    path('real_market/', views.real_market, name='real_market'),
    path('admin/trades/', views.trade_review_admin, name='admin_trades'),
    path('admin/trade/<int:trade_id>/mark/<str:outcome>/', views.mark_trade_result, name='mark_trade_result'),
    path('language_page/', views.language_page, name='language_page'),
    path('upload-banners/', views.upload_banner_set, name='upload_banner_set'),
    path('mining/', views.mining, name='mining'),
    path('staking/', views.staking, name='staking'),



    path('ad/manage_trades/', views.admin_manage_trades, name='admin_manage_trades'),
    path("trade/check/<int:trade_id>/", views.check_trade_result, name="check_trade"),
    path('delete-trade/<int:trade_id>/', views.delete_trade, name='delete_trade'),

    
    path('ad/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('ad/deposits/', views.admin_deposit_list, name='admin_deposits'),
    path('ad/deposit/approve/<int:deposit_id>/', views.approve_deposit, name='approve_deposit'),
    path('ad/loginx/z1z2', views.admin_login_view, name='admin_login'),
    path('ad/logout/', views.admin_logout , name='admin_logout'),
    path('ad/registerx/z1z2', views.admin_register_view, name='admin_register'),
    path('ad/admins/', views.all_admins_view, name='all_admins'),
    path('ad/admins/delete/<int:admin_id>/', views.delete_admin_view, name='delete_admin'),
    path('ad/withdrawal_list/', views.admin_withdrawal_list, name='admin_withdrawal_list'), 
    path('ad/trade/<int:trade_id>/mark/', views.mark_trade_result, name='mark_trade_result'),
    path('subscription/create/', views.create_subscription_item, name='create_subscription_item'),
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/subscribe/<int:item_id>/', views.subscribe_to_item, name='subscribe_to_item'),
    path('ad/trades/update/<int:trade_id>/', views.update_trade_profit, name='update_trade_profit'),
    path('all-users/', views.all_users_view, name='all_users'),
    path('pending/', TemplateView.as_view(template_name='index/invite_pending.html'), name='invite_pending'),
    path('ad/invites/', views.admin_invite_list, name='admin_invite_list'),
    path('ad/invite/approve/<int:profile_id>/', views.approve_user, name='approve_user'),
    path('ad/deposits_list/', views.admin_deposit_list_view, name='admin_deposit_list_view'),
    path('support/', views.support_chat, name='support_chat'), 
    path('support-page/', views.support_page, name='support_page'),
    path('ad/support/', views.admin_support_dashboard, name='admin_support_dashboard'),  
    path('ad/support/<int:user_id>/', views.admin_chat_with_user, name='admin_chat_with_user'),
  

]