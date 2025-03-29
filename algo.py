import pulp

# Define the months and create an index mapping.
months = ["May", "June", "July", "August", "September", "October", "November", "December"]
month_index = {m: i for i, m in enumerate(months)}

# Price data for WTI (physical prices).
midland_price = {
    "May": 70.00, "June": 70.35, "July": 70.70, "August": 70.90,
    "September": 70.90, "October": 70.90, "November": 70.90, "December": 70.90
}
houston_price = {
    "May": 70.65, "June": 71.45, "July": 71.55, "August": 71.35,
    "September": 71.25, "October": 71.25, "November": 71.25, "December": 71.25
}

# Forecast adjustments for Houston prices (in dollars).
forecast_adjustment = {m: 0.0 for m in months}
forecasted_houston_WTI = {m: houston_price[m] + forecast_adjustment[m] for m in months}

# For WTS, define sour differentials (in dollars).
Delta_M = {
    "May": 1.00, "June": 1.00, "July": 0.70, "August": 0.70,
    "September": 0.70, "October": 0.70, "November": 0.70, "December": 0.70
}
Delta_H = {
    "May": 0.75, "June": 0.75, "July": 0.90, "August": 0.90,
    "September": 0.90, "October": 0.90, "November": 0.90, "December": 0.90
}
forecasted_houston_WTS = {m: (houston_price[m] - Delta_H[m]) + forecast_adjustment[m] for m in months}

# Trading days per month and daily capacity.
trading_days = {
    "May": 20, "June": 21, "July": 22, "August": 21,
    "September": 21, "October": 22, "November": 21, "December": 21
}
daily_capacity = {"WTI": 80000, "WTS": 20000}

# Monthly capacity for each product is calculated as daily_capacity * trading_days.
cap = {
    "WTI": {m: daily_capacity["WTI"] * trading_days[m] for m in months},
    "WTS": {m: daily_capacity["WTS"] * trading_days[m] for m in months}
}

# Cost parameters.
pipeline_fixed = 0.55    # Fixed pipeline cost per barrel.
storage_cost = 0.2      # Storage cost per barrel per month for long trades.

# Functions to compute costs and prices.
def pipeline_cost_adjust(p, m, L):
    if p == "WTI":
        price_used = midland_price[m] if L == "M" else houston_price[m]
    else:
        price_used = (midland_price[m] - Delta_M[m]) if L == "M" else (houston_price[m] - Delta_H[m])
    return pipeline_fixed + 0.002 * price_used

def cost_buy(p, m, L):
    if p == "WTI":
        return midland_price[m] if L == "M" else houston_price[m]
    else:
        return (midland_price[m] - Delta_M[m]) if L == "M" else (houston_price[m] - Delta_H[m])

def sale_price(p, n, S):
    if p == "WTI":
        if S == "M":
            return midland_price[n]
        elif S == "H":
            return forecasted_houston_WTI[n]
        elif S == "R":
            return forecasted_houston_WTI[n] + 0.05
    else:
        if S == "M":
            return midland_price[n] - Delta_M[n]
        elif S == "H":
            return forecasted_houston_WTS[n]
        elif S == "R":
            return forecasted_houston_WTI[n] - 0.62

# Profit functions.
def profit_long(p, m, n, L, S):
    # For long trades: storage cost applies.
    hold = month_index[n] - month_index[m]
    base_cost = cost_buy(p, m, L)
    transport = pipeline_cost_adjust(p, m, L) if L != S else 0
    sp = sale_price(p, n, S)
    if hold > 0:
        return sp - (base_cost + transport) - storage_cost * hold +0.06
    return sp - (base_cost + transport)

def profit_short(p, m, n, L, S):
    # For short trades: no storage cost.
    base_cost = cost_buy(p, m, L)
    transport = pipeline_cost_adjust(p, m, L) if L != S else 0
    sp = sale_price(p, n, S)
    return (base_cost + transport) - sp

# Allowed routes.
buy_locations = ["M", "H"]
sell_options = ["M", "H", "R"]

# Define a big-M constant.
BIG_M = max(max(cap["WTI"].values()), max(cap["WTS"].values())) * 10

# Initialize the MIP decision variables.
xplus = {}   # Volume for long trades.
yplus = {}   # Binary selection for long trades.
xminus = {}  # Volume for short trades.
yminus = {}  # Binary selection for short trades.

for p in ["WTI", "WTS"]:
    xplus[p] = {}
    yplus[p] = {}
    xminus[p] = {}
    yminus[p] = {}
    for L in buy_locations:
        xplus[p][L] = {}
        yplus[p][L] = {}
        xminus[p][L] = {}
        yminus[p][L] = {}
        for S in sell_options:
            xplus[p][L][S] = {}
            yplus[p][L][S] = {}
            xminus[p][L][S] = {}
            yminus[p][L][S] = {}
            for m in months:
                xplus[p][L][S][m] = {}
                yplus[p][L][S][m] = {}
                xminus[p][L][S][m] = {}
                yminus[p][L][S][m] = {}
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    var_name_plus = f"xplus_{p}_{L}_{S}_{m}_{n}"
                    var_name_yplus = f"yplus_{p}_{L}_{S}_{m}_{n}"
                    var_name_minus = f"xminus_{p}_{L}_{S}_{m}_{n}"
                    var_name_yminus = f"yminus_{p}_{L}_{S}_{m}_{n}"
                    xplus[p][L][S][m][n] = pulp.LpVariable(var_name_plus, lowBound=0, cat="Continuous")
                    yplus[p][L][S][m][n] = pulp.LpVariable(var_name_yplus, cat="Binary")
                    xminus[p][L][S][m][n] = pulp.LpVariable(var_name_minus, lowBound=0, cat="Continuous")
                    yminus[p][L][S][m][n] = pulp.LpVariable(var_name_yminus, cat="Binary")

# Create the MIP problem.
prob = pulp.LpProblem("Enhanced_FlatBook_MIP_Optimization", pulp.LpMaximize)

# Add linking constraints: if the binary variable is 0, then volume must be 0.
for p in ["WTI", "WTS"]:
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    prob += xplus[p][L][S][m][n] <= BIG_M * yplus[p][L][S][m][n], f"LinkPlus_{p}_{L}_{S}_{m}_{n}"
                    prob += xminus[p][L][S][m][n] <= BIG_M * yminus[p][L][S][m][n], f"LinkMinus_{p}_{L}_{S}_{m}_{n}"

# Objective: maximize total profit.
obj_terms = []
for p in ["WTI", "WTS"]:
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    # For long trades: use profit_long; for short trades: use profit_short.
                    obj_terms.append(profit_long(p, m, n, L, S) * xplus[p][L][S][m][n] -
                                     profit_short(p, m, n, L, S) * xminus[p][L][S][m][n])
prob += pulp.lpSum(obj_terms)

# Buying capacity constraints: for each product and each buy month m.
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

# Selling capacity constraints: for each product and each sell month n.
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

# Flat-book constraint: for each product, total long equals total short.
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

# Storage constraint: for each location (M and H) and each month t, active inventory from routes where buy and sell are the same must be <= 3,000,000 barrels.
for L in buy_locations:
    for t in months:
        terms = []
        for p in ["WTI", "WTS"]:
            # Only consider routes with sell option equal to L.
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    if L == "M":
                        if m <= t and month_index[t] < month_index[n]:
                            terms.append(xplus[p]["M"]["M"][m][n])
                    elif L == "H":
                        if m <= t and month_index[t] < month_index[n]:
                            terms.append(xplus[p]["H"]["H"][m][n])
        prob += pulp.lpSum(terms) <= 3000000, f"InvCap_{L}_{t}"

# Solve the MIP.
solver = pulp.PULP_CBC_CMD(msg=1)
prob.solve(solver)

print("Status:", pulp.LpStatus[prob.status])
total_profit = pulp.value(prob.objective)
print(f"Total Maximum Profit: ${total_profit:,.2f}\n")

print("Executed Trades (Routes with nonzero volume):")
for p in ["WTI", "WTS"]:
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    plus_val = xplus[p][L][S][m][n].varValue
                    minus_val = xminus[p][L][S][m][n].varValue
                    if (plus_val is not None and plus_val > 1e-3) or (minus_val is not None and minus_val > 1e-3):
                        route_profit_long = profit_long(p, m, n, L, S)
                        route_profit_short = profit_short(p, m, n, L, S)
                        # For output, label sell option "R" as "Refinery (H)"
                        sell_label = S if S != "R" else "Refinery (H)"
                        if plus_val is not None and plus_val > 1e-3:
                            print(f"  LONG: Buy {p} in {m} at {L} and Sell in {n} via {sell_label}: {plus_val:,.0f} barrels; Profit/barrel: ${route_profit_long:.4f}")
                        if minus_val is not None and minus_val > 1e-3:
                            print(f"  SHORT: Sell {p} in {m} at {L} and Cover in {n} via {sell_label}: {minus_val:,.0f} barrels; Profit/barrel: ${route_profit_short:.4f}")

# Optional: Summary of flat-book volumes.
for p in ["WTI", "WTS"]:
    total_long = sum(xplus[p][L][S][m][n].varValue 
                     for L in buy_locations for S in sell_options 
                     for m in months for n in months if month_index[n] >= month_index[m] and xplus[p][L][S][m][n].varValue is not None)
    total_short = sum(xminus[p][L][S][m][n].varValue 
                      for L in buy_locations for S in sell_options 
                      for m in months for n in months if month_index[n] >= month_index[m] and xminus[p][L][S][m][n].varValue is not None)
    print(f"{p} Summary: Total Long = {total_long:,.0f} barrels, Total Short = {total_short:,.0f} barrels")
