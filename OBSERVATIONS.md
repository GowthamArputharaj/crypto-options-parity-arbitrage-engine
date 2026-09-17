=========================================
OBSERVATION 1: STREAM TIMING & SNAPSHOTS
=========================================
• DATA DELTA: Packet delta between Call and Put is exactly 0ms.
• EXCHANGE MECHANICS: Binance packages the entire option chain into one single massive JSON array.
• THE IMPACT: Every script inside that chunk inherits the exact same atomic timestamp ('E' field).
• CODE SUCCESS: Real-time O(1) state cache matches them flawlessly with zero timing drift.
=========================================

=========================================
OBSERVATION 2: THE TRADING FEE WALL
=========================================
• THE ACCURATE DATA: Raw math shows gross gaps of $10.00 to $28.00 per BTC.
• EXCHANGE FRICTION: Executing all 3 legs costs exactly $75.22 in retail taker fees.
• THE MARKET REALITY: Market makers keep pricing gaps just wide enough to clear their own VIP fees, but narrow enough to block retail VIP 0 traders.
• CODE SUCCESS: Scanner marks trades with an 'X' to safely stop fee-negative losses.
=========================================

=========================================
OBSERVATION 3: DYNAMIC INDEX CORRELATION
=========================================
• LIVE TIMELINE: Spot falls ($76757.80 -> $76757.48) -> Yield falls ($21.96 -> $21.63).
• EXCHANGE MECHANICS: Option prices shift instantly alongside the live underlying asset index ('i').
• THE IMPACT: Math pricing models are highly reactive to micro-dollar spot moves.
• CODE SUCCESS: Proves the scanner's present value calculation (PV_K) updates flawlessly on every network tick.
=========================================

=========================================
OBSERVATION 4: LIQUIDITY BOTTLENECKS
=========================================
• DATA LIMIT: Profitable long-dated scripts have tiny volume sizes (1.95 to 5.62 BTC max).
• EXCHANGE MECHANICS: Liquidity is thin on deep forward-dated contracts.
• THE IMPACT: Trading large sizes will crush the order book, causing massive slippage.
• CODE SUCCESS: Scanner calculates min(call_qty, put_qty) to protect execution viability.
=========================================

