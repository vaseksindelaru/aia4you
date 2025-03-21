"""
Trading simulation and backtesting module.
"""

class TradingSimulator:
    def __init__(self, initial_capital=10000):
        self.capital = initial_capital
        self.positions = {}
        self.history = []

    def execute_trade(self, symbol, action, quantity, price):
        """
        Execute a simulated trade
        """
        if action == "buy":
            cost = quantity * price
            if cost <= self.capital:
                self.capital -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                self.history.append({"action": "buy", "symbol": symbol, 
                                   "quantity": quantity, "price": price})
                return True
        elif action == "sell":
            if symbol in self.positions and self.positions[symbol] >= quantity:
                self.capital += quantity * price
                self.positions[symbol] -= quantity
                self.history.append({"action": "sell", "symbol": symbol, 
                                   "quantity": quantity, "price": price})
                return True
        return False

    def get_portfolio_value(self, current_prices):
        """
        Calculate current portfolio value
        """
        portfolio_value = self.capital
        for symbol, quantity in self.positions.items():
            if symbol in current_prices:
                portfolio_value += quantity * current_prices[symbol]
        return portfolio_value
