import asyncio
from datetime import datetime
import json
import math

class ParityArbitrageScanner:

    def __init__(self, latency_threshold_ms=50.0, min_profit_usd=5.0):
        # Nested Cache Structure: options_cache[expiry][strike][type] = payload
        self.options_cache = {}
        # Strict constraints to impress recruiters
        self.latency_threshold_ms = latency_threshold_ms
        self.min_profit_usd = min_profit_usd

    def parse_symbol(self, symbol_str):
        """Extract Expiry, Strike, and Type from Symbol String (e.g., BTC-260925-80000-P)"""
        parts = symbol_str.split("-")
        expiry = parts[1]  # '260925'
        strike = float(parts[2])  # 80000.0
        opt_type = parts[3]  # 'C' or 'P'
        return expiry, strike, opt_type

    def calculate_time_to_expiry(self, expiry_str, timestamp_ms):
        """Dynamically computes T (in years) between Event Time E and Expiry String Date"""
        current_time = datetime.fromtimestamp(timestamp_ms / 1000.0)
        expiry_time = datetime.strptime(expiry_str, "%y%m%d").replace(
            hour=8, minute=0, second=0
        )  # Crypto options typically expire at 08:00 UTC

        time_delta_seconds = (expiry_time - current_time).total_seconds()
        # Ensure T is not zero or negative
        T = max(time_delta_seconds / (365.25 * 24 * 60 * 60), 0.00001)
        return T

    def process_packet(self, data):
        """Processes an incoming JSON dictionary tick from the WebSocket stream"""
        symbol = data["s"]
        expiry, strike, opt_type = self.parse_symbol(symbol)

        # Initialize dictionary levels dynamically
        if expiry not in self.options_cache:
            self.options_cache[expiry] = {}
        if strike not in self.options_cache[expiry]:
            self.options_cache[expiry][strike] = {"C": None, "P": None}

        # Update cache with fresh stream data
        self.options_cache[expiry][strike][opt_type] = data

        # Check for matching pair twin
        twin_type = "P" if opt_type == "C" else "C"
        twin_data = self.options_cache[expiry][strike][twin_type]

        if not twin_data:
            return  # Wait until the opposite contract hits the stream cache

        # Run parity engine check using current and twin data
        call_data = data if opt_type == "C" else twin_data
        put_data = data if opt_type == "P" else twin_data
        
        if abs(call_data["E"] - put_data["E"]) > self.latency_threshold_ms:  # Must be within 10 milliseconds!
            return  # Ignore stale data
        self.evaluate_parity_violation(expiry, strike, call_data, put_data)
    
    def calculate_binance_fees(self, spot_price, c_price, p_price):
        """Computes the exact 3-leg fee breakdown considering Binance caps"""
        spot_fee = spot_price * 0.0005  # 0.05% Futures Taker Fee
        base_opt_fee = spot_price * 0.00024  # 0.024% Option Taker Fee
        
        # Apply 10% premium cap to option fees
        call_fee = min(base_opt_fee, c_price * 0.10)
        put_fee = min(base_opt_fee, p_price * 0.10)
        
        total_fees = spot_fee + call_fee + put_fee
        return total_fees, spot_fee, call_fee, put_fee

    def is_arbitrage_profitable(self, gross_profit, total_fees):
        """Checks if the gross yield survives exchange fees and meets your minimum threshold"""
        net_profit = gross_profit - total_fees
        return net_profit > self.min_profit_usd, net_profit

    def evaluate_parity_violation(self, expiry, strike, call, put):
        """Executes the corrected mathematical parity checks against the order books"""

        # 1. Extract pricing elements from payloads
        S = float(call["i"])    # Spot Index Price
        rf = float(call["rf"])  # Risk-free rate
        T = self.calculate_time_to_expiry(expiry, call["E"])

        # Order Book Levels 
        c_bid, c_ask = float(call["bo"]), float(call["ao"])
        p_bid, p_ask = float(put["bo"]), float(put["ao"])
        
        # Order Book Sizes
        c_bid_qty, c_ask_qty = float(call["bq"]), float(call["aq"])
        p_bid_qty, p_ask_qty = float(put["bq"]), float(put["aq"])

        # Discount Factor: e^(-rf * T)
        present_value_of_strike = strike * math.exp(-rf * T)

        # =========================================================================
        # 2. TEST A: Conversion Arbitrage (Put is overpriced)
        # Real Cash Flow: + P_bid + S - C_ask - PV(Strike)
        # =========================================================================
        conversion_profit = p_bid + S - c_ask - present_value_of_strike
        
        if conversion_profit > self.min_profit_usd:
            # Liquidity check: Must be able to buy Call and sell Put
            max_size = min(c_ask_qty, p_bid_qty)
            
            if max_size > 0.0:  # Ignore dead order books with 0 liquidity
                total_fees, s_fee, c_fee, p_fee = self.calculate_binance_fees(S, c_ask, p_bid)
                is_viable, net_profit = self.is_arbitrage_profitable(conversion_profit, total_fees)
                #
                print(f"   [CONV] Exp:{expiry} Str:{strike:.0f} | Size: {max_size:.2f} BTC")
                print(f"   Buy Call @ {c_ask}, Sell Put @ {p_bid}, Short Spot @ {S:.2f}")
                print(f"   Proof: P_bid(${p_bid}) + Spot(${S:.2f}) - C_ask(${c_ask}) - PV_K(${present_value_of_strike:.2f})")
                print(f"   Yield: ${conversion_profit:.2f} profit/BTC -> ROUTE: Buy Call / Sell Put / Short Spot")
                if is_viable:
                    print(f"   Fees : Total: ${total_fees:.2f} [Spot_Hedging: ${s_fee:.2f} | Call_Taker: ${c_fee:.2f} | Put_Taker: ${p_fee:.2f}]")
                else:
                    print(f"X  Fees : Total: ${total_fees:.2f} [Spot_Hedging: ${s_fee:.2f} | Call_Taker: ${c_fee:.2f} | Put_Taker: ${p_fee:.2f}]")
                print("-" * 10)

        # =========================================================================
        # 3. TEST B: Reversal Arbitrage (Call is overpriced)
        # Real Cash Flow: + C_bid - P_ask - S + PV(Strike)
        # =========================================================================
        reversal_profit = c_bid - p_ask - S + present_value_of_strike
        
        if reversal_profit > self.min_profit_usd:
            # Liquidity check: Must be able to sell Call and buy Put
            max_size = min(c_bid_qty, p_ask_qty)
            
            if max_size > 0.0:  # Ignore dead order books with 0 liquidity
                total_fees, s_fee, c_fee, p_fee = self.calculate_binance_fees(S, c_bid, p_ask)
                is_viable, net_profit = self.is_arbitrage_profitable(reversal_profit, total_fees)
                
                print(f"  [REVR] Exp:{expiry} K:{strike:.0f} | Size: {max_size:.2f} BTC | Spot: ${S:.2f}")
                print(f"   Sell Call @ {c_bid}, Buy Put @ {p_ask}, Buy Spot @ {S:.2f}")
                print(f"   Proof: C_bid(${c_bid}) - P_ask(${p_ask}) - Spot(${S:.2f}) + PV_K(${present_value_of_strike:.2f})")
                print(f"   Yield: ${reversal_profit:.2f} profit/BTC -> ROUTE: Sell Call / Buy Put / Buy Spot")
                if is_viable:
                    print(f"   Fees : Total: ${total_fees:.2f} [Spot_Hedging: ${s_fee:.2f} | Call_Taker: ${c_fee:.2f} | Put_Taker: ${p_fee:.2f}]")
                else:
                    print(f"X  Fees : Total: ${total_fees:.2f} [Spot_Hedging: ${s_fee:.2f} | Call_Taker: ${c_fee:.2f} | Put_Taker: ${p_fee:.2f}]")
                print("-" * 10)
