"""
Serializers pour PlayerProfile.
"""
from rest_framework import serializers
from .models import PlayerProfile


class PlayerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email    = serializers.EmailField(source="user.email",    read_only=True)

    class Meta:
        model = PlayerProfile
        fields = [
            "id", "username", "email",
            "battletag", "rank_tank", "rank_dps", "rank_support",
            "most_played", "last_synced",
        ]
        read_only_fields = ["id", "username", "email", "most_played", "last_synced"]
