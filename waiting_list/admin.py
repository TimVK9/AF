from django.contrib import admin
from .models import InterestResponse


@admin.register(InterestResponse)
class InterestResponseAdmin(admin.ModelAdmin):
    list_display = ('email', 'comment', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('email', 'comment')
    readonly_fields = ('ip_address', 'created_at')
    ordering = ('-created_at',)
