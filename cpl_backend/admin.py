from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import TeamMember, Team, Player, Bid

admin.site.site_header = 'CPL Dashboard'

class PlayerResouce(resources.ModelResource):
    class Meta:
        model = Player

# Register your models here.
class PlayerAdmin(ImportExportModelAdmin):
    resource_classes = [PlayerResouce]
    list_display = ("cpl_id", "name", "type", "basic_amount", "photo", "card", "is_external", "is_sold")
    search_fields = ("cpl_id", "name")

    # @admin.display(description='Team')
    # def team(self, obj):
    #     team = TeamMember.objects.get(team=obj.id)
    #     return team.team.name

class TeamResource(resources.ModelResource):
    class Meta:
        model = Team

class TeamAdmin(ImportExportModelAdmin):
    resource_classes = [TeamResource]
    list_display = ("cpl_id", "name", "description", "total_amount", "expended_amount", "balance_amount")
    search_fields = ("cpl_id", "name")


class BidAdmin(admin.ModelAdmin):
    list_display = ("team", "player", "bid_amount", "is_sold")

admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(TeamMember)