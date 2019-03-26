

# betting logic
# + bet splitting, etc
from deuces import Evaluator
from model import Match

# hand evaluation
evaluator = Evaluator()

def evaluate(hand, board=None):
    # if board is None:
    #     # 1 array
    #     cards = [Card.new(c) for c in hand]
    #     hand, board = cards[:2], cards[2:]
    # else:
    #     # 2 arrays
    #     hand = [Card.new(c) for c in hand]
    #     board = [Card.new(c) for c in board]

    score = evaluator.evaluate(list(hand), list(board))
    hclass = evaluator.get_rank_class(score)

    return score, evaluator.class_to_string(hclass)


def evaluate_all(match: Match):
    points = {}
    what = {}

    for uid, hand in match.hands.items():
        if hand:
            points[uid], what[uid] = evaluate(hand, match.cards)

    min_uid = min(points, key=points.get)
    min_point1 = points.pop(min_uid)

    min_uid2 = min(points, key=points.get)
    min_point2 = points.get(min_uid2)

    if min_point1 == min_point2:
        winners = {min_uid}

        for uid in points:
            winners.add(uid)

        return list(winners), what
    else:

        return [min_uid], what
