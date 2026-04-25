from django.urls import path
from .views import BuyGold, DepositMoney, SellGold, UserAssets, WithdrawMoney

urlpatterns = [
    path('buy/', BuyGold.as_view(), name='buy_gold'),
    path('sell/', SellGold.as_view(), name='sell_gold'),
    path('assets/', UserAssets.as_view(), name='user_assets'),
    path('deposit/', DepositMoney.as_view(), name='deposit_money'),
    path('withdraw/', WithdrawMoney.as_view(), name='withdraw_money'),
]
