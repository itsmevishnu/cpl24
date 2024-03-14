from django.core.exceptions import ValidationError
from django.db import models

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .constants import PLAYER_CHOICES, INTERNAL_PLAYER_BASIC_AMOUNT, \
                EXTERNAL_PLAYER_BASIC_AMOUNT, TEAM_BASIC_AMOUNT,\
                EXTERNAL_PLAYERS_COUNT, INTERNAL_PLAYERS_COUNT

# Create your models here.
class Team(models.Model):

    class Meta:
        db_table = "teams"
    
    #field
    cpl_id = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField()
    logo = models.FileField(upload_to="teams/logo")
    total_amount = models.DecimalField(default=TEAM_BASIC_AMOUNT, decimal_places=2, max_digits=10)
    expended_amount = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    balance_amount = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    created_at = models.DateField(auto_now=True)

    def save(self, *args, **kwargs):
        self.balance_amount = self.total_amount - self.expended_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Player(models.Model):

    class Meta:
        db_table = "players"

    #Fields
    cpl_id = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=100)
    type = models.CharField(choices=PLAYER_CHOICES, max_length=100)
    card = models.FileField(upload_to="players/card",  null=True, blank=True)
    photo = models.FileField(upload_to="players/photo", null=True, blank=True)
    basic_amount = models.DecimalField(default=0, decimal_places=2, max_digits=10)
    is_external = models.BooleanField()
    is_sold = models.BooleanField()
    created_at = models.DateField(auto_now=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):

        if self.is_external:
            self.basic_amount = EXTERNAL_PLAYER_BASIC_AMOUNT
        else:
            self.basic_amount = INTERNAL_PLAYER_BASIC_AMOUNT

        super().save(*args, **kwargs)



class TeamMember(models.Model):

    class Meta:
         db_table = "team_players"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    players = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"Team: {self.team.name}, Player: {self.players.name}"


class Bid(models.Model):

    class Meta:
         db_table = "bids"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, blank=True, null=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, blank=True, null=True)
    bid_amount = models.FloatField()
    is_sold = models.BooleanField()
    created_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.team.name} quoted {self.bid_amount} for {self.player.name}"
    
    def clean(self):
        super().clean()
        next_bid = next_bid_amount(team=self.team, player=self.player)
        if self.bid_amount <= self.player.basic_amount:
            raise ValidationError("Bid amount should be greater than players' basic amount")
        
        if self.player.is_sold:
            raise ValidationError("The player already sold, Choose another players")

        if self.bid_amount > self.team.balance_amount:
            raise ValidationError("The bid amount should be less than your Balance amount")
        
        if self.bid_amount >= next_bid:
             raise ValidationError("Bid amount is too high, You can not buy enough players")


    def save(self, *args, **kwargs):
        self.full_clean()
        
        if self.is_sold:
            TeamMember.objects.create(team=self.team, players=self.player)
            self.player.is_sold = True
            self.player.save()
        #Update the value of team
        
        self.team.expended_amount += self.bid_amount
        self.team.save()
        super().save(*args, **kwargs)


@receiver(pre_delete, sender=Bid)
def pre_delete_bid(sender, instance, **kwargs):
    # If the bid is sold, remove the corresponding entry from TeamPlayer
    if instance.is_sold:
        TeamMember.objects.filter(team=instance.team, players=instance.player).delete()
        instance.player.is_sold = False
        instance.player.save()
    #update the amounts
    instance.team.expended_amount -= instance.bid_amount
    instance.team.save()
        
def next_bid_amount(team, player):
    try:
        team_players = TeamMember.objects.filter(team=team)
    except Exception as e:
        raise ValidationError("Unexpected error occured")
    
    internal_player_count = team_players.filter(players__is_external=False).count() 
    external_player_count = team_players.filter(players__is_external=True).count()

    #updated internal and external player count based on the player selected
    if not player.is_external:
        internal_player_count += 1
    else: 
        external_player_count += 1

    internal_required = INTERNAL_PLAYERS_COUNT - internal_player_count
    external_required = EXTERNAL_PLAYERS_COUNT - external_player_count

    if internal_required < 0 and external_required < 0: # bidding for extra players
        return team.balance_amount

    return team.balance_amount - ((internal_required * INTERNAL_PLAYER_BASIC_AMOUNT)+ 
                                      (external_required * EXTERNAL_PLAYER_BASIC_AMOUNT))