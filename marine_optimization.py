"""
Marine Squad Load Optimization (based on Multiple Knapsack Problem)

This project is adapted from the model in:
"An Application of the Multiple Knapsack Problem: The Self-Sufficient Marine"
by Jay Simon, Aruna Apte, Eva Regnier
Published in European Journal of Operational Research, 2017

This implementation solves an integer programming formulation that distributes
supply items among Marines (knapsacks), subject to capacity and operational constraints.
"""

import pandas as pd
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpInteger, PULP_CBC_CMD, value
import os

# Load datasets
hot_df = pd.read_csv("hot_sop_dataset.csv")
cold_df = pd.read_csv("cold_sop_dataset.csv")
params = pd.read_csv("optimization_parameters.csv")

# Extract model parameters from the parameter CSV
param_dict = params.set_index('Parameter')['Value'].to_dict()
w_base = float(param_dict.get('w', 100)) # Weight capacity per Marine
q_base = float(param_dict.get('q', 75)) # Volume capacity per Marine (cubic units)
beta = float(param_dict.get('beta', 0.2)) # Weight penalty coefficient
gamma = float(param_dict.get('gamma', 0.001)) # Volume penalty coefficient

# Create folder to save output files
os.makedirs("results", exist_ok=True)

# Optimization function
def run_sop_optimization(df, K, duration, scenario):
    print(f"{scenario} | Squad={K} | Duration={duration}...", flush=True)

    # Standardize column names to expected internal names
    df = df.rename(columns={
        'Item': 'item', 'Value_b': 'b', 'Weight_c': 'c', 'Volume_v': 'v',
        'Transferable_t': 't', 'LowerBound_l': 'l', 'Requirement_r': 'r', 'Shareable_a': 'a'
    })

    # Scale requirement and constraints based on mission duration
    df['r'] *= duration
    df['l'] *= duration
    w = w_base * duration   # total weight capacity
    q = max(q_base * duration, df['v'].sum() / K) # total volume capacity

    # Filter infeasible items
    df = df[(df['a'] <= df['r']) & ~((df['t'] == 0) & (df['r'] < K))]

    # Precompute utility coefficient
    df['coef'] = df.apply(lambda row: row['b'] * row['a'] / row['r'] if row['r'] > 0 else 0, axis=1)

    # Define model
    model = LpProblem("Marine_Load_Optimization", LpMaximize)

    # Decision variables: number of item i assigned to Marine k
    Xik = {(i, k): LpVariable(name=f"x_{i}_{k}", cat=LpInteger, lowBound=0)
           for i in df.index for k in range(K)}

    # Objective function: maximize utility minus weight/volume penalties
    utility_term = lpSum(df.loc[i, 'coef'] * lpSum(Xik[i, k] for k in range(K)) for i in df.index)
    weight_penalty = beta * lpSum(df.loc[i, 'c'] * Xik[i, k] for i in df.index for k in range(K))
    volume_penalty = gamma * lpSum(df.loc[i, 'v'] * Xik[i, k] for i in df.index for k in range(K))
    model += utility_term - weight_penalty - volume_penalty

    # Constraints: Marine capacity limits
    for k in range(K):
        model += lpSum(df.loc[i, 'c'] * Xik[i, k] for i in df.index) <= w
        model += lpSum(df.loc[i, 'v'] * Xik[i, k] for i in df.index) <= q

    # Constraints: Item usage limits
    for i in df.index:
        model += lpSum(Xik[i, k] for k in range(K)) <= int(df.loc[i, 'r'] / df.loc[i, 'a'])
        model += lpSum(df.loc[i, 'a'] * Xik[i, k] for k in range(K)) >= df.loc[i, 'l']
        for k in range(K):
            model += (1 - df.loc[i, 't']) * Xik[i, k] <= 1

    # Solve the model using CBC solver (max 60s per scenario)
    model.solve(PULP_CBC_CMD(msg=0, timeLimit=60))

    # Compute scores
    actual_utility = sum(
        df.loc[i, 'b'] * df.loc[i, 'a'] * Xik[i, k].varValue
        for i in df.index for k in range(K) if Xik[i, k].varValue
    )
    ideal_utility = (df['b'] * df['r']).sum()
    score = actual_utility / ideal_utility if ideal_utility > 0 else 0
    obj_val = value(model.objective)

    # Display allocation result
    result_df = pd.DataFrame([
        {'Item': df.loc[i, 'item'], 'Marine': k + 1, 'Quantity': int(Xik[i, k].varValue)}
        for i in df.index for k in range(K)
        if Xik[i, k].varValue and Xik[i, k].varValue > 0
    ])
    print(result_df.to_string(index=False))
    print(f"Objective: {obj_val:.2f} | Self-Sufficiency Score: {score:.3f} ({score*100:.1f}%)\n")

    # Save allocation to CSV
    filename = f"{scenario.lower().replace(' ', '_')}_k{K}_d{duration}.csv"
    filepath = os.path.join("results", filename)
    result_df.to_csv(filepath, index=False)
    print(f"Saved detailed allocation to: {filepath}\n")

    return {
        "Scenario": scenario,
        "SquadSize": K,
        "Duration": duration,
        "Objective": round(obj_val, 2),
        "SelfSufficiencyScore": round(score, 4),
        "ScorePercent": f"{score * 100:.1f}%"
    }

# Run optimization for multiple combinations of squad size and duration
results = []
for K in [4, 8, 12]:
    for duration in [2, 3, 4]:
        results.append(run_sop_optimization(hot_df.copy(), K, duration, "Hot SOP"))
        results.append(run_sop_optimization(cold_df.copy(), K, duration, "Cold SOP"))

# Output summary
summary_df = pd.DataFrame(results)
print("\nSummary:")
print(summary_df.to_string(index=False))

# Save full summary
summary_path = os.path.join("results", "sop_summary_results.csv")
summary_df.to_csv(summary_path, index=False)
print(f"\nSummary saved to: {summary_path}")