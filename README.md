# Marine Load Optimizer

A Python-based optimization model for efficiently allocating mission-critical gear to marine squads using the Standard Operating Procedure (SOP) datasets. The goal is to maximize utility while considering weight, volume, and item constraints.

## Objective

To assign items across a marine squad of varying sizes and mission durations in a way that:
- Maximizes overall mission utility
- Respects per-marine capacity (weight/volume)
- Meets item requirements, shareability, and transferability rules
- Provides a self-sufficiency score to evaluate loadout effectiveness

## Output
- Console summary table for all configurations
- Per-configuration CSVs with:
- Assigned items per marine
- Objective value
- Self-sufficiency score

## Method
Formulated as a Multiple Knapsack Problem using PuLP:
- Maximizes weighted utility (item value × quantity) adjusted by penalty terms
- Applies item-level and marine-level constraints

## Citation & Attribution
This project is based on the model and problem formulation from:

Jay Simon, Aruna Apte, Eva Regnier
An application of the multiple knapsack problem: The self-sufficient marine
European Journal of Operational Research, Volume 256, Issue 3, 2017, Pages 868–876
DOI: 10.1016/j.ejor.2016.07.039
