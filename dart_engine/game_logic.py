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

        self.scores     = [starting_score] * self.num_players
        self.leg_scores = [0] * self.num_players
        self.current_player = 0
        self.game_over  = False
        self.winner     = None

        # per-visit stats — includes busts for accurate averages
        self.visit_scores      = [[] for _ in range(self.num_players)]
        self.visit_dart_counts = [[] for _ in range(self.num_players)]
        self.total_darts       = [0]  * self.num_players

    @property
    def averages(self):
        avgs = []
        for i in range(self.num_players):
            visits = self.visit_scores[i]
            if visits:
                avgs.append(round(sum(visits) / len(visits) * 3, 1))
            else:
                avgs.append(0.0)
        return avgs

    def get_score_for_dart(self, notation):
        if not notation or notation in ('', 'miss'):
            return 0
        if notation == 'DB':
            return 50
        if notation == 'SB':
            return 25
        prefix = notation[0]
        try:
            number = int(notation[1:])
        except (ValueError, IndexError):
            return 0
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
        Returns: (visit_score, player_remaining_before_advance, bust, leg_won, game_won)
        """
        if self.game_over:
            return 0, self.scores[self.current_player], False, False, True

        player      = self.current_player
        visit_score = sum(self.get_score_for_dart(d) for d in darts if d)
        remaining   = self.scores[player] - visit_score

        bust     = False
        leg_won  = False
        game_won = False

        if remaining < 0 or remaining == 1:
            bust = True
        elif remaining == 0:
            last = next((d for d in reversed(darts) if d and d != 'miss'), None)
            if last and (last.startswith('D') or last == 'DB'):
                leg_won = True
                self.leg_scores[player] += 1
                self.scores = [self.starting_score] * self.num_players
                if self.leg_scores[player] >= self.num_legs:
                    game_won = True
                    self.game_over = True
                    self.winner = self.player_names[player]
            else:
                bust = True
        else:
            self.scores[player] = remaining

        # Track ALL visits (including busts) for honest averages
        dart_count = len([d for d in darts if d])
        if dart_count > 0:
            self.total_darts[player]  += dart_count
            self.visit_scores[player].append(visit_score / dart_count)
            self.visit_dart_counts[player].append(dart_count)

        if not game_won:
            self.current_player = (self.current_player + 1) % self.num_players

        return visit_score, self.scores[player], bust, leg_won, game_won

    def undo_visit(self, player_idx, previous_score):
        """Revert the last committed visit for player_idx."""
        self.scores[player_idx] = previous_score
        if self.visit_scores[player_idx]:
            self.visit_scores[player_idx].pop()
        if self.visit_dart_counts[player_idx]:
            removed = self.visit_dart_counts[player_idx].pop()
            self.total_darts[player_idx] = max(0, self.total_darts[player_idx] - removed)
        self.current_player = player_idx
