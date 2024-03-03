import os

from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse

from django.conf import settings
from .models import Player, Team, TeamMember, Bid


def homepage(request):
    return render(request, "index.html")

def paginate(request, queryset):
    paginator = Paginator(queryset, 20) 
    page = request.GET.get('page')
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    return items


def list_players(request):
    try:
        players = Player.objects.all()
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
    
    
    context = {
        "players": paginate(request=request, queryset=players),
        "title": "List of all players",
        "MEDIA_URL": settings.MEDIA_URL
        }
    return render(request, "pages/players.html", context)

def list_teams(request):
    try:
        teams = Team.objects.all()
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    context = {
        "teams": paginate(request=request, queryset=teams), 
        "title": "List of all teams",
        "MEDIA_URL": settings.MEDIA_URL
        }
    return render(request, "pages/teams.html", context)

def list_team_members(request, id):
    try:
        team_players = TeamMember.objects.filter(team=id)
        team = Team.objects.filter(id=id).first()
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    context = {
        "team_players": team_players,
        "team": team,
        "title": f"Team members of {team.name}",
        "MEDIA_URL": settings.MEDIA_URL
        }
    return render(request, "pages/team_players.html", context)

def list_players_for_bidding(request):
    try:
        players = Player.objects.filter(is_sold=False)
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    context = {
        "players": paginate(request=request, queryset=players),
        "title": "Remaining players",
        "MEDIA_URL": settings.MEDIA_URL
        }
    return render(request, "pages/to_bid.html", context)

def add_new_bid(request, id):
    try:
        player = Player.objects.filter(id=id).first()
        teams = Team.objects.all()
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    context = {
        "player": player,
        "teams": teams,
        "title": "New bid",
        "MEDIA_URL": settings.MEDIA_URL
        }
    return render(request, "pages/bids.html", context)

def save_bid(request):
    if request.method == "POST":
        player = request.POST.get("player")
        team = request.POST.get("team")
        bid_amount = request.POST.get("amount")
        is_sold = bool(request.POST.get("is_sold"))
        next = request.POST.get("next")
        try:
            bid_id = Bid.objects.create(
                team=Team.objects.filter(id=team).first(),
                player=Player.objects.filter(id=player).first(),
                bid_amount=bid_amount,
                is_sold=is_sold
            )
            messages.success(request, 'Bid successfully recorded!')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
        if is_sold:
            return HttpResponseRedirect(reverse('to_bid'))
        else:
            return HttpResponseRedirect(next)
    else:
        # If the request method is not POST, render the form template
        return HttpResponseRedirect(next)