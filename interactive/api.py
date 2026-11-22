from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .evaluators import evaluator_for
from .models import Answer, Comment, Poll, PollOption, Question, Quiz, Vote


class PollOptionSerializer(serializers.ModelSerializer):
    votes = serializers.IntegerField(source="votes.count", read_only=True)

    class Meta:
        model = PollOption
        fields = ["id", "text", "votes"]


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Poll
        fields = ["id", "question", "is_active", "total_votes", "options"]


class PollViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Poll.objects.filter(is_active=True).prefetch_related("options")
    serializer_class = PollSerializer

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def vote(self, request, pk=None):
        poll = self.get_object()
        option = poll.options.filter(pk=request.data.get("option")).first()
        if not option:
            return Response({"detail": "Невірний варіант"}, status=400)
        _, created = Vote.objects.get_or_create(poll=poll, user=request.user, defaults={"option": option})
        if not created:
            return Response({"detail": "Ви вже голосували"}, status=409)
        return Response(PollSerializer(poll).data, status=201)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "text"]  # правильні відповіді не віддаємо клієнту


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "answers"]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "kind", "questions"]


class QuizViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Quiz.objects.filter(is_active=True).prefetch_related("questions__answers")
    serializer_class = QuizSerializer

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def submit(self, request, pk=None):
        """Тіло запиту: {"answers": [id1, id2, ...]}"""
        quiz = self.get_object()
        try:
            r = evaluator_for(quiz).evaluate(request.user, [int(a) for a in request.data.get("answers", [])])
        except (ValueError, TypeError) as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"title": r.title, "description": r.description, "score": r.score, "max_score": r.max_score})


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "article", "user", "text", "created_at"]


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or obj.user == request.user or request.user.is_staff


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = Comment.objects.filter(is_visible=True).select_related("user")
        article = self.request.query_params.get("article")
        return qs.filter(article_id=article) if article else qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
