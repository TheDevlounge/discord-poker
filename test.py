import sys
import asyncio
from eme.entities import EntityPatch
from mock import MagicMock

import model
model.file_loc = "test.json"
model.user_loc = "test_users.json"
model.channels, model.users = model.load()


from thebot import bot

async def bot_say(msg):
    print("    BOT:", msg)

async def bot_send_message(user, msg):
    print("    PRIV {}:".format(user.id), msg)

async def bot_get_user_info(id):
    return ctx_users[id]

def bot_wrapper(pass_context=True):
    def decorator(func):
        def wrapper(ctx, *args, **kwargs):
            print("--->", func.__name__, ctx.message.author.id)
            return func(ctx, *args, **kwargs)
        return wrapper
    return decorator

bot.say = MagicMock(side_effect = bot_say)
bot.get_user_info = MagicMock(side_effect=bot_get_user_info)
bot.command = MagicMock(side_effect=bot_wrapper)
bot.send_message = MagicMock(side_effect=bot_send_message)

from commands import sit, call, check, fold, bet

ctx_users = {
    "U001": EntityPatch({
        "id": "U001",
        "name": "User 1",
        "mention": "@user1"
    }),
    "U002": EntityPatch({
        "id": "U002",
        "name": "User 2",
        "mention": "@user2"
    })
}

ctx_es = [
    EntityPatch({
        "message": EntityPatch({
            "channel": EntityPatch({
               "id": "CHANNEL1"
            }),
            "author": ctx_users["U001"]
        })
    }),
    EntityPatch({
        "message": EntityPatch({
            "channel": EntityPatch({
               "id": "CHANNEL1"
            }),
            "author": ctx_users["U002"]
        })
    })
]


async def runTests():


    await sit(ctx_es[0], 1000)
    await sit(ctx_es[1], 1000)

    await call(ctx_es[0])
    await check(ctx_es[1])

    # flop
    await check(ctx_es[0])
    await check(ctx_es[1])
    # turn
    await check(ctx_es[0])
    await bet(ctx_es[1], 20)
    await bet(ctx_es[0], 50)
    await call(ctx_es[1])

    #await call(ctx_es[0])
    # river
    await check(ctx_es[0])
    await check(ctx_es[1])



if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.run_until_complete(runTests())
