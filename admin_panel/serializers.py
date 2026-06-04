from rest_framework import serializers
from accounts.models import User
# admin_panel/serializers.py

from rest_framework import serializers
from accounts.models import UserFee
from rest_framework import serializers
from gold_app.models import Product, ProductCategory
from gold_app.utils import get_live_gold_price
from decimal import Decimal
from silver_app.models import SilverProductCategory, SilverProduct
from silver_app.utils import get_live_silver_price





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