import json
import sys

import discord
from discord.ext.commands import Bot

from core import dealer, betting
import model
from views import numToIcon, getCard

bot = Bot(description="Poker bot", command_prefix="po ", pm_help=False)


@bot.event
async def on_ready():
    print('Logged in as ' + bot.user.name + ' (ID:' + bot.user.id + ') | Connected to ' + str(
        len(bot.servers)) + ' servers | Connected to ' + str(len(set(bot.get_all_members()))) + ' users')
    print('--------')
    print('Use this link to invite {}:'.format(bot.user.name))
    print('https://discordapp.com/oauth2/authorize?client_id={}&scope=bot&permissions=0'.format(bot.user.id))
    print('--------')



    return await bot.change_presence(game=discord.Game(name='With human lives'))


bot.remove_command('help')
@bot.command(pass_context=True)
async def help(ctx, *args):
    _help = """
    Discord poker commands:
    **Admins:**
    `po setchannel <bb>` - sets channel as poker room + sets big blind amount
    `:x: po delchannel` - 

    ------------
    **Players:**

    :x: `po refill` - gives you 1000 chips
    :x: `po wassup` - lists your stats and history

    ------------
    **Poker room:**

    `po sit <amount>` - sits in channel with amount in chips
    :x: `po leave` - sits out of channel
    :x: `po time` - forces the current player to flop if they're out of time

    `po call` - calls minimum bet
    `po check` - checks
    :x: `po bet <amount>` - bets or raises amount in chips. 
    :x: `po fold` - folds cards

    """
    return await bot.say(_help)


def getErr(e):
    str0 = "{} at line {} [{}]".format(str(e), sys.exc_info()[-1].tb_lineno, type(e).__name__)

    return str0


async def handle_turn(match: model.Match):
    N = len(match.users)

    try:
        # check if bets are even, if not, restart the turn
        bets = list(match.bets.values())

        are_bets_equalized = bets.count(bets[0]) == len(bets)
        state, n_cards = match.dealer.next_turn(can_switch_state=are_bets_equalized)

        if state == 'reset':
            # shift dealer role
            match.users.append(match.users.pop)

            return

        if state == 'hand' and n_cards is not None:
            await oszt_hand(match, n_cards)

            return

        if n_cards is None:
            # state didn't change, next player comes
            await bot.say(await msg_yourturn(match))

            return

        elif state != 'evaluate':
            # flop, turn, river:
            # we have cards to deal
            new_cards = match.dealer.deal(n_cards)
            match.cards.extend(new_cards)

            # Prepare str
            msg = "**" + match.dealer.state.title() + "**:"
            for card in match.cards:
                msg += " " + getCard(card)
            msg += "\n" + await msg_yourturn(match)

            await bot.say(msg)
            return

        else:
            # Evaluate cards, rewards winner(s)
            await evaluate_match(match)
            return

        await bot.say("Uhmm... uhg.... excuse me something went totally bad")

    except Exception as e:
        getErr(e)
        raise e


async def oszt_hand(match: model.Match, n_cards):
    try:
        # beginning of turn!
        for uid in match.users:
            hand = match.dealer.deal(n_cards)
            match.hands[uid] = hand
            user = await bot.get_user_info(uid)

            await bot.send_message(user, "{} Your hand: {} {}".format(user.name, getCard(hand[0]), getCard(hand[1])))

        # SB/BB
        BB_uid = match.users[-1]
        match.bets[BB_uid] = match.BB
        SB_uid = match.users[-2]
        match.bets[SB_uid] = match.SB

        user_BB = await bot.get_user_info(BB_uid)
        user_SB = await bot.get_user_info(SB_uid)

        msg = "Hands dealt in pm.\n"
        msg += "BB: {} ({}), SB: {} ({})\n".format(user_BB.name, match.BB, user_SB.name, match.SB)
        msg += "\n" + await msg_yourturn(match)

        await bot.say(msg)

    except Exception as e:
        raise e
        #getErr(e)


async def msg_yourturn(match: model.Match):
    user = await bot.get_user_info(match.getCurrentId())

    min_bet = max(match.bets.values())
    my_bet = match.bets[user.id]
    to_call = min_bet - my_bet

    msg = "{} it's your turn. ".format(user.mention)
    msg += "Check or bet." if to_call == 0 else "{}$ to call.".format(to_call)
    msg += "\n:moneybag: pot: {}".format(sum(match.bets.values()))

    return msg



async def evaluate_match(match):
    # Table cards:
    msg = ""
    for card in match.cards:
        msg += " " + getCard(card)

    # Reveal user cards
    for uid, hand in match.hands.items():
        if hand:
            user = await bot.get_user_info(uid)
            msg += "\n -" + user.name + ": " + getCard(hand[0]) + " " + getCard(hand[1])

    winners, what = betting.evaluate_all(match)

    if len(winners) > 1:
        # todo: split bet
        # todo: find others who split
        msg += "\nTODO: split bet!!!! sorry guys im a half finished bot"

        await bot.say(msg)
    else:
        win_uid = winners[0]

        winner = await bot.get_user_info(win_uid)
        prize = sum(match.bets.values())
        msg += "\nWinner: {} with **{}**\nPot: {}$".format(winner.mention, what[win_uid], prize)

        match.chips[win_uid] += prize

        await bot.say(msg)

        # reset match
        for uid in match.users:
            match.bets[uid] = 0
            match.hands[uid] = None
            match.cards = []

