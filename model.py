import json
from time import time

from core.dealer import Dealer

class Match:

    def __init__(self, cid, name=None, **kwargs):
        self.cid = cid
        self.name = name
        self.dealer = Dealer()

        # uid list, in order (rotates)
        self.users = kwargs.get('users', [])
        # uid -> (card1, card2)
        self.hands = kwargs.get('hands', {})
        # uid -> chips
        self.chips = kwargs.get('chips', {})
        # uid -> bet
        self.bets = kwargs.get('bets', {})
        # flop, hand, river [5]
        self.cards = kwargs.get('cards', [])

        self.BB = kwargs.get('BB', 0)
        self.SB = kwargs.get('SB', self.BB / 2)

    def setBB(self,BB):
        self.BB = BB
        self.SB = BB / 2

    def toView(self):
        return {
            "cid": self.cid,
            "BB": self.BB,
            "SB": self.SB,
            "name": self.name,
            # "users": self.users,
            # "cards": self.cards,
            # "chips": self.chips,
            # "bets": self.bets,
        }

    def getCurrentId(self):
        if self.dealer.current is None:
            return None

        return self.users[self.dealer.current]


class User:
    def __init__(self, uid, name=None, chips=0, last_request=0):
        self.uid = uid
        self.name = name
        self.chips = chips
        self.last_request = last_request

    def toView(self):
        return {
            "uid": self.uid,
            "name": self.name,
            "chips": self.chips,
            "last_request": self.last_request,
        }

def save():
    with open(file_loc, 'w') as fh:
        json.dump({cid:c.toView() for cid,c in channels.items()}, fh)

    with open(user_loc, 'w') as fh:
        json.dump({uid:u.toView() for uid,u in users.items()}, fh)

def load():
    with open(file_loc, 'r') as fh:
        channels = {cid:Match(**c) for cid,c in json.load( fh).items()}

    with open(user_loc, 'r') as fh:
        users = {uid:User(**u) for uid,u in json.load( fh).items()}

    return channels, users

def fetch_or_create(cid, name):
    if cid in channels:
        return channels[cid]

    match = Match(cid, name)
    channels[cid] = match

    return match


def fetch_or_create_user(uid, name):
    if uid in users:
        return users[uid]

    user = User(uid, name, chips=1000, last_request=int(time()))
    users[uid] = user

    return user


def fetch_test_user():
    user = User("333597133720649729", "IrishCyborg", chips=10000000, last_request=int(time()))

    return user


def fetch(cid):
    return channels[cid]


file_loc = "matches.json"
user_loc = "users.json"
channels, users = load()


def sit_user(user: User, match: Match, chips):
    N = len(match.users)
    uid = user.uid

    if uid in match.users:
        # you're already sitting
        return

    match.users.append(uid)
    match.chips[uid] = chips
    match.bets[uid] = 0
    match.hands[uid] = None

    return N
