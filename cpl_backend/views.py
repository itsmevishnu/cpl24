import os

from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.conf import settings
from .models import Player, Team, TeamMember, Bid
from . import constants
from django.db.models import Sum


def homepage(request):
    context = constants.SITE_INFO
    return render(request, "index.html", context=context)

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
        "MEDIA_URL": settings.MEDIA_URL,
        "SITE_INFO": constants.SITE_INFO
        }
    return render(request, "pages/players.html", context)

def list_teams(request):
    # (((EXTERNAL_PLAYERS_COUNT - current_external_players) * EXTERNAL_PLAYER_BASIC_AMOUNT
# INTERNAL_PLAYERS_COUNT - current_internal_players) * INTERNAL_PLAYER_BASIC_AMOUNT) ):
    try:
        teams = Team.objects.all()
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    context = {
        "teams": paginate(request=request, queryset=teams), 
        "title": "List of all teams",
        "MEDIA_URL": settings.MEDIA_URL,
        "SITE_INFO": constants.SITE_INFO
        }
    return render(request, "pages/teams.html", context)

def list_team_members(request, id):
    # Team-players are players of the current team
    # Find out the number of external players
    # Find oout the number of internal players
    # Calculate the next highest bid amount for external players
    # Total__balance - ((Total_extenal_player - current_extenal_player)* external_player_amount
    # + (Total_internal_player - current_internal_player)* internal_player_amount)
    # Calculate the next highest bid amount for internal players
    try:
        team_players = TeamMember.objects.filter(team=id)
        team = Team.objects.filter(id=id).first()
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    internal_player_count = team_players.filter(players__is_external=False).count() 
    external_player_count = team_players.filter(players__is_external=True).count()
    
    remaining_internal_player = constants.INTERNAL_PLAYERS_COUNT - internal_player_count
    remaining_external_player = constants.EXTERNAL_PLAYERS_COUNT - external_player_count

    total_internal_bids = Bid.objects.filter(team=team, player__is_external=False, is_sold=True).aggregate(Sum("bid_amount"))
    total_external_bids = Bid.objects.filter(team=team, player__is_external=True, is_sold=True).aggregate(Sum("bid_amount"))
    
    internal_bid_sum = total_internal_bids["bid_amount__sum"] if  total_internal_bids["bid_amount__sum"] else 0
    external_bid_sum = total_external_bids["bid_amount__sum"] if total_external_bids["bid_amount__sum"] else 0
    
    total_internal_fund = (remaining_internal_player * constants.INTERNAL_PLAYER_BASIC_AMOUNT) + internal_bid_sum
    total_external_fund = (remaining_external_player * constants.EXTERNAL_PLAYER_BASIC_AMOUNT) + external_bid_sum
    total_bidded = total_internal_fund + total_external_fund
    
    next_bid = constants.TEAM_BASIC_AMOUNT - total_bidded 
    next_bid = next_bid + 2000 if remaining_external_player != 0 else next_bid + 600

    print(internal_bid_sum, external_bid_sum)
    print(remaining_internal_player, remaining_external_player)
    print(total_internal_fund,total_external_fund )
    print(next_bid)

    player_counts = {
        "internal_player_count": internal_player_count,
        "external_player_count": external_player_count,
        "total_internal_players": constants.INTERNAL_PLAYERS_COUNT,
        "total_external_players": constants.EXTERNAL_PLAYERS_COUNT,
        "next_bid": next_bid
    }
    


    context = {
        "team_players": team_players,
        "team": team,
        "title": f"Team members of {team.name}",
        "MEDIA_URL": settings.MEDIA_URL,
        "counts": player_counts
        }
    messages.warning(request, f'Team required {remaining_internal_player} more internal players \
                     and {remaining_external_player} more external players.')
    return render(request, "pages/team_players.html", context)

def list_players_for_bidding(request):
    try:
        players = Player.objects.filter(is_sold=False)
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')

    context = {
        "players": paginate(request=request, queryset=players),
        "title": "Remaining players",
        "MEDIA_URL": settings.MEDIA_URL,
        "SITE_INFO": constants.SITE_INFO
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
        "MEDIA_URL": settings.MEDIA_URL,
        "SITE_INFO": constants.SITE_INFO
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
            return HttpResponseRedirect(next)
        
        if is_sold:
            return HttpResponseRedirect(reverse('to_bid'))
        else:
            return HttpResponseRedirect(next)
    else:
        # If the request method is not POST, render the form template
        return HttpResponseRedirect(next)
    

def search_player(request):
    if request.method == "GET":
        keyword = request.GET.get("search")
        players = Player.objects.filter(Q(name__icontains=keyword) | 
                                        Q(cpl_id__icontains=keyword))
        
        context = {
        "players": paginate(request=request, queryset=players),
        "title": "List of all players",
        "MEDIA_URL": settings.MEDIA_URL,
        "SITE_INFO": constants.SITE_INFO
        }
    return render(request, "pages/players.html", context)
            