from random import shuffle

from core.dealer import evaluate
from deuces.card import Card


hand = (
    Card.new("Ah"),
    Card.new("Ad"),
)

board = [
    Card.new("Th"),
    Card.new("Td"),
    Card.new("Qh"),
    Card.new("2d"),
    Card.new("5h"),

]

e = evaluate(hand, board)

print(e)