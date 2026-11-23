from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from content.api import ArticleListSerializer
from content.models import Article

from .models import Collection, Profile


class CollectionSerializer(serializers.ModelSerializer):
    articles = ArticleListSerializer(many=True, read_only=True)
    article_ids = serializers.PrimaryKeyRelatedField(
        source="articles", many=True, write_only=True, required=False,
        queryset=Article.objects.all(),
    )

    class Meta:
        model = Collection
        fields = ["id", "name", "description", "is_public", "articles", "article_ids", "created_at"]


class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.collections.prefetch_related("articles__rubric")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me(request):
    p = Profile.for_user(request.user)
    sub = p.active_subscription
    return Response({
        "username": request.user.username,
        "email": request.user.email,
        "bio": p.bio,
        "avatar": request.build_absolute_uri(p.avatar.url) if p.avatar else None,
        "interests": list(p.interests.values_list("name", flat=True)),
        "recommendation_mode": p.recommendation_mode,
        "is_premium": p.is_premium,
        "sees_ads": p.sees_ads,
        "subscription": {"plan": sub.plan.name, "ends_at": sub.ends_at} if sub else None,
        "saved": ArticleListSerializer(p.saved_articles.all(), many=True).data,
    })
