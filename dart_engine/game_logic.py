"""
Game logic for x01 dart games (501, 301, etc.)
Supports double-out, bust detection, multi-player, multi-leg.
"""


class GameLogic:
    def __init__(self, ruleset='x01', player_names=None, starting_score=501, num_legs=1):
        self.ruleset = ruleset
        self.player_names = player_names or ['Player 1']
        self.num_players = len(self.player_names)
        self.starting_score = starting_score
        self.num_legs = num_legs

        self.scores = [starting_score] * self.num_players
        self.leg_scores = [0] * self.num_players
        self.current_player = 0
        self.game_over = False
        self.winner = None

        # history for averages
        self.visit_scores = [[] for _ in range(self.num_players)]
        self.total_darts = [0] * self.num_players

    @property
    def averages(self):
        avgs = []
        for i in range(self.num_players):
            visits = self.visit_scores[i]
            if visits:
                avgs.append(sum(visits) / len(visits) * 3)  # per-dart avg × 3 = visit avg
            else:
                avgs.append(0.0)
        return avgs

    def get_score_for_dart(self, notation):
        if not notation or notation == '' or notation == 'miss':
            return 0
        if notation == 'DB':
            return 50
        if notation == 'SB':
            return 25
        prefix = notation[0]
        number = int(notation[1:])
        if prefix == 'S':
            return number
        if prefix == 'D':
            return number * 2
        if prefix == 'T':
            return number * 3
        return 0

    def commit_visit(self, darts):
        """
        darts: list of notation strings e.g. ['T20', 'S5', 'D16']
        Returns: (score_this_visit, new_remaining, bust, leg_won, game_won)
        """
        if self.game_over:
            return 0, self.scores[self.current_player], False, False, True

        visit_score = sum(self.get_score_for_dart(d) for d in darts if d)
        remaining = self.scores[self.current_player] - visit_score

        bust = False
        leg_won = False
        game_won = False

        if remaining < 0 or remaining == 1:
            bust = True
            # score doesn't change on bust
        elif remaining == 0:
            # must finish on a double or bullseye (DB)
            last = next((d for d in reversed(darts) if d and d != 'miss'), None)
            if last and (last.startswith('D') or last == 'DB'):
                leg_won = True
                self.leg_scores[self.current_player] += 1
                self.scores = [self.starting_score] * self.num_players
                if self.leg_scores[self.current_player] >= self.num_legs:
                    game_won = True
                    self.game_over = True
                    self.winner = self.player_names[self.current_player]
            else:
                bust = True
        else:
            self.scores[self.current_player] = remaining

        if not bust:
            dart_count = len([d for d in darts if d])
            self.total_darts[self.current_player] += dart_count
            per_dart = visit_score / dart_count if dart_count else 0
            self.visit_scores[self.current_player].append(per_dart)

        # advance player
        if not game_won:
            self.current_player = (self.current_player + 1) % self.num_players

        return visit_score, self.scores[self.current_player - 1 if not game_won else self.current_player], bust, leg_won, game_won

    def undo_visit(self, player_idx, previous_score):
        """Revert a committed visit."""
        self.scores[player_idx] = previous_score
        if self.visit_scores[player_idx]:
            self.visit_scores[player_idx].pop()
        self.current_player = player_idx
