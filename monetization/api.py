from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Partner, Plan
from .services import SubscriptionFacade


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "price", "duration_days", "ad_free", "exclusive_access", "description"]


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.filter(is_active=True)
    serializer_class = PlanSerializer

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        try:
            sub = SubscriptionFacade().subscribe(request.user, int(pk))
        except (Plan.DoesNotExist, ValueError) as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"plan": sub.plan.name, "starts_at": sub.starts_at, "ends_at": sub.ends_at}, status=201)


class PartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partner
        fields = ["id", "name", "website", "description"]


class PartnerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Partner.objects.all()
    serializer_class = PartnerSerializer
