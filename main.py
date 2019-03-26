import json
import sys

import discord
from discord.ext.commands import Bot, bot

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

def getErr(e):
    str0 = "{} at line {} [{}]".format(str(e), sys.exc_info()[-1].tb_lineno, type(e).__name__)

    return str0


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

    `:x: po refill` - gives you 1000 chips
    `:x: po wassup` - lists your stats and history

    ------------
    **Poker room:**

    `po sit <amount>` - sits in channel with amount in chips
    `:x: po leave` - sits out of channel
    `:x: po time` - forces the current player to flop if they're out of time

    `:x: po call` - calls minimum bet
    `:x: po check` - checks
    `:x: po bet <amount>` - bets or raises amount in chips. 
    `:x: po fold` - folds cards
    
    """
    return await bot.say(_help)



@bot.command(pass_context=True)
async def setchannel(ctx, BB: int=50, *args):
    try:
        match = model.fetch_or_create(ctx.message.channel.id, ctx.message.channel.name)
        match.setBB(BB)
        model.save()

        await bot.say("Registered this channel {} as poker room!".format(match.name))


    except Exception as e:
        getErr(e)


@bot.command(pass_context=True)
async def sit(ctx, cash: int, *args):
    try:
        user = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        match = model.fetch(ctx.message.channel.id)

        if user.chips < cash:
            await bot.say("{} you don't have enough chips. You have **{}** $".format(ctx.message.author.mention, user.chips))

            return

        seat = model.sit_user(user, match, cash) + 1

        if seat is None:
            # user is present or we get err, w/e
            return

        model.save()

        await bot.say("{} {} has sit down with **{}** $".format(numToIcon(seat), ctx.message.author.mention, cash))


        if seat == 2:
            # match has started
            current, n_cards = match.dealer.new_round(len(match.users))

            #await bot.say("Table has started with 2 seats.")
            await oszt_hand(match, n_cards)


    except Exception as e:
        await bot.say(getErr(e))
        raise e



@bot.command(pass_context=True)
async def bet(ctx, cash: int, *args):
    try:
        user = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        match = model.fetch(ctx.message.channel.id)

        if match.getCurrentId() != user.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return


        # todo: mindenfele safety check, return

        min_bet = max(match.bets.values())

        if cash > match.chips[user.uid]:
            await bot.say("{} you can't bet {}$, get more chips mate. You have {}$".format(ctx.message.author.mention, cash, user.chips))
            return

        if min_bet > 0:
            await bot.say("{} you can't bet, raise instead.".format(ctx.message.author.mention, min_bet))
            return

        # bet:
        match.chips[user.uid] -= cash
        match.bets[user.uid] += cash

        await handle_turn(match)

    except Exception as e:
        await bot.say(getErr(e))
        raise e


@bot.command(pass_context=True)
async def call(ctx, *args):
    try:
        user = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        match = model.fetch(ctx.message.channel.id)

        # todo: mindenfele safety check, return
        if match.getCurrentId() != user.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        min_bet = max(match.bets.values())
        my_bet = match.bets[user.uid]
        to_call = min_bet - my_bet

        if to_call > match.chips[user.uid]:
            await bot.say("{} you can't call {}$, get more chips mate. You have {}$".format(ctx.message.author.mention, to_call, user.chips))
            return

        # call the pot:
        match.chips[user.uid] -= to_call
        match.bets[user.uid] += to_call

        await handle_turn(match)

    except Exception as e:
        await bot.say(getErr(e))
        raise e


@bot.command(pass_context=True)
async def check(ctx, *args):
    try:
        user = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        match = model.fetch(ctx.message.channel.id)

        # todo: mindenfele safety check, return
        if match.getCurrentId() != user.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        min_bet = max(match.bets.values())
        my_bet = match.bets[user.uid]

        if my_bet < min_bet:
            await bot.say("{} you can't check, bet up to {} at least, or fold.".format(ctx.message.author.mention, min_bet))
            return

        await handle_turn(match)


    except Exception as e:
        await bot.say(getErr(e))
        raise e


@bot.command(pass_context=True)
async def fold(ctx, *args):
    try:
        user = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        match = model.fetch(ctx.message.channel.id)

        # todo: mindenfele safety check, return
        if match.getCurrentId() != user.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        min_bet = max(match.bets.values())
        my_bet = match.bets[user.uid]

        if my_bet < min_bet:
            await bot.say("{} you need to bet up to {} at least, or fold.".format(user.mention, min_bet))
            return

        await handle_turn(match)


    except Exception as e:
        await bot.say(getErr(e))
        raise e


# # # # # # # # #
#     LIB       #
# # # # # # # # #

async def handle_turn(match: model.Match):
    try:
        N = len(match.users)
        state, n_cards = match.dealer.next_turn()

        if state == 'reset':
            # shift dealer role
            match.users.append(match.users.pop)

            return

        if state == 'hand' and n_cards is not None:
            await oszt_hand(match, n_cards)

            return

        if n_cards is None:
            # state didn't change, next player comes
            user = await bot.get_user_info(match.getCurrentId())

            await bot.say("{} it's your turn. Current bet is: {} $. ".format(user.mention, max(match.bets.values())))

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

            await bot.say(msg)

            return

        else:
            # Evaluate cards

            # Table cards:
            msg = ""
            for card in match.cards:
                msg += " " + getCard(card)

            # Reveal user cards
            for uid, hand in match.hands.items():
                if hand:
                    user = await bot.get_user_info(uid)
                    msg += "\n *" + user.name + ": " + getCard(hand[0]) + " " + getCard(hand[1])

            winners, what = betting.evaluate_all(match)

            if len(winners) > 1:
                # todo: split bet
                # todo: find others who split
                msg += "\nTODO: split bet!!!! sorry guys im a half finished bot"

                await bot.say(msg)
                return
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

        current_id = match.getCurrentId()
        current_user = await bot.get_user_info(current_id)
        user_BB = await bot.get_user_info(BB_uid)
        user_SB = await bot.get_user_info(SB_uid)

        msg = "Hands dealt.\n"
        msg += "**Current turn:** {}\n".format(current_user.mention)
        msg += "BB: {}, SB: {}, Blinds: {}".format(user_BB.name, user_SB.name, match.BB)

        await bot.say(msg)

    except Exception as e:
        raise e
        #getErr(e)


if __name__ == "__main__":
    with open('pw.json') as fh:
        conf = json.load(fh)
    bot.run(conf['secret'])
