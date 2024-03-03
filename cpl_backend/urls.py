from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name="home"),
    path('players/', views.list_players, name="players"),
    path('teams/', views.list_teams, name="teams"),
    path('teams/<int:id>', views.list_team_members, name="team"),
    path('bids/', views.list_players_for_bidding, name="to_bid"),
    path('players/<int:id>/bid', views.add_new_bid, name="bids"),
    path('save-bid/', views.save_bid, name='save_bid'),
]
