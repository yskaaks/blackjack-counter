class GameState:
    def __init__(self):
        self.running_count = 0
        self.true_count = 0.0
        self.seen_cards = [] # List of timestamps/ids to prevent double counting
        self.decks_remaining = 6.0 # Default to 6 decks
    
    def update_count(self, card_rank):
        """
        Updates the count based on Hi-Lo strategy.
        2-6: +1
        7-9: 0
        10, J, Q, K, A: -1
        """
        val = 0
        rank = str(card_rank).upper()
        
        if rank in ['2', '3', '4', '5', '6']:
            val = 1
        elif rank in ['7', '8', '9']:
            val = 0
        elif rank in ['10', 'J', 'Q', 'K', 'A']:
            val = -1
            
        self.running_count += val
        self.calculate_true_count()
        return val

    def calculate_true_count(self):
        if self.decks_remaining > 0:
            self.true_count = self.running_count / self.decks_remaining
        else:
            self.true_count = self.running_count # Fallback

    def set_decks_remaining(self, decks):
        self.decks_remaining = max(0.5, float(decks)) # Avoid division by zero
        self.calculate_true_count()

    def reset(self):
        self.running_count = 0
        self.true_count = 0.0
        self.seen_cards = []
