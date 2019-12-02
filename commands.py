import json
import sys

import discord
from discord.ext.commands import Bot

from core import dealer, betting
import model
from thebot import bot, handle_turn, oszt_hand, getErr
from views import numToIcon, getCard


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
async def sit(ctx, cash: int, test=None, *args):
    try:
        player = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        if test:
            player = model.fetch_test_user()
        match = model.fetch(ctx.message.channel.id)


        if cash < match.BB * 20:
            await bot.say("{} you have to sit down with at least {} chips.".format(ctx.message.author.mention, match.BB * 20))
            return

        if player.chips < cash:
            await bot.say("{} you don't have enough chips. You have **{}** $".format(ctx.message.author.mention, player.chips))
            return

        seat = model.sit_user(player, match, cash) + 1

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
async def bet(ctx, cash: int, test=None, *args):
    try:
        player = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        if test:
            player = model.fetch_test_user()
        match = model.fetch(ctx.message.channel.id)

        if match.getCurrentId() != player.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        # todo: mindenfele safety check, return

        min_bet = max(match.bets.values())

        if cash > match.chips[player.uid]:
            await bot.say("{} you can't bet {}$, get more chips mate. You have {}$".format(ctx.message.author.mention, cash, player.chips))
            return

        # if min_bet > 0:
        #     await bot.say("{} you can't bet, raise instead.".format(ctx.message.author.mention, min_bet))
        #     return

        # bet:
        match.chips[player.uid] -= cash
        match.bets[player.uid] += cash

        await handle_turn(match)

    except Exception as e:
        await bot.say(getErr(e))
        raise e


@bot.command(pass_context=True)
async def call(ctx, test=None, *args):
    try:
        player = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        if test:
            player = model.fetch_test_user()
        match = model.fetch(ctx.message.channel.id)

        # todo: mindenfele safety check, return
        if match.getCurrentId() != player.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        min_bet = max(match.bets.values())
        my_bet = match.bets[player.uid]
        to_call = min_bet - my_bet

        if min_bet == 0:
            await bot.say("{} you wanted to check. Don't make me call the floor master.".format(ctx.message.author.mention))
            return

        if to_call > match.chips[player.uid]:
            await bot.say("{} you can't call {}$, get more chips mate. You have {}$".format(ctx.message.author.mention, to_call, player.chips))
            return

        # call the pot:
        match.chips[player.uid] -= to_call
        match.bets[player.uid] += to_call

        await handle_turn(match)

    except Exception as e:
        await bot.say(getErr(e))
        raise e


@bot.command(pass_context=True)
async def check(ctx, test=None, *args):
    try:
        player = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        if test:
            player = model.fetch_test_user()
        match = model.fetch(ctx.message.channel.id)

        # todo: mindenfele safety check, return
        if match.getCurrentId() != player.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        min_bet = max(match.bets.values())
        my_bet = match.bets[player.uid]

        if my_bet < min_bet:
            await bot.say("{} you can't check, call {} at least, or fold.".format(ctx.message.author.mention, min_bet - my_bet))
            return

        await handle_turn(match)


    except Exception as e:
        await bot.say(getErr(e))
        raise e


@bot.command(pass_context=True)
async def fold(ctx, test=None, *args):
    try:
        player = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)
        if test:
            player = model.fetch_test_user()
        match = model.fetch(ctx.message.channel.id)

        # todo: mindenfele safety check, return
        if match.getCurrentId() != player.uid:
            await bot.say("{} it's not your turn!".format(ctx.message.author.mention))
            return

        min_bet = max(match.bets.values())
        my_bet = match.bets[player.uid]

        if my_bet < min_bet:
            await bot.say("{} you need to bet up to {} at least, or fold.".format(player.mention, min_bet))
            return

        await handle_turn(match)


    except Exception as e:
        await bot.say(getErr(e))
        raise e



@bot.command(pass_context=True)
async def uid(ctx, *args):
    player = model.fetch_or_create_user(ctx.message.author.id, ctx.message.author.name)

    await bot.say(player.uid)


if __name__ == "__main__":
    with open('pw.json') as fh:
        conf = json.load(fh)
    bot.run(conf['secret'])
