## Tổng hợp theo đồ thị và thuật toán

| dataset | algorithm | n_cases | expanded_mean | expanded_median | expanded_ratio_to_ucs_median | gap_pct_median | gap_pct_max | optimal_pct | runtime_ms_median |
|---|---|---|---|---|---|---|---|---|---|
| B1 | BFS | 56 | 22877.518 | 21501.0 | 1.324 | 32.202 | 122.077 | 5.357 | 11.317 |
| B1 | GBFS | 56 | 311.821 | 145.5 | 0.01 | 33.981 | 73.047 | 5.357 | 0.296 |
| B1 | ASTAR | 56 | 2723.268 | 1891.5 | 0.145 | 0.0 | 0.0 | 100.0 | 3.782 |
| B1 | UCS | 56 | 17228.482 | 17650.0 | 1.0 | 0.0 | 0.0 | 100.0 | 25.183 |
| B2 | BFS | 31 | 1805.323 | 1742.0 | 1.219 | 20.57 | 123.911 | 12.903 | 0.669 |
| B2 | GBFS | 31 | 108.032 | 71.0 | 0.057 | 28.859 | 109.389 | 9.677 | 0.139 |
| B2 | ASTAR | 31 | 443.613 | 268.0 | 0.212 | 0.0 | 0.0 | 100.0 | 0.428 |
| B2 | UCS | 31 | 1620.355 | 1513.0 | 1.0 | 0.0 | 0.0 | 100.0 | 1.561 |

## Tổng hợp theo tính chất ca thử

| dataset | property | algorithm | n_cases | expanded_median | hops_median | path_km_median | gap_pct_median | gap_pct_max |
|---|---|---|---|---|---|---|---|---|
| B1 | easy | BFS | 1 | 448.0 | 16.0 | 1.81 | 0.0 | 0.0 |
| B1 | easy | GBFS | 1 | 17.0 | 16.0 | 1.81 | 0.0 | 0.0 |
| B1 | easy | ASTAR | 1 | 17.0 | 16.0 | 1.81 | 0.0 | 0.0 |
| B1 | easy | UCS | 1 | 552.0 | 16.0 | 1.81 | 0.0 | 0.0 |
| B1 | good_heuristic | BFS | 1 | 36113.0 | 66.0 | 11.028 | 27.664 | 27.664 |
| B1 | good_heuristic | GBFS | 1 | 87.0 | 79.0 | 9.384 | 8.638 | 8.638 |
| B1 | good_heuristic | ASTAR | 1 | 805.0 | 83.0 | 8.638 | 0.0 | 0.0 |
| B1 | good_heuristic | UCS | 1 | 10612.0 | 83.0 | 8.638 | 0.0 | 0.0 |
| B1 | gbfs_trap | BFS | 2 | 33270.0 | 70.0 | 20.563 | 31.722 | 59.547 |
| B1 | gbfs_trap | GBFS | 2 | 4241.5 | 146.5 | 21.414 | 48.915 | 55.409 |
| B1 | gbfs_trap | ASTAR | 2 | 7325.5 | 102.0 | 14.59 | 0.0 | 0.0 |
| B1 | gbfs_trap | UCS | 2 | 26123.0 | 102.0 | 14.59 | 0.0 | 0.0 |
| B1 | bfs_hop_bias | BFS | 1 | 25002.0 | 54.0 | 18.457 | 46.296 | 46.296 |
| B1 | bfs_hop_bias | GBFS | 1 | 169.0 | 159.0 | 17.697 | 40.268 | 40.268 |
| B1 | bfs_hop_bias | ASTAR | 1 | 3133.0 | 115.0 | 12.616 | 0.0 | 0.0 |
| B1 | bfs_hop_bias | UCS | 1 | 18507.0 | 115.0 | 12.616 | 0.0 | 0.0 |
| B1 | distance_scaling | BFS | 3 | 8230.0 | 36.0 | 5.746 | 14.312 | 27.664 |
| B1 | distance_scaling | GBFS | 3 | 53.0 | 52.0 | 5.9 | 8.638 | 17.365 |
| B1 | distance_scaling | ASTAR | 3 | 184.0 | 50.0 | 5.027 | 0.0 | 0.0 |
| B1 | distance_scaling | UCS | 3 | 4187.0 | 50.0 | 5.027 | 0.0 | 0.0 |
| B1 | random | BFS | 48 | 20672.5 | 49.5 | 17.558 | 34.792 | 122.077 |
| B1 | random | GBFS | 48 | 148.0 | 127.5 | 15.803 | 36.777 | 73.047 |
| B1 | random | ASTAR | 48 | 2173.0 | 101.0 | 12.441 | 0.0 | 0.0 |
| B1 | random | UCS | 48 | 18120.5 | 101.0 | 12.441 | 0.0 | 0.0 |
| B2 | easy | BFS | 1 | 55.0 | 9.0 | 1.81 | 0.0 | 0.0 |
| B2 | easy | GBFS | 1 | 10.0 | 9.0 | 1.81 | 0.0 | 0.0 |
| B2 | easy | ASTAR | 1 | 10.0 | 9.0 | 1.81 | 0.0 | 0.0 |
| B2 | easy | UCS | 1 | 99.0 | 9.0 | 1.81 | 0.0 | 0.0 |
| B2 | good_heuristic | BFS | 1 | 1591.0 | 32.0 | 9.258 | 7.182 | 7.182 |
| B2 | good_heuristic | GBFS | 1 | 60.0 | 56.0 | 8.878 | 2.779 | 2.779 |
| B2 | good_heuristic | ASTAR | 1 | 197.0 | 59.0 | 8.638 | 0.0 | 0.0 |
| B2 | good_heuristic | UCS | 1 | 1150.0 | 59.0 | 8.638 | 0.0 | 0.0 |
| B2 | gbfs_trap | BFS | 2 | 1557.0 | 34.0 | 13.876 | 15.055 | 22.691 |
| B2 | gbfs_trap | GBFS | 2 | 324.0 | 51.5 | 16.071 | 35.625 | 38.008 |
| B2 | gbfs_trap | ASTAR | 2 | 573.0 | 36.5 | 11.894 | 0.0 | 0.0 |
| B2 | gbfs_trap | UCS | 2 | 1703.0 | 36.5 | 11.894 | 0.0 | 0.0 |
| B2 | bfs_hop_bias | BFS | 1 | 2723.0 | 40.0 | 15.146 | 21.86 | 21.86 |
| B2 | bfs_hop_bias | GBFS | 1 | 120.0 | 110.0 | 17.338 | 39.501 | 39.501 |
| B2 | bfs_hop_bias | ASTAR | 1 | 577.0 | 63.0 | 12.429 | 0.0 | 0.0 |
| B2 | bfs_hop_bias | UCS | 1 | 2112.0 | 63.0 | 12.429 | 0.0 | 0.0 |
| B2 | distance_scaling | BFS | 3 | 919.0 | 26.0 | 6.266 | 7.182 | 30.495 |
| B2 | distance_scaling | GBFS | 3 | 30.0 | 28.0 | 5.038 | 2.779 | 4.936 |
| B2 | distance_scaling | ASTAR | 3 | 42.0 | 33.0 | 4.801 | 0.0 | 0.0 |
| B2 | distance_scaling | UCS | 3 | 344.0 | 33.0 | 4.801 | 0.0 | 0.0 |
| B2 | random | BFS | 23 | 2210.0 | 36.0 | 15.083 | 20.581 | 123.911 |
| B2 | random | GBFS | 23 | 77.0 | 65.0 | 16.17 | 30.065 | 109.389 |
| B2 | random | ASTAR | 23 | 424.0 | 51.0 | 12.877 | 0.0 | 0.0 |
| B2 | random | UCS | 23 | 2209.0 | 51.0 | 12.877 | 0.0 | 0.0 |

## RQ2: tương quan gap(GBFS) và tỉ lệ vòng

| dataset | n | spearman_rho | p_value |
|---|---|---|---|
| B1 | 54 | 0.371 | 0.0058 |
| B2 | 29 | 0.258 | 0.1759 |

## RQ3: BFS so với UCS

| dataset | group | n | hops_bfs | hops_ucs | km_bfs | km_ucs | gap_pct |
|---|---|---|---|---|---|---|---|
| B1 | C4 | 1 | 54.0 | 115.0 | 18.457 | 12.616 | 46.296 |
| B1 | random (trung vị) | 48 | 49.5 | 101.0 | 17.558 | 12.441 | 34.792 |
| B2 | C4 | 1 | 40.0 | 63.0 | 15.146 | 12.429 | 21.86 |
| B2 | random (trung vị) | 23 | 36.0 | 51.0 | 15.083 | 12.877 | 20.581 |

## RQ4: hệ số góc log(expanded) theo log(d_euclid)

| dataset | algorithm | n | slope | r2 |
|---|---|---|---|---|
| B1 | BFS | 51 | 1.624 | 0.677 |
| B1 | GBFS | 51 | 1.173 | 0.752 |
| B1 | ASTAR | 51 | 2.047 | 0.822 |
| B1 | UCS | 51 | 1.663 | 0.971 |
| B2 | BFS | 26 | 1.728 | 0.881 |
| B2 | GBFS | 26 | 1.152 | 0.715 |
| B2 | ASTAR | 26 | 1.815 | 0.788 |
| B2 | UCS | 26 | 1.648 | 0.972 |

## RQ4: B1 so với B2 trên các đích ngẫu nhiên chung

| algorithm | n_pairs | expanded_b1_median | expanded_b2_median | ratio_b1_b2 |
|---|---|---|---|---|
| BFS | 23 | 17768.0 | 2210.0 | 8.04 |
| GBFS | 23 | 146.0 | 77.0 | 1.9 |
| ASTAR | 23 | 2366.0 | 424.0 | 5.58 |
| UCS | 23 | 17361.0 | 2209.0 | 7.86 |

## Mức A: 132 cặp quận

| dataset | algorithm | n_cases | expanded_mean | expanded_median | expanded_ratio_to_ucs_median | gap_pct_median | gap_pct_max | optimal_pct | runtime_ms_median |
|---|---|---|---|---|---|---|---|---|---|
| A | BFS | 132 | 7.0 | 7.0 | 1.0 | 0.0 | 0.0 | 100.0 | 0.004 |
| A | GBFS | 132 | 3.606 | 3.0 | 0.5 | 0.0 | 38.298 | 83.333 | 0.005 |
| A | ASTAR | 132 | 4.447 | 4.0 | 0.667 | 0.0 | 0.0 | 100.0 | 0.006 |
| A | UCS | 132 | 7.0 | 7.0 | 1.0 | 0.0 | 0.0 | 100.0 | 0.008 |
