

# discord ViewModel for the cards & other stuff
from deuces import Card


def numToIcon(c):
    if c == 0: char = ':zero:'
    elif c == 1: char = ':one:'
    elif c == 2: char = ':two:'
    elif c == 3: char = ':three:'
    elif c == 4: char = ':four:'
    elif c == 5: char = ':five:'
    elif c == 6: char = ':six:'
    elif c == 7: char = ':seven:'
    elif c == 8: char = ':eight:'
    elif c == 9: char = ':nine:'

    return char

def getCard(card: Card):
    return Card.int_to_pretty_str(card)
