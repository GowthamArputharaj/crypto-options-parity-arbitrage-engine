# Live BTC Options Put-Call Parity Arbitrage Scanner

An asynchronous market data parser written in Python. The system listens to live exchange WebSocket channels to evaluate put-call parity violations across concurrent options chains in real time, factoring in order book liquidity and exchange transaction fee schedules.

## Core Architecture & State Management

To avoid performance bottlenecks during high-volume data packet updates, the scanner implements a nested hash map structure:

```python
self.options_cache = {
    "expiry_date": {
        "strike_price": {
            "C": call_packet_dict,
            "P": put_packet_dict
        }
    }
}
```

This state implementation ensures data insertions and matching contract lookups resolve in O(1) time complexity. 

## Arbitrage Mechanics & Calculations

The system continuously verifies the standard European options put-call equilibrium:

\[C + K \cdot e^{-rf \cdot T} = P + S\]

Where:
* **C / P:** Best Ask (Conversion) or Best Bid (Reversal) for Calls and Puts.
* **K:** Strike price parsed from the ticker string.
* **S:** Live underlying Index Spot price (`i`).
* **rf / T:** Annualised risk-free rate (`rf`) and time to maturity computed dynamically against event time (`E`).

### Execution Leg Mapping

To lock in parity spreads while maintaining a zero-delta market-neutral risk profile, the scanner maps the exact order routing paths across three simultaneous legs. The platform automatically tracks whether execution must occur at the active Bid or Ask limit depth:

#### Scenario A: Conversion Arbitrage (Executed when Put is overpriced)
```text
Leg 1 [Option]: Buy Call   -> Order Type: LIMIT BUY  -> Execution Price: Call Ask (ao)
Leg 2 [Option]: Sell Put  -> Order Type: LIMIT SELL -> Execution Price: Put Bid (bo)
Leg 3 [Futures]: Short BTC -> Order Type: MARKET SELL -> Execution Price: Index Spot (i)
```

#### Scenario B: Reversal Arbitrage (Executed when Call is overpriced)
```text
Leg 1 [Option]: Sell Call  -> Order Type: LIMIT SELL -> Execution Price: Call Bid (bo)
Leg 2 [Option]: Buy Put   -> Order Type: LIMIT BUY  -> Execution Price: Put Ask (ao)
Leg 3 [Futures]: Buy BTC   -> Order Type: MARKET BUY  -> Execution Price: Index Spot (i)
```


## Frictional Cost & State Verification Logic

Rather than analyzing raw formula variables, the execution logic isolates the available order book size bottleneck via `min(qty_leg_1, qty_leg_2)` and filters out trades where transaction costs exceed gross margins. 

### Actual Terminal Logs Monitored

```text
 [CONV] Exp:261127 Str:82000 | Size: 1.95 BTC
   Buy Call @ 3065.0, Sell Put @ 7555.0, Short Spot @ 76757.80
   Proof: P_bid($7455.0) + Spot($76955.85) - C_ask($3185.0) - PV_K($81211.47)
   Yield: $21.96 profit/BTC
X  Fees : Total: $75.22 [Spot_Hedging: $38.38 | Call_Taker: $18.42 | Put_Taker: $18.42]
```

### Technical Post-Mortem Analysis

1. **Feed Synchronization Check:** Since data packets are broadcast in bundled arrays, the arrival delta between Call and Put components checks out at exactly `0ms`. The signals are verified as synchronized state updates.
2. **Fee Suppression Barrier:** As documented in the Strike 82,000 log, a gross structural deviation of **\$21.96/BTC** is isolated. 
3. **Execution Decision:** The internal costing function calculates a multi-leg fee overhead of **\$75.22** (composed of a 0.05% linear spot hedge taker fee and dual 0.024% options taker fees capped at 10% of premiums). Because the execution costs exceed the gross yield, the trade is marked with an `X` and safely suppressed from routing layers.