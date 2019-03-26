from deuces.deck import Deck

import faker

fake = faker.Faker("en_GB")


class Dealer():

    """Texas Hold'em dealer"""
    def __init__(self):
        self.deck = None
        self.state = 'waiting'
        self.states = []
        self.turn_iter = None
        self.rounds = 0
        self.N = 0
        self.cards_dealt = 0
        self.name = fake.name()
        self.current = None

    def deal(self, N):

        return self.deck.draw(N)

    def new_round(self, N):
        self.deck = Deck()
        self.N = N
        self.turn_iter = iter(range(N))
        self.states = [
            ('hand', 2),
            ('flop', 3), ('turn', 1), ('river', 1),
            ('evaluate', 0)
        ]
        self.state, self.cards_dealt = self.states.pop(0)
        self.current = next(self.turn_iter)

        return self.current, self.cards_dealt

    def next_turn(self):
        try:
            self.current = next(self.turn_iter)

            return self.state, None

        except StopIteration:
            # None means that there are no more people in the round
            self.current = 0
            self.turn_iter = iter(range(self.N))

            # turn ends => new state
            self.state, self.cards_dealt = self.states.pop(0)

            if self.state == 'evaluate':
                # dealer asks to be reset
                self.rounds += 1

            return self.state, self.cards_dealt
