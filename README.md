

# Case Competition: Algorithmic Summary of Flat-Book Multi-Route Trading Optimization Model

**Author:** Divyam Kamboj  
**Date:** March 2025

## 📌 Introduction
This project provides a comprehensive **algorithmic and mathematical summary** of a flat-book, multi-route trading optimization model. The objective is to **route trades (long and short)** across different months, locations, and sell options **while maintaining zero net market exposure (flat book)**.

The model accounts for:
- Pipeline and storage costs  
- Inventory limits  
- Forecast adjustments  

Python code (using LP solvers like PuLP) implements the model for practical optimization.

---

## 📊 Input Data and Parameters

- **Monthly Prices:**
  - Midland: `P^M(m)`
  - Houston: `P^H(m)`
- **Sour Differentials (for WTS):**
  - Midland: `Δ_M(m)`, Houston: `Δ_H(m)`
- **Forecast Adjustments:**  
  Applied to Houston prices for futures routes (set to 0 in this example)
- **Trading Days & Daily Capacity:**
  - WTI: 80,000 barrels/day  
  - WTS: 20,000 barrels/day
- **Storage Cost:** `$0.26` per barrel per month held
- **Pipeline Cost:** `$0.55` fixed + `0.2%` of effective buying price if buying and selling locations differ
- **Inventory Capacity:**  
  3,000,000 barrels per location (Midland, Houston)

---

## 🧠 Derived Data Computation

### Monthly Capacity
```math
Capacity_p(m) = DailyCapacity_p × TradingDays(m)
```

### Effective Buying Cost
For WTI:
```math
C_buy^WTI(m, L) = P^M(m) or P^H(m)
```
For WTS:
```math
C_buy^WTS(m, L) = P^M(m) - Δ_M(m) or P^H(m) - Δ_H(m)
```

### Pipeline Cost
If `L ≠ S`:
```math
PipelineCost = 0.55 + 0.002 × EffectiveBuyingPrice
```

### Sale Price
Includes adjustments and premiums/discounts for refinery routes:
```math
P_sell^WTI(n, S) = P^M(n), P^H(n) + adj., or P^H(n) + adj. + 0.05
P_sell^WTS(n, S) = P^M(n) - Δ_M(n), etc.
```

### Storage Cost
```math
StorageCost(m, n) = 0.26 × (n - m)
```

---

## 💰 Profit Per Barrel for a Route
```math
π(p, m, n, L, S) = SalePrice - [BuyPrice + PipelineCost (if any)] - StorageCost
```

- If `π ≥ 0`: profitable long trade
- If `π < 0`: profitable short trade (profit = `|π|`)

---

## 📏 Flat-Book Constraint
To ensure zero net exposure:
```math
∑ x^+ = ∑ x^−
```
For every product `p`, the total volume of long trades equals that of short trades.

---

## 🔁 Decision Variables (Routing)

Each route is defined by:
- Product: WTI or WTS  
- Buy Month `m`, Sell Month `n`  
- Buy Location `L`: Midland or Houston  
- Sell Option `S`: Midland, Houston, or Refinery  

**Decision Variables:**
- `x^+_{L,S}(m,n)`: long trade volume  
- `x^-_{L,S}(m,n)`: short trade volume  

---

## ✅ Constraints

### Monthly Capacity
For every month `m` (buy) and `n` (sell):
```math
∑ x^+ + x^- ≤ Capacity_p(m or n)
```

### Flat-Book
```math
∑ x^+ = ∑ x^−
```

### Inventory Constraint (Optional)
Cumulative barrels stored at each location should not exceed 3,000,000 per month.

---

## 🎯 Objective Function
Maximize total profit:
```math
Maximize ∑ π(p, m, n, L, S) × (x^+ - x^-)
```
Allocate long trades for positive profits and short trades for negative profits (i.e., positive arbitrage opportunities).

---

## ⚙️ Step-by-Step Algorithm

### Step 1: Data Input
- Load all prices, trading days, and cost parameters
- Compute monthly capacities

### Step 2: Route Generation
- Enumerate all possible routes `(m, n, L, S)`

### Step 3: Profit Computation
For each route, calculate:
- Effective buying cost  
- Pipeline cost (if needed)  
- Sale price  
- Storage cost  
- Net profit `π`

### Step 4: Define Decision Variables
- For each route, define `x^+` and `x^-`

### Step 5: Add Constraints
- Monthly capacity  
- Flat-book  
- Optional storage constraint

### Step 6: Set Objective
- Maximize:
```math
∑ π × (x^+ - x^-)
```

### Step 7: Solve LP
- Use an LP solver like **PuLP's CBC** to solve for optimal volumes

---

## ✅ Conclusion

This model:
- Computes trading and storage economics for multiple oil grades and routes  
- Maintains net market neutrality via flat-book constraint  
- Uses linear programming to select the most profitable trade volumes  
- Can be extended with additional constraints like inventory rollover, dynamic pricing, etc.

---

Let me know if you'd like this in a file or need a sample Python script as part of the `README.md`.
