import pulp

# Define the months and create an index mapping
months = ["May", "June", "July", "August", "September", "October", "November", "December"]
month_index = {m: i for i, m in enumerate(months)}

# Price data for WTI (physical prices)
midland_price = {
    "May": 70.00, "June": 70.35, "July": 70.70, "August": 70.90,
    "September": 70.90, "October": 70.90, "November": 70.90, "December": 70.90
}
houston_price = {
    "May": 70.65, "June": 71.45, "July": 71.55, "August": 71.35,
    "September": 71.25, "October": 71.25, "November": 71.25, "December": 71.25
}

# Forecast adjustments for Houston prices (in dollars)
forecast_adjustment = {
    "May": 0.0, "June": 0.0, "July": 0.0, "August": -0.0,
    "September": -0.0, "October": -0.0, "November": -0.0, "December": 0.0
}
# Forecasted Houston prices for WTI (futures trades)
forecasted_houston_WTI = {m: houston_price[m] + forecast_adjustment[m] for m in months}

# For WTS, define sour differentials (in dollars)
Delta_M = {
    "May": 1.00, "June": 1.00, "July": 0.70, "August": 0.70,
    "September": 0.70, "October": 0.70, "November": 0.70, "December": 0.70
}
Delta_H = {
    "May": 0.75, "June": 0.75, "July": 0.90, "August": 0.90,
    "September": 0.90, "October": 0.90, "November": 0.90, "December": 0.90
}
# Forecasted Houston prices for WTS (futures route): subtract differential then add forecast adjustment.
forecasted_houston_WTS = {m: (houston_price[m] - Delta_H[m]) + forecast_adjustment[m] for m in months}

# Trading days per month (assumed based on allowed trading hours)
trading_days = {
    "May": 20, "June": 21, "July": 22, "August": 21,
    "September": 21, "October": 22, "November": 21, "December": 21
}
# Daily capacity limits:
daily_capacity = {"WTI": 80000, "WTS": 20000}

# Monthly capacity for each product is calculated as daily capacity * trading_days.
cap = {
    "WTI": {m: daily_capacity["WTI"] * trading_days[m] for m in months},
    "WTS": {m: daily_capacity["WTS"] * trading_days[m] for m in months}
}

# Cost parameters
pipeline_fixed = 0.55    # Fixed pipeline cost per barrel
storage_cost = 0.26      # Storage cost per barrel per month (0.03 in + 0.03 out plus additional cost)

# Functions to compute costs and prices
def pipeline_cost_adjust(p, m, L):
    # If buying in location L, use the corresponding price.
    if p == "WTI":
        price_used = midland_price[m] if L == "M" else houston_price[m]
    else:  # WTS
        price_used = (midland_price[m] - Delta_M[m]) if L == "M" else (houston_price[m] - Delta_H[m])
    return pipeline_fixed + 0.002 * price_used

def cost_buy(p, m, L):
    # Cost of buying depends on the location.
    if p == "WTI":
        return midland_price[m] if L == "M" else houston_price[m]
    else:  # WTS
        return (midland_price[m] - Delta_M[m]) if L == "M" else (houston_price[m] - Delta_H[m])

def sale_price(p, n, S):
    # Sale price depends on the selling option.
    if p == "WTI":
        if S == "M":
            return midland_price[n]
        elif S == "H":
            return forecasted_houston_WTI[n]
        elif S == "R":
            return forecasted_houston_WTI[n] + 0.05
    else:  # WTS
        if S == "M":
            return midland_price[n] - Delta_M[n]
        elif S == "H":
            return forecasted_houston_WTS[n]
        elif S == "R":
            return forecasted_houston_WTI[n] - 0.62

# Profit per barrel for a given route: product p, buy month m, sell month n, buy location L, sell option S.
def profit(p, m, n, L, S):
    hold = month_index[n] - month_index[m]  # number of months held
    base_cost = cost_buy(p, m, L)
    # If the buy and sell locations differ, add pipeline cost.
    transport = pipeline_cost_adjust(p, m, L) if L != S else 0
    sp = sale_price(p, n, S)
    return sp - (base_cost + transport) - storage_cost * hold

# Define decision variables.
# Allowed routes: Buy location L in {M,H} and Sell option S in {M,H,R}.
buy_locations = ["M", "H"]
sell_options = ["M", "H", "R"]

# Decision variables for long (xplus) and short (xminus) trades.
xplus = {}
xminus = {}
for p in ["WTI", "WTS"]:
    xplus[p] = {}
    xminus[p] = {}
    for L in buy_locations:
        xplus[p][L] = {}
        xminus[p][L] = {}
        for S in sell_options:
            xplus[p][L][S] = {}
            xminus[p][L][S] = {}
            for m in months:
                xplus[p][L][S][m] = {}
                xminus[p][L][S][m] = {}
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    var_name_plus = f"xplus_{p}_{L}_{S}_{m}_{n}"
                    var_name_minus = f"xminus_{p}_{L}_{S}_{m}_{n}"
                    xplus[p][L][S][m][n] = pulp.LpVariable(var_name_plus, lowBound=0, cat="Continuous")
                    xminus[p][L][S][m][n] = pulp.LpVariable(var_name_minus, lowBound=0, cat="Continuous")

# Create the LP problem.
prob = pulp.LpProblem("Enhanced_FlatBook_Optimization_With_Storage", pulp.LpMaximize)

# Objective: maximize total profit across all routes.
obj_terms = []
for p in ["WTI", "WTS"]:
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    route_profit = profit(p, m, n, L, S)
                    # For long trade: profit is route_profit (if positive).
                    # For short trade: profit is -route_profit (if route_profit is negative).
                    obj_terms.append(route_profit * (xplus[p][L][S][m][n] - xminus[p][L][S][m][n]))
prob += pulp.lpSum(obj_terms)

# Constraints:
# 1. Buying capacity: For each product and each buy month m, total barrels traded (long + short) across all routes starting in m <= cap[p][m].
for p in ["WTI", "WTS"]:
    for m in months:
        terms = []
        for L in buy_locations:
            for S in sell_options:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    terms.append(xplus[p][L][S][m][n] + xminus[p][L][S][m][n])
        prob += pulp.lpSum(terms) <= cap[p][m], f"BuyCap_{p}_{m}"

# 2. Selling capacity: For each product and each sell month n, total barrels delivered across all routes ending in n <= cap[p][n].
for p in ["WTI", "WTS"]:
    for n in months:
        terms = []
        for L in buy_locations:
            for S in sell_options:
                for m in months:
                    if month_index[n] < month_index[m]:
                        continue
                    terms.append(xplus[p][L][S][m][n] + xminus[p][L][S][m][n])
        prob += pulp.lpSum(terms) <= cap[p][n], f"SellCap_{p}_{n}"

# 3. Flat-book constraint: For each product, total long volume equals total short volume.
for p in ["WTI", "WTS"]:
    long_total = []
    short_total = []
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    long_total.append(xplus[p][L][S][m][n])
                    short_total.append(xminus[p][L][S][m][n])
    prob += pulp.lpSum(long_total) == pulp.lpSum(short_total), f"FlatBook_{p}"

# 4. Storage (Inventory) capacity constraint:
# We assume that only trades with the same buy and sell location cause physical inventory to be held at that location.
# For each location L and for each month t, sum all long trades that start in month m and end in month n (with m < n)
# that are active (i.e. m <= t < n) must be <= 3,000,000 barrels.
for L in buy_locations:  # This applies separately for Midland (M) and Houston (H)
    for t in months:
        terms = []
        for p in ["WTI", "WTS"]:
            # Only consider routes with S equal to the same location as L.
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    if L != "M" and L != "H":
                        continue
                    # Only count if route uses same buy and sell location: L == S.
                    # Also, only count if the trade is held during month t, i.e. m <= t < n.
                    if n != m:  # Only trades spanning multiple months involve storage.
                        if m <= t and month_index[t] < month_index[n]:
                            terms.append(xplus[p][L][L][m][n])
        prob += pulp.lpSum(terms) <= 3000000, f"InvCap_{L}_{t}"

# Solve the LP.
solver = pulp.PULP_CBC_CMD(msg=1)
prob.solve(solver)

# Output the results.
print("Status:", pulp.LpStatus[prob.status])
total_profit = pulp.value(prob.objective)
print(f"Total Maximum Profit: ${total_profit:,.2f}\n")

# Report each nonzero trade with appropriate labeling.
sum=0
for p in ["WTI", "WTS"]:
    print(f"Trade allocations for {p}:")
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    route_profit = profit(p, m, n, L, S)
                    plus_val = xplus[p][L][S][m][n].varValue
                    minus_val = xminus[p][L][S][m][n].varValue
                    # If route_profit is positive, a long trade is profitable.
                    if plus_val is not None and plus_val > 1e-3 and route_profit >= 0:
                        sum+=route_profit*plus_val
                        print(f"  LONG: Buy {p} in {m} at {L} and Sell in {n} via {S}: {plus_val:,.0f} barrels; Profit per barrel: ${route_profit:.4f}")
                    # If route_profit is negative, display a short trade with profit as the absolute value.
                    if minus_val is not None and minus_val > 1e-3 and route_profit < 0:
                        sum+=route_profit*(-minus_val)
                        print(f"  SHORT: Sell {p} in {m} at {L} and Cover in {n} via {S}: {minus_val:,.0f} barrels; Profit per barrel: ${abs(route_profit):.4f}")
    print("")
    
print("Monthly Capacities:")
for p in ["WTI", "WTS"]:
    print(f"  {p}:")
    for m in months:
        print(f"    {m}: {cap[p][m]:,} barrels")
print(sum)