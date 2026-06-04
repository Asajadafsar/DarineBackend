from rest_framework import serializers
from accounts.models import User
# admin_panel/serializers.py

from rest_framework import serializers
from accounts.models import UserFee
from rest_framework import serializers
from gold_app.models import FinancialTransaction, GiftCard, GiftCardOrder, GoldBankInfo, GoldTransaction, Order, OrderItem, Product, ProductCategory
from gold_app.utils import get_live_gold_price
from decimal import Decimal
from silver_app.models import SilverBankInfo, SilverFinancialTransaction, SilverOrder, SilverOrderItem, SilverProductCategory, SilverProduct, SilverTransaction
from silver_app.utils import get_live_silver_price
import uuid





class AdminUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class AdminUserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class AdminUserUpdateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ("id", "date_joined")

    def update(self, instance, validated_data):

        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
    





class UserFeeSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = UserFee
        fields = [
            "id",
            "user",
            "user_mobile",
            "gold_buy_fee",
            "gold_sell_fee",
            "silver_buy_fee",
            "silver_sell_fee",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user_mobile"]


class UserFeeUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserFee
        fields = [
            "gold_buy_fee",
            "gold_sell_fee",
            "silver_buy_fee",
            "silver_sell_fee",
        ]






# =========================================================
# CATEGORY
# =========================================================

class ProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductCategory
        fields = "__all__"


# =========================================================
# PRODUCT LIST
# =========================================================

class ProductSerializer(serializers.ModelSerializer):

    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


# =========================================================
# PRODUCT CREATE / UPDATE
# =========================================================

class ProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = "__all__"

    def validate(self, attrs):

        try:
            weight = attrs.get("weight")

            if weight is None:
                raise serializers.ValidationError({
                    "weight": "وزن محصول الزامی است"
                })

            price_per_gram = get_live_gold_price()

            if not price_per_gram:
                raise serializers.ValidationError({
                    "price": "قیمت طلا دریافت نشد"
                })

            price_per_gram = Decimal(str(price_per_gram))
            weight = Decimal(str(weight))

            base_price = weight * price_per_gram

            # اجرت/کارمزد (فعلاً خام)
            attrs["buy_price"] = int(base_price)
            attrs["sell_price"] = int(base_price)

            # این هم همون وزن واقعی
            attrs["total_weight_with_fees"] = weight

            return attrs

        except Exception as e:
            raise serializers.ValidationError({
                "error": f"server validation error: {str(e)}"
            })
        


class SilverProductCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProductCategory
        fields = "__all__"


class SilverProductSerializer(serializers.ModelSerializer):

    category_name = serializers.SerializerMethodField()

    class Meta:
        model = SilverProduct
        fields = "__all__"

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    

class SilverProductCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverProduct
        fields = "__all__"
        extra_kwargs = {
            "weight": {"required": False},
            "name": {"required": False},
            "category": {"required": False},
            "delivery_type": {"required": False},
            "inventory_count": {"required": False},
            "image": {"required": False},
            "description": {"required": False},
            "buy_price": {"required": False},
            "sell_price": {"required": False},
            "total_weight_with_fees": {"required": False},
        }

    def validate(self, attrs):

        price_per_gram = get_live_silver_price()

        if price_per_gram is None:
            raise serializers.ValidationError({
                "price": "قیمت نقره دریافت نشد"
            })

        price_per_gram = Decimal(str(price_per_gram))

        weight = attrs.get("weight", None)

        if weight is not None:

            weight = Decimal(str(weight))

            base_price = weight * price_per_gram

            attrs["buy_price"] = base_price
            attrs["sell_price"] = base_price
            attrs["total_weight_with_fees"] = weight

        return attrs
    

class GiftCardSerializer(serializers.ModelSerializer):

    created_by_name = serializers.CharField(source="created_by.mobile", read_only=True)
    activated_by_name = serializers.CharField(source="activated_by.mobile", read_only=True)

    class Meta:
        model = GiftCard
        fields = "__all__"



class GiftCardCreateUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = GiftCard
        fields = "__all__"
        extra_kwargs = {
            "created_by": {"required": False, "read_only": True},
            "activated_by": {"required": False, "read_only": True},
            "serial_number": {"required": False},
            "status": {"required": False},
            "is_used": {"required": False},
            "used_at": {"required": False},
        }

    def validate(self, attrs):

        import uuid

        if not attrs.get("serial_number"):
            attrs["serial_number"] = str(uuid.uuid4()).split("-")[0].upper()

        return attrs




class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(required=True)
    admin_note = serializers.CharField(required=False, allow_blank=True)


class GiftCardOrderSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = GiftCardOrder
        fields = "__all__"

    

class OrderItemSerializer(serializers.ModelSerializer):

    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"



class FinancialTransactionSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = FinancialTransaction
        fields = "__all__"


class GoldTransactionSerializer(serializers.ModelSerializer):

    user_mobile = serializers.CharField(source="user.mobile", read_only=True)

    class Meta:
        model = GoldTransaction
        fields = "__all__"



class SilverOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SilverOrderItem
        fields = "__all__"


class SilverOrderSerializer(serializers.ModelSerializer):
    items = SilverOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = SilverOrder
        fields = "__all__"


class SilverTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverTransaction
        fields = "__all__"


class SilverFinancialTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverFinancialTransaction
        fields = "__all__"


# class StatusUpdateSerializer(serializers.Serializer):
#     status = serializers.CharField()
#     admin_note = serializers.CharField(required=False, allow_blank=True)





class AdminDashboardSerializer(serializers.Serializer):

    users_count = serializers.IntegerField()

    verified_users = serializers.IntegerField()

    pending_users = serializers.IntegerField()

    gold_products = serializers.IntegerField()

    silver_products = serializers.IntegerField()

    gold_orders = serializers.IntegerField()

    silver_orders = serializers.IntegerField()

    pending_orders = serializers.IntegerField()

    gold_transactions = serializers.IntegerField()

    silver_transactions = serializers.IntegerField()

    total_wallet_balance = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )

    total_silver_wallet_balance = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )

    total_gold_inventory = serializers.DecimalField(
        max_digits=30,
        decimal_places=5
    )

    total_silver_inventory = serializers.DecimalField(
        max_digits=30,
        decimal_places=5
    )

    total_deposit_amount = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )

    pending_withdraw_amount = serializers.DecimalField(
        max_digits=30,
        decimal_places=0
    )

    recent_users = serializers.ListField()

    recent_orders = serializers.ListField()



class GoldBankInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoldBankInfo
        fields = "__all__"


class SilverBankInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = SilverBankInfo
        fields = "__all__"

        