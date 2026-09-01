# Production Optimization Module

This module will handle:
- Workshop schedule formulation as a Constraint Satisfaction / Mixed Integer Programming problem using Google OR-Tools CP-SAT solver.
- Balancing constraints:
  - Artisan availability and skill matrix (e.g. setter vs polisher vs caster)
  - Machine throughput and maintenance windows
  - Production order batch quantities, priority weights, and hard deadlines
  - Dependency precedence between manufacturing stages.
