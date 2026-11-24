# Noise history

All noise figures in dB relative to the signal (noise minus the 1 kHz gain), 20 Hz-20 kHz unless a band is given. SNR and THD are for a -30 dBFS-peak 1 kHz drive.
\* gain borrowed from housing_250 (same housing, bias and supply; its THD at 1 kHz was 0.455%).

| stage | run | gain_1k_db | noise_dbfs | noise_re_signal_db | noise_a_re_signal_db | snr_at_-30dbfs_drive_db | hum50_re_signal_db | 20_300hz_db | 300_2500hz_db | 2500_5000hz_db | 5k_20khz_db | thd_1k_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Old op-amp, code 500 | 20261024-121433_dac_all_500 | 9.0 | -72.9 | -81.9 | -84.6 | 48.9 | -97.3 | -86.7 | -88.1 | -92.2 | -86.7 | 0.511 |
| MCP6002 + C10, code 2048 | 20261102-223002_c10_fitted | -2.1 | -72.6 | -70.5 | -72.3 | 37.5 | -90.1 | -78.3 | -78.9 | -76.3 | -74.1 | 0.072 |
| New 12 V supply | 20261102-224430_new_supply | -3.2 | -78.3 | -75.1 | -79.4 | 42.1 | -90.6 | -78.5 | -83.9 | -87.2 | -79.6 | 0.628 |
| Housing, code 250 | 20261103-110608_housing_r13_250 | 28.2 * | -56.3 | -84.5 | -86.6 | 51.5 | -94.8 | -91.9 | -96.3 | -90.5 | -87.5 |  |
| 9 V battery | 20261103-112302_battery9v_r13_250 | 28.2 * | -59.0 | -87.3 | -92.9 | 54.3 | -91.8 | -90.0 | -96.9 | -101.3 | -92.2 |  |
| Laptop off charger | 20261103-112627_battery9v_laptopbatt_r13_250 | 28.2 * | -63.0 | -91.2 | -94.2 | 58.2 | -110.4 | -99.5 | -99.1 | -102.1 | -93.4 |  |

LED off (pickup + preamp floor, 20261103-110542_housing_r13_0) at the housing gain: -121.5 dB re signal.
