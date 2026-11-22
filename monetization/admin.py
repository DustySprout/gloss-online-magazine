from django.contrib import admin

from .models import AdCampaign, Partner, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration_days", "ad_free", "exclusive_access", "is_active")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "starts_at", "ends_at", "is_active", "amount_paid")
    list_filter = ("plan", "is_active")


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "website")


@admin.register(AdCampaign)
class AdCampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "partner", "is_promo", "is_active", "starts_at", "ends_at")
    list_filter = ("is_promo", "is_active", "partner")
