from rest_framework import serializers
from .models import User
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import UserDetailsSerializer, LoginSerializer
from django.contrib.auth import get_user_model

UserModel = get_user_model()

# 회원 가입 custom serializer
class CustomRegisterSerializer(RegisterSerializer):
    nickname = serializers.CharField(
        required=True,
        max_length=150,
    )
    phone = serializers.CharField(
        max_length = 11,
        # validators=[User.phone_regex],
        required=False,
        default = ''
    )
    age = serializers.IntegerField(
        required=True,
    )

    # property = serializers.IntegerField(
    #     required=False,
    #     default=0
    # )

    # gender = serializers.CharField(
    #     max_length=1,
    #     default='N',
    #     required=False
    # )

    # marital_status = serializers.BooleanField(
    #     required=False,
    #     default=False
    # )
    # 동적으로 unique 속성 필드에 대한 중복 검사
    def validate(self, attrs):
        unique_fields = ['phone', 'nickname']  # 검사할 필드 추가
        for field in unique_fields:
            value = attrs.get(field)
            if value and User.objects.filter(**{field: value}).exists():
                raise serializers.ValidationError({field: f"이미 등록된 {field} 입니다."})
        return attrs

    def validate_gender(self, value):
        valid_choices = ['M', 'F', 'N']
        if value not in valid_choices:
            raise serializers.ValidationError(f"'{value}' is not a valid choice for gender.")
        return value

    # 필드 데이터 불러오기
    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'nickname': self.validated_data.get('nickname', ''),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'phone': self.validated_data.get('phone', ''),
            'age': self.validated_data.get('age', 0),
        }
    
    # 추가 로직(로그 기록, 외부 API 호출 등) 구현 시 필요한 save 메서드 오버라이드
    def save(self, request):
        user = super().save(request)
        # 추가 필드 작성
        user.nickname = self.validated_data.get('nickname', '')
        user.phone = self.validated_data.get('phone', '')
        user.age = self.validated_data.get('age', 0)
        user.save()
        return user


# 회원 가입 상품 정보를 위한 serializer
# from ..financial_products.models import *


# 회원 정보 custom serializer
class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta:
        model = UserModel
        fields = (
            'pk',
            'username',
            'email',
            'nickname',
            'profile_img',
            'phone',
            'age',
            'gender',
            'property',
            'marital_status',
        )
        read_only_fields = ('username', 'email') # 변경 불가 필드들

    # 유니크 필드 검증(유효성 검증)
    def validate(self, attrs):
        user = self.context['request'].user
        unique_fields = ['nickname', 'phone', 'email']
        for field in unique_fields:
            value = attrs.get(field)
            if value:
                # 중복 검사 시 현재 사용자를 제외
                if UserModel.objects.exclude(pk=user.pk).filter(**{field: value}).exists():
                    raise serializers.ValidationError({
                        field: f'이미 등록된 {field}입니다.'
                    })
        return attrs


# 로그인 custom serializer
# 이메일과 비밀번호만 이용하여 로그인
class CustomLoginSerializer(LoginSerializer):
    username = None
    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = self.get_auth_user(email, password)

        if not user:
            msg = 'Unable to log in with provided credentials.'
            raise serializers.ValidationError(msg)

        attrs['user'] = user
        return attrs

    def get_auth_user(self, email, password):
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
        except UserModel.DoesNotExist:
            return None





from financial_products.models import Deposit, Saving


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = ['id']

class SavingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Saving
        fields = ['id']


class UserInfoSerializer(UserDetailsSerializer):
    joined_deposits = DepositSerializer(many=True, read_only=True)
    joined_savings = SavingSerializer(many=True, read_only=True)

    # id = CustomUserDetailsSerializer()
    # age = CustomUserDetailsSerializer()
    # gender = CustomUserDetailsSerializer()
    # property = CustomUserDetailsSerializer()
    # merital_status = CustomUserDetailsSerializer()

    class Meta:
        model = UserModel
        # fields = ['id', 'age', 'gender', 'property', 'merital_status', 'joined_deposits', 'joined_savings']
        fields = '__all__'
