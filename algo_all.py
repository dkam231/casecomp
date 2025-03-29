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
    "May": 0.0, "June": 0.0, "July": 0.0, "August": 0.0,
    "September": 0.0, "October": 0.0, "November": 0.0, "December": 0.0
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
storage_cost = 0.26      # Storage cost per barrel per month

# Functions for pipeline cost, buying cost and sale price.
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
            return forecasted_houston_WTS[n] - 0.62

# Net profit per barrel for a given route.
def profit(p, m, n, L, S):
    hold = month_index[n] - month_index[m]  # months held
    base_cost = cost_buy(p, m, L)
    transport = pipeline_cost_adjust(p, m, L) if L != S else 0
    sp = sale_price(p, n, S)
    return sp - (base_cost + transport) - storage_cost * hold

# Define decision variables.
buy_locations = ["M", "H"]
sell_options = ["M", "H", "R"]

xplus = {}   # Long trades (buy then sell)
xminus = {}  # Short trades (sell then cover)
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
prob = pulp.LpProblem("Enhanced_FlatBook_Optimization_With_All_Routes", pulp.LpMaximize)

# Objective: maximize total profit over all routes.
obj_terms = []
for p in ["WTI", "WTS"]:
    for L in buy_locations:
        for S in sell_options:
            for m in months:
                for n in months:
                    if month_index[n] < month_index[m]:
                        continue
                    route_profit = profit(p, m, n, L, S)
                    obj_terms.append(route_profit * (xplus[p][L][S][m][n] - xminus[p][L][S][m][n]))
prob += pulp.lpSum(obj_terms)

# Constraints:
# 1. Buying capacity for each product and buy month.
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

# 2. Selling capacity for each product and sell month.
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

# 3. Flat-book constraint: total long equals total short for each product.
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

# 4. Storage (Inventory) constraint for physical inventory.
# Only routes with the same buy and sell location (M=M and H=H) contribute to storage.
for L in buy_locations:
    for t in months:
        inv_terms = []
        for p in ["WTI", "WTS"]:
            for m in months:
                for n in months:
                    if month_index[n] <= month_index[m]:
                        continue
                    if L == "M":
                        # Only consider routes with buy=M and sell=M.
                        if L == "M":
                            if month_index[m] <= month_index[t] and month_index[t] < month_index[n]:
                                inv_terms.append(xplus[p]["M"]["M"][m][n])
                    elif L == "H":
                        # Only consider routes with buy=H and sell=H.
                        if L == "H":
                            if month_index[m] <= month_index[t] and month_index[t] < month_index[n]:
                                inv_terms.append(xplus[p]["H"]["H"][m][n])
        prob += pulp.lpSum(inv_terms) <= 3000000, f"InvCap_{L}_{t}"

# Solve the LP.
solver = pulp.PULP_CBC_CMD(msg=1)
prob.solve(solver)

# Write the output to a file.
with open("output.txt", "w") as f:
    f.write("Status: " + pulp.LpStatus[prob.status] + "\n")
    total_profit = pulp.value(prob.objective)
    f.write(f"Total Maximum Profit: ${total_profit:,.2f}\n\n")
    f.write("All Route Details:\n")
    for p in ["WTI", "WTS"]:
        for L in buy_locations:
            for S in sell_options:
                for m in months:
                    for n in months:
                        if month_index[n] < month_index[m]:
                            continue
                        route_profit = profit(p, m, n, L, S)
                        plus_val = xplus[p][L][S][m][n].varValue
                        minus_val = xminus[p][L][S][m][n].varValue
                        f.write(f"Product: {p}, Route: Buy in {m} at {L} -> Sell in {n} via {S}\n")
                        f.write(f"  Profit per barrel: {route_profit:.4f}\n")
                        f.write(f"  Long volume: {plus_val if plus_val is not None else 0:,.0f} barrels\n")
                        f.write(f"  Short volume: {minus_val if minus_val is not None else 0:,.0f} barrels\n")
                        f.write("-------------------------------------------------\n")
    # Optionally, output a summary of flat-book volumes.
    for p in ["WTI", "WTS"]:
        total_long = sum(xplus[p][L][S][m][n].varValue 
                         for L in buy_locations for S in sell_options 
                         for m in months for n in months 
                         if month_index[n] >= month_index[m] and xplus[p][L][S][m][n].varValue is not None)
        total_short = sum(xminus[p][L][S][m][n].varValue 
                          for L in buy_locations for S in sell_options 
                          for m in months for n in months 
                          if month_index[n] >= month_index[m] and xminus[p][L][S][m][n].varValue is not None)
        f.write(f"\n{p} Summary: Total Long = {total_long:,.0f} barrels, Total Short = {total_short:,.0f} barrels\n")

    f.write("\nMonthly Capacities:\n")
    for p in ["WTI", "WTS"]:
        f.write(f"  {p}:\n")
        for m in months:
            f.write(f"    {m}: {cap[p][m]:,} barrels\n")
