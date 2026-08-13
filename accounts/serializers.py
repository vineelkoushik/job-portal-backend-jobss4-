from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):

    role = serializers.ChoiceField(
        choices=Profile.ROLE_CHOICES
    )

    phone = serializers.CharField()
    location = serializers.CharField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "role",
            "phone",
            "location"
        ]

        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }

    def create(self, validated_data):

        role = validated_data.pop("role")
        phone = validated_data.pop("phone")
        location = validated_data.pop("location")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"]
        )

        Profile.objects.create(
            user=user,
            role=role,
            phone=phone,
            location=location
        )

        return user
class ProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    email = serializers.EmailField(
        source="user.email",
        read_only=True
    )

    class Meta:
        model = Profile
        fields = [
            "username",
            "email",
            "role",
            "phone",
            "location",
            "resume",
            "skills"
        ]
        read_only_fields = [
        "username",
        "email",
        "role"
        ]
        
class ProfileSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = Profile

        fields = [
            "id",
            "username",
            "role",
            "phone",
            "location",
            "skills"
        ]

        read_only_fields = [
            "id",
            "username",
            "role"
        ]