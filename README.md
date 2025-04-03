\documentclass{article}
\usepackage{amsmath, amssymb}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{listings}
\usepackage{xcolor}

\lstset{
    language=Python,
    basicstyle=\ttfamily\footnotesize,
    numbers=left,
    stepnumber=1,
    numberstyle=\tiny,
    breaklines=true,
    frame=single,
    showstringspaces=false,
    commentstyle=\color{gray},
    keywordstyle=\color{blue},
    stringstyle=\color{red}
}

\title{Case Competition: Algorithmic Summary of Flat-Book Multi-Route Trading Optimization Model}
\author{Divyam Kamboj}
\date{March 2025}

\begin{document}

\maketitle

\section{Introduction}
This document provides a comprehensive algorithmic and mathematical summary of a flat-book, multi-route trading optimization model. The goal is to route trades (both long and short) across different months, locations, and selling options while ensuring zero net market exposure (a flat book). In addition, the model incorporates various costs, such as pipeline fees, storage costs, and physical inventory constraints. Code snippets are provided (in Python) to illustrate how these mathematical formulations are implemented.

\section{Input Data and Parameters}
\begin{itemize}[label=\textbullet]
    \item \textbf{Monthly Prices:}
    \begin{itemize}[label=--]
        \item Midland prices: \(P^M(m)\) for each month \(m\).
        \item Houston prices: \(P^H(m)\) for each month \(m\).
    \end{itemize}
    \item \textbf{Sour Differentials (for WTS):} \(\Delta_M(m)\) and \(\Delta_H(m)\) for each month \(m\).
    \item \textbf{Forecast Adjustments:} An adjustment is applied to Houston prices for futures routes. (In this example, they are set to 0.)
    \item \textbf{Trading Days and Daily Capacity:} The number of trading days per month and the daily capacities:
    \begin{itemize}[label=--]
        \item WTI: 80,000 barrels per day.
        \item WTS: 20,000 barrels per day.
    \end{itemize}
    \item \textbf{Storage Cost:} \$0.26 per barrel per month held.
    \item \textbf{Pipeline Cost:} A fixed cost of \$0.55 per barrel plus 0.2\% of the effective buying price is applied if the buy and sell locations differ.
    \item \textbf{Inventory Capacity:} Physical storage capacity of 3,000,000 barrels is assumed for each location (Midland and Houston) for trades where the oil is held (i.e. when the buy and sell locations are the same).
\end{itemize}

\section{Derived Data Computation}
\subsection{Monthly Capacity}
For each product \(p\) and month \(m\), the capacity is computed as:
\[
\text{Capacity}_{p}(m) = \text{DailyCapacity}_{p} \times \text{TradingDays}(m)
\]
For example, for WTI in May:
\[
\text{Capacity}_{WTI}(May) = 80,000 \times 20 = 1,600,000 \text{ barrels}
\]
and similarly for WTS.

\subsection{Effective Buying Cost}
The effective buying cost depends on the product and the location where the purchase is made:
\begin{itemize}
    \item \textbf{For WTI:}
    \[
    C_{\text{buy}}^{WTI}(m,L) =
    \begin{cases}
    P^{M}(m) & \text{if } L = M,\\[1mm]
    P^{H}(m) & \text{if } L = H.
    \end{cases}
    \]
    \item \textbf{For WTS:}
    \[
    C_{\text{buy}}^{WTS}(m,L) =
    \begin{cases}
    P^{M}(m) - \Delta_M(m) & \text{if } L = M,\\[1mm]
    P^{H}(m) - \Delta_H(m) & \text{if } L = H.
    \end{cases}
    \]
\end{itemize}

\subsection{Pipeline Cost}
If the buy and sell locations differ, an additional transportation cost is incurred:
\[
\text{PipelineCost}(p, m, L) = 0.55 + 0.002 \times (\text{Effective Buying Price})
\]
For example, for WTI buying in Midland, the effective buying price is \(P^M(m)\).

\subsection{Sale Price}
The sale price depends on the chosen selling option:
\begin{itemize}
    \item \textbf{For WTI:}
    \[
    P_{\text{sell}}^{WTI}(n,S) =
    \begin{cases}
    P^{M}(n) & \text{if } S = M,\\[1mm]
    P^{H}(n) + \text{ForecastAdjustment}(n) & \text{if } S = H,\\[1mm]
    P^{H}(n) + \text{ForecastAdjustment}(n) + 0.05 & \text{if } S = R.
    \end{cases}
    \]
    \item \textbf{For WTS:}
    \[
    P_{\text{sell}}^{WTS}(n,S) =
    \begin{cases}
    P^{M}(n) - \Delta_M(n) & \text{if } S = M,\\[1mm]
    P^{H}(n) - \Delta_H(n) + \text{ForecastAdjustment}(n) & \text{if } S = H,\\[1mm]
    P^{H}(n) - \Delta_H(n) + \text{ForecastAdjustment}(n) - 0.62 & \text{if } S = R.
    \end{cases}
    \]
\end{itemize}

\subsection{Storage Cost}
For a trade that spans from buy month \(m\) to sell month \(n\), the storage cost is:
\[
\text{StorageCost}(m,n) = 0.26 \times (n-m)
\]
with \(n-m\) measured in months.

\section{Profit per Barrel for a Route}
For each product \(p \in \{\text{WTI, WTS}\}\), a route is defined by:
\begin{itemize}
    \item Buy month \(m\) and sell month \(n\) (\(m \le n\)),
    \item Buy location \(L \in \{M,H\}\),
    \item Sell option \(S \in \{M, H, R\}\).
\end{itemize}
The net profit per barrel is calculated by:
\[
\pi(p, m, n, L, S) = P_{\text{sell}}^{p}(n,S) - \Bigl[ C_{\text{buy}}^{p}(m,L) + \mathbf{1}_{\{L\neq S\}}\,\text{PipelineCost}(p,m,L) \Bigr] - \text{StorageCost}(m,n)
\]
where:
\begin{itemize}
    \item \(\mathbf{1}_{\{L\neq S\}} = 1\) if \(L \neq S\) (i.e., if transportation is required) and \(0\) otherwise.
\end{itemize}
\textbf{Interpretation:}
\begin{itemize}
    \item If \(\pi \ge 0\), a long trade (buy then sell) is profitable.
    \item If \(\pi < 0\), then a short trade (sell then cover) is profitable, with profit \( |\pi| \).
\end{itemize}

\section{Flat-Book Trading Constraint}
To maintain zero net market exposure (i.e., a flat book), the following constraint is imposed for each product \(p\):
\[
\sum_{L,S} \sum_{m \le n} x^{p,+}_{L,S}(m,n) = \sum_{L,S} \sum_{m \le n} x^{p,-}_{L,S}(m,n)
\]
where:
\begin{itemize}
    \item \(x^{p,+}_{L,S}(m,n)\) is the volume allocated to a long trade on route \((m,n,L,S)\).
    \item \(x^{p,-}_{L,S}(m,n)\) is the volume allocated to a short trade on that route.
\end{itemize}

\section{Decision Variables (Routing)}
A route is defined by:
\begin{itemize}
    \item Product \(p \in \{\text{WTI, WTS}\}\),
    \item Buy month \(m\) and sell month \(n\) with \(m \le n\),
    \item Buy location \(L \in \{M, H\}\) (Midland or Houston),
    \item Sell option \(S \in \{M, H, R\}\) (Midland, Houston, or Refinery).
\end{itemize}
For each route, we define two sets of continuous decision variables:
\begin{align*}
x^{p,+}_{L,S}(m,n) &\quad \text{(Volume allocated to a long trade)}\\[1mm]
x^{p,-}_{L,S}(m,n) &\quad \text{(Volume allocated to a short trade)}
\end{align*}

\section{Constraints}
\subsection*{Monthly Capacity Constraints}
For each product \(p\) and for each buy month \(m\):
\[
\sum_{L,S} \sum_{n: \, n \ge m} \Bigl( x^{p,+}_{L,S}(m,n) + x^{p,-}_{L,S}(m,n) \Bigr) \le \text{Capacity}_p(m)
\]
Similarly, for each sell month \(n\):
\[
\sum_{L,S} \sum_{m: \, m \le n} \Bigl( x^{p,+}_{L,S}(m,n) + x^{p,-}_{L,S}(m,n) \Bigr) \le \text{Capacity}_p(n)
\]
where
\[
\text{Capacity}_p(m) = \text{DailyCapacity}_p \times \text{TradingDays}(m).
\]

\subsection*{Flat-Book Constraint}
For each product \(p\):
\[
\sum_{L,S} \sum_{m \le n} x^{p,+}_{L,S}(m,n) = \sum_{L,S} \sum_{m \le n} x^{p,-}_{L,S}(m,n)
\]

\subsection*{Storage (Inventory) Constraint (Optional)}
For each physical location \(L \in \{M,H\}\) and each month \(t\), the cumulative inventory from all routes with \(L = S\) that are active during month \(t\) must not exceed 3,000,000 barrels.

\section{Objective Function}
Maximize total profit across all products and all routes:
\[
\text{Maximize } \quad \sum_{p \in \{\text{WTI, WTS}\}} \sum_{L,S} \sum_{m \le n} \pi(p, m, n, L, S) \, \Bigl( x^{p,+}_{L,S}(m,n) - x^{p,-}_{L,S}(m,n) \Bigr)
\]
This objective function ensures:
\begin{itemize}
    \item For routes with \(\pi \ge 0\), the model allocates volume to long trades.
    \item For routes with \(\pi < 0\), volume is allocated as short trades, with profit taken as the absolute value \( |\pi| \).
\end{itemize}

\section{Algorithm Process (Step-by-Step)}
\begin{enumerate}[label=\textbf{Step \arabic*:}, leftmargin=2cm]
    \item \textbf{Data Input:} \\
    Read in monthly prices \(P^M(m)\) and \(P^H(m)\), sour differentials \(\Delta_M(m)\), \(\Delta_H(m)\), forecast adjustments, and trading days. Compute monthly capacities as:
    \[
    \text{Capacity}_p(m) = \text{DailyCapacity}_p \times \text{TradingDays}(m)
    \]
    for each product \(p\).

    \item \textbf{Route Generation:} \\
    Enumerate all possible routes defined by:
    \begin{itemize}
        \item Buy month \(m\) and sell month \(n\) (with \(m \le n\)).
        \item Buy location \(L \in \{M, H\}\).
        \item Sell option \(S \in \{M, H, R\}\).
    \end{itemize}
    
    \item \textbf{Cost and Profit Computation:} \\
    For each route, compute:
    \begin{itemize}
        \item Effective buying cost \(C_{\text{buy}}^{p}(m, L)\).
        \item If \(L \neq S\), add pipeline cost: \(\text{PipelineCost}(p, m, L) = 0.55 + 0.002 \times (\text{Effective Buying Price})\).
        \item Sale price \(P_{\text{sell}}^{p}(n, S)\).
        \item Storage cost: \(\text{StorageCost}(m,n) = 0.26 \times (n-m)\).
        \item Net profit per barrel:
        \[
        \pi(p, m, n, L, S) = P_{\text{sell}}^{p}(n,S) - \Bigl[ C_{\text{buy}}^{p}(m, L) + \mathbf{1}_{\{L \neq S\}}\,\text{PipelineCost}(p, m, L) \Bigr] - 0.26 \times (n-m)
        \]
    \end{itemize}
    
    \item \textbf{LP Decision Variables:} \\
    For each route, define:
    \[
    x^{p,+}_{L,S}(m,n) \quad \text{and} \quad x^{p,-}_{L,S}(m,n)
    \]
    representing the volumes assigned to long and short trades, respectively.

    \item \textbf{Constraints:} \\
    \begin{itemize}
        \item \textbf{Monthly Capacity:} Total volume bought in month \(m\) and sold in month \(n\) must not exceed \(\text{Capacity}_p(m)\) and \(\text{Capacity}_p(n)\) respectively.
        \item \textbf{Flat-Book:} For each product \(p\):
        \[
        \sum_{L,S} \sum_{m \le n} x^{p,+}_{L,S}(m,n) = \sum_{L,S} \sum_{m \le n} x^{p,-}_{L,S}(m,n)
        \]
        \item \textbf{Storage (Inventory):} For each location \(L\) and month \(t\), cumulative active inventory (from routes with \(L=S\)) must be \(\le 3,000,000\) barrels.
    \end{itemize}
    
    \item \textbf{Objective:} \\
    Maximize the total profit:
    \[
    \text{Maximize } \quad \sum_{p,L,S} \sum_{m \le n} \pi(p, m, n, L, S) \Bigl( x^{p,+}_{L,S}(m,n) - x^{p,-}_{L,S}(m,n) \Bigr)
    \]
    
    \item \textbf{LP Solution:} \\
    Solve the linear programming problem using an LP solver (e.g., PuLP's CBC solver). The solution provides:
    \begin{itemize}
        \item The volume allocated to each route.
        \item For routes with \(\pi \ge 0\), these are executed as long trades.
        \item For routes with \(\pi < 0\), these are executed as short trades (with profit reported as \(|\pi|\)).
    \end{itemize}
\end{enumerate}


\section{Conclusion}
In summary, the algorithm:
\begin{itemize}
    \item Computes monthly capacities, effective buying costs, pipeline and storage costs, and sale prices.
    \item Calculates the net profit per barrel for every feasible route defined by buy month, sell month, buy location, and sell option.
    \item Defines LP decision variables for long and short trades for each route.
    \item Imposes capacity constraints, a flat-book constraint (ensuring net zero exposure), and storage constraints (cumulative inventory \(\le\) 3,000,000 barrels at each location).
    \item Maximizes total profit by selecting the optimal mix of long and short trades.
\end{itemize}

The model is solved using a linear programming solver (such as PuLP's CBC solver), and the output provides optimal trade allocations along with the per-barrel profit for each route.

\end{document}
