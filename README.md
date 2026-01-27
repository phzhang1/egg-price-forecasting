# Egg Price Volatility Prediction

Predict monthly egg price ($/dozen) using corn futures, avian flue signals, and seasonality to inform sell vs hold decisions for inventory strategists.

## Business Overview

Eggs are perishable and cold-storage capacity is expensive. When prices move unexpectedly, Inventory Strategists face operational risk: holding inventory too long,
paying for storage they don't need, or selling too early and missing margin opportunities. A reliable one-month price outlook reduces this uncertainty and supports smarter operational planning. 

- **Stakeholder and decision:** Inventory Strategist - determining when to sell vs hold 

- **Business Impact:**
    - Reduce operational risk from mistimed storage decisions
    - Improve planning for storage capacity and logistics
    - Protect margins by anticipating price movements
    - Enhance contract negotiation timing with buyers and suppliers

- **Decision Horizon:** Strategists typically plan inventory movements 2-6 weeks ahead, making a one-month forecast operationally meaningful.

- **Project Goal:** Translate public market signals into a forward-looking price estimate that reduces operational uncertainty.

- **Scope Boundary:**
    - MVP: price-only model using public signals
    - Future Work: Integrate additional operational signals (e.g., weekly inventory counts, fuel prices, weather impacts) using USDA and other public data APIs. 
    
- **Status:** Outline complete; next step: data ingestion and baseline model

## Predictive Objective

- **Target Variable:** Montlhy U.S. egg price ($/dozen)
    - Captures the intersection of supply, demand, disease shocks, feed costs, and market sentiment
    - Represents the actual outcome the strategist care about (revenue per unit)
    - Avoids the trap of predicitng only supply or demand, which would miss half the system

- **Feature Strategy (Leading Factors):**
    - **Core Features (MVP):**
        - Avian flue cases (supply shocks)
        - Corn futures (feed costs)
        - Seasonality (monthly patterns)
    - **Secondary Features (Future Exploration):** 
        - Fuel prices (transportation cost)
        - Weather patterns (flock health, heat stress)
        - Weekly inventory counts (operational constraints)

- **Joining Logic and Preprocessing:**
    - Traget variable is monthly, so all features are aggregated to monthly
    - Lags are created so the model can learn from prior periods 
    - Daily or weekly data is bucketed into monthly averages or sums
    - Zero-filling is used for flue data before 2022 (no outbreaks ≠ missing data)
    - All tables are joined on data after aggregation
    - No imputation of unknown values - avoid injecting artifical signals

## Hypothesis Story
**Hypothesis 1:** When avian flu birds spike, supply tightens and egg prices rise with a lag of ~2-4 weeks
**Hypothesis 2:** When corn futures increases, producers face higher feed costs and prices rise to protect margins
**Hypothesis 3:** Seasonal patterns (holidays, baking seasons) create predictable demand cycles

## ETL Pipeline:
- **Extract:**
    - **FRED API:** Egg CPI, corn futures
    - **USDA HPAI:** Avian flu outbreaks, release dates, birds affected
    - Robust parsing for messy USDA structure (500+ dynamic columns)

- **Transform:**
    - Standarize all sources to monthly frequency
    - Aggregate flu data into:
        - `flu_outbreak_count` (monthly mean)
        - `flu_birds_affected` (monthly mean)
    - Forward/backward fill for economic series
    - Zero-fill for flu data to avoid false signals
    - Outer-join to preserve all months
    - Add month and quarter columns to count for Seasonality
    
- **Load:**
    - Load final dataset into PostgreSQL via SQLAlchemy
    - Dockerized Postgres environment
    - Automatic table creation and date indexing ingestion

## Exploratory Data Analysis 

- **Hypothesis Findings**
    - **Hypothesis 1 (Strong Support): Avian Flu Supply Shocks** 
        - Outbreak spikes consistently precede egg price increases by **1–2 months**.
        - Price impact scales with **birds affected**, confirming strong supply‑side sensitivity.
    - **Hypothesis 2 (Partial Support): Feed Costs (Corn)**
        - **2019-2023:** Corn and egg prices moved together, suggesting feed costs mattered in stable periods.
        - **2024-Present Divergence:** Corn stabilized while egg prices surged, indicating **feed costs are no longer the main driver.** 
    - **Hypothesis 3 (Weak Signal): Seasonal Demand**
        - “Baking season” months do not reliably align with price peaks
        - **Finding:** Largest spikes often occur in **non‑seasonal months**, suggesting demand seasonality is not a dominant factor.

- **Correlation Analysis (Revised After Differencing)**
    - **Raw Price Correlations Were Misleading**
        - Egg price and its 1-month lag showed an extremely high correlation (**0.96**).
        - This created the illusion that most features were strongly predictive simply because prices trend smoothly over time.
        - **Insight:** Raw-price correlations overstated relationships and masked true drivers of volatility.
    - **Differenced Target Reveals True Predictive Signals**
        - After switching to Δ price (month-over-month change):
            - **Outbreak count (News)** became a **strong** predictor than **Birds Affected (Biomass)**.
            - Corn price changes show only a weak relationship (~0.12).
            - Month and Quarter remain low-value features.
    - **Multicollinearity**
        - Flu outbreak count and birds affected are highly correlated.
        - **Modeling Implication:** Remove `flu_birds_affected` to avoid redundant signals and focus on the stronger "Market Panic" signal from `flu_outbreak_count`.
    - **Modeling Implications**
        - **Stationary:** Differencing the target avoids a "lazy model" that achieves high accuracy by simply copying last month's price.
        - **Drivers:** Lagged outbreak frequency becomes the primary external driver, while momentum (`price_diff_lag`) drives the baseline.
        - Feed-cost signals are present but secondary to biological shocks.
        - Seasonality shows little to no signal.

- **Baseline vs Challenger Model:**
    - *To be completed after initial experiments. This section will compare the baseline linear model to a more non linear challenger model (e.g., Random Forest), including performance metrics and trade-offs.*

## Results and Outcomes

- *To be completed after model evaluation. This section will report forecasting accuracy (e.g., RMSE), highlight how well the model captured price trends, and translate performance into business impact for the Inventory Strategist.* -

## What I Learned

- *To be completed after project completion. This section will reflect on key lessons across data sourcing, time‑series feature engineering, model evaluation, and translating technical results into operational insights.*

## Next Steps/Future Work

- *To be completed after initial deployment. This section will outline opportunities to expand the model, integrate additional data sources, improve feature engineering, and explore more advanced forecasting techniques.*