from django.db.models import F
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Profile

from .models import Article, Issue, IssueItem, Rubric
from .patterns import ArticleAccessProxy, get_creator
from .recommendations import RecommendationService


class RubricSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rubric
        fields = ["id", "name", "slug", "description", "color"]


class ArticleListSerializer(serializers.ModelSerializer):
    rubric = serializers.StringRelatedField()

    class Meta:
        model = Article
        fields = ["id", "title", "slug", "rubric", "kind", "lead", "is_premium", "published_at", "views"]


class ArticleDetailSerializer(ArticleListSerializer):
    body = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    full_access = serializers.SerializerMethodField()
    partner = serializers.StringRelatedField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ["body", "video_url", "partner", "full_access"]

    def _proxy(self, obj):
        return ArticleAccessProxy(obj, self.context["request"].user)

    def get_body(self, obj):
        return self._proxy(obj).body

    def get_video_url(self, obj):
        return self._proxy(obj).video_url

    def get_full_access(self, obj):
        return self._proxy(obj).can_read_full


class ArticleCreateSerializer(serializers.Serializer):
    """Створення через Factory Method: тип матеріалу визначає творця."""

    kind = serializers.ChoiceField(choices=Article.Kind.choices)
    title = serializers.CharField(max_length=200)
    rubric = serializers.PrimaryKeyRelatedField(queryset=Rubric.objects.all())
    lead = serializers.CharField(max_length=300)
    body = serializers.CharField()
    is_premium = serializers.BooleanField(required=False, default=False)
    video_url = serializers.URLField(required=False, allow_blank=True)
    guest = serializers.CharField(required=False, allow_blank=True)

    def create(self, data):
        kind = data.pop("kind")
        try:
            return get_creator(kind).create(author=self.context["request"].user, **data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))


class IsStaffOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_staff


class RubricViewSet(viewsets.ModelViewSet):
    queryset = Rubric.objects.all()
    serializer_class = RubricSerializer
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "slug"


class ArticleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsStaffOrReadOnly]
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        if self.request.user.is_staff:
            qs = Article.objects.all()
        else:
            qs = Article.published.all()
        qs = qs.select_related("rubric", "partner")
        rubric = self.request.query_params.get("rubric")
        if rubric:
            qs = qs.filter(rubric__slug=rubric)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return ArticleCreateSerializer
        if self.action == "list":
            return ArticleListSerializer
        return ArticleDetailSerializer

    def create(self, request, *args, **kwargs):
        s = ArticleCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        article = s.save()
        return Response(ArticleDetailSerializer(article, context={"request": request}).data, status=201)

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        Article.objects.filter(pk=obj.pk).update(views=F("views") + 1)
        return Response(ArticleDetailSerializer(obj, context={"request": request}).data)

    @action(detail=True, methods=["post"], url_path="save", permission_classes=[permissions.IsAuthenticated])
    def toggle_save(self, request, slug=None):
        article = self.get_object()
        profile = Profile.for_user(request.user)
        if profile.saved_articles.filter(pk=article.pk).exists():
            profile.saved_articles.remove(article)
            return Response({"saved": False})
        profile.saved_articles.add(article)
        return Response({"saved": True})

    @action(detail=False, methods=["get"])
    def recommended(self, request):
        items = RecommendationService.for_user(request.user).get(request.user, 10)
        return Response(ArticleListSerializer(items, many=True).data)


class IssueItemSerializer(serializers.ModelSerializer):
    article = ArticleListSerializer()

    class Meta:
        model = IssueItem
        fields = ["order", "section", "article"]


class IssueSerializer(serializers.ModelSerializer):
    items = IssueItemSerializer(many=True, read_only=True)

    class Meta:
        model = Issue
        fields = ["id", "number", "title", "slug", "month", "is_special", "theme", "editor_note", "items"]


class IssueViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IssueSerializer
    lookup_field = "slug"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return Issue.objects.filter(is_published=True).prefetch_related("items__article__rubric")
