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

- **Correlation Findings (Statistical Validation)**
    - **Market Memory (Autocorrelation)**
        - Egg price vs. 1-month lag shows a correlation of **0.96**.
        - Indicates extremely high price persistence.
        - **Modeling Implication:** Raw price forecasting risks becoming a "lazy model" that simply copies last month's value. Differencing the target (predicting change in price) will help the model learn real drivers.
    - **Biological Supply Shocks vs. Economic Inputs**
        - Birds affected show a strong correlation (**0.65**) with egg prices.
        - Introducing a 1-month flu lag strengthens the relationship further (**0.72**).
        - Corn prices show a weaker relationship (**0.23**).
        - **Modeling Implication:** Flu severity, especially with lag, is the dominant predictive signal; feed costs are secondary.
    - **Seasonality**
        - Month are quarter correlations are week (0.11)
        - **Modeling Implications:** Seasonality adds little predictive value and can be deprioritized or dropped.
    - **Multicollinearity**
        - Flu Outbreak and Flu Birds Affected are **highly correlated** which means that they encode the same underlying signal. 
        - **Model Implications:** Remove `flu_outbreak_count` to avoid redundant features and reduce noise during training.

- **Baseline vs Challenger Model:**
    - *To be completed after initial experiments. This section will compare the baseline linear model to a more non linear challenger model (e.g., Random Forest), including performance metrics and trade-offs.*

## Results and Outcomes

- *To be completed after model evaluation. This section will report forecasting accuracy (e.g., RMSE), highlight how well the model captured price trends, and translate performance into business impact for the Inventory Strategist.* -

## What I Learned

- *To be completed after project completion. This section will reflect on key lessons across data sourcing, time‑series feature engineering, model evaluation, and translating technical results into operational insights.*

## Next Steps/Future Work

- *To be completed after initial deployment. This section will outline opportunities to expand the model, integrate additional data sources, improve feature engineering, and explore more advanced forecasting techniques.*