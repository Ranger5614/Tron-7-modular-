"""
High-performance technical indicators with Numba JIT compilation

All indicators are vectorized and Numba-compiled for maximum speed.
Typical speedup: 20-50x faster than pandas-based implementations.

Usage:
    from encom.indicators import rsi, macd, atr, bollinger_bands, vwap, adx

    # Calculate RSI for entire series at once
    rsi_values = rsi(df['close'].values, period=14)

    # Calculate MACD
    macd_line, signal_line, histogram = macd(df['close'].values)

    # Calculate Bollinger Bands
    middle, upper, lower = bollinger_bands(df['close'].values)

    # Calculate VWAP (requires OHLCV)
    vwap_values = vwap(df['high'].values, df['low'].values,
                       df['close'].values, df['volume'].values)

    # Calculate ADX (trend strength)
    adx_values = adx(df['high'].values, df['low'].values, df['close'].values)
"""

from encom.indicators.momentum import (
    rsi, macd, ema, sma, stochastic,
    cci, williams_r, roc, ultimate_oscillator, cmo, ppo, tsi,
    rsi_nb, macd_nb, ema_nb, sma_nb, stochastic_nb,
    cci_nb, williams_r_nb, roc_nb, ultimate_oscillator_nb, cmo_nb, ppo_nb, tsi_nb
)

from encom.indicators.volatility import (
    atr, bollinger_bands, std_dev, keltner_channels,
    atr_nb, bollinger_bands_nb, std_dev_nb, keltner_channels_nb
)

from encom.indicators.volume import (
    vwap, obv, ad, cmf, mfi, volume_roc,
    vwap_nb, obv_nb, ad_nb, cmf_nb, mfi_nb, volume_roc_nb
)

from encom.indicators.trend import (
    adx, di, psar, supertrend, aroon, true_range,
    adx_nb, di_nb, psar_nb, supertrend_nb, aroon_nb, true_range_nb
)

from encom.indicators.overlap import (
    wma, hma, kama, dema, tema, t3, zlema, vwma, trima, midpoint, midprice,
    wma_nb, hma_nb, kama_nb, dema_nb, tema_nb, t3_nb, zlema_nb, vwma_nb,
    trima_nb, midpoint_nb, midprice_nb
)

from encom.indicators.statistical import (
    correlation, covariance, beta, variance, skewness, kurtosis, zscore,
    linear_regression, linear_regression_slope, linear_regression_angle,
    linear_regression_intercept, tsf, standard_error,
    correlation_nb, covariance_nb, beta_nb, variance_nb, skewness_nb, kurtosis_nb, zscore_nb,
    linear_regression_nb, linear_regression_slope_nb, linear_regression_angle_nb,
    linear_regression_intercept_nb, tsf_nb, standard_error_nb
)

from encom.indicators.price_transform import (
    avgprice, medprice, typprice, wclprice, hlc3, ohlc4, hl2, hlcc4,
    avgprice_nb, medprice_nb, typprice_nb, wclprice_nb, hlc3_nb, ohlc4_nb, hl2_nb, hlcc4_nb
)

from encom.indicators.support_resistance import (
    pivot_points, fibonacci_retracement, fibonacci_extension, swing_high_low, fractal, donchian_channel,
    pivot_points_nb, fibonacci_retracement_nb, fibonacci_extension_nb, swing_high_low_nb, fractal_nb, donchian_channel_nb
)

from encom.indicators.advanced_momentum import (
    trix, bop, apo, kst, dpo, fisher_transform, ao, ac,
    trix_nb, bop_nb, apo_nb, kst_nb, dpo_nb, fisher_transform_nb, ao_nb, ac_nb
)

from encom.indicators.advanced_volatility import (
    historical_volatility, ulcer_index, chaikin_volatility, natr, true_range, mass_index, price_channels,
    historical_volatility_nb, ulcer_index_nb, chaikin_volatility_nb, natr_nb, true_range_nb, mass_index_nb, price_channels_nb
)

from encom.indicators.hilbert_transform import (
    ht_trendline, ht_dcperiod, ht_dcphase, ht_phasor, ht_sine, ht_trendmode, ht_leadsine,
    ht_trendline_nb, ht_dcperiod_nb, ht_dcphase_nb, ht_phasor_nb, ht_sine_nb, ht_trendmode_nb
)

from encom.indicators.pattern_recognition import (
    engulfing_pattern, doji_pattern, hammer_pattern, morning_evening_star, three_soldiers_crows,
    engulfing_pattern_nb, doji_pattern_nb, hammer_pattern_nb, morning_evening_star_nb, three_soldiers_crows_nb
)

from encom.indicators.market_profile import (
    point_of_control, value_area, volume_profile,
    point_of_control_nb, value_area_nb, volume_profile_nb
)

from encom.indicators.order_flow import (
    delta_volume, cumulative_volume_delta, aggressive_ratio, volume_pace,
    delta_volume_nb, cumulative_volume_delta_nb, aggressive_ratio_nb, volume_pace_nb
)

from encom.indicators.advanced_volume import (
    volume_roc as volume_roc_adv, klinger_volume_oscillator, ease_of_movement,
    negative_volume_index, positive_volume_index,
    volume_roc_nb as volume_roc_adv_nb, klinger_volume_oscillator_nb, ease_of_movement_nb,
    negative_volume_index_nb, positive_volume_index_nb
)

from encom.indicators.candlestick_patterns import (
    shooting_star, piercing_dark_cloud, harami, marubozu, spinning_top, three_inside, tweezer,
    shooting_star_nb, piercing_dark_cloud_nb, harami_nb, marubozu_nb, spinning_top_nb, three_inside_nb, tweezer_nb
)

from encom.indicators.oscillators import (
    stochastic_rsi, relative_vigor_index, psychological_line, aroon_oscillator,
    commodity_selection_index, detrended_oscillator, trend_intensity_index, momentum_oscillator,
    rate_of_change_ratio, smoothed_rate_of_change, intraday_momentum_index,
    stochastic_rsi_nb, relative_vigor_index_nb, psychological_line_nb, aroon_oscillator_nb,
    commodity_selection_index_nb, detrended_oscillator_nb, trend_intensity_index_nb, momentum_oscillator_nb,
    rate_of_change_ratio_nb, smoothed_rate_of_change_nb, intraday_momentum_index_nb
)

from encom.indicators.bands_channels import (
    envelope, starc_bands, price_channel_bands, median_price_bands,
    typical_price_bands, weighted_close_bands, acceleration_bands, high_low_bands,
    envelope_nb, starc_bands_nb, price_channel_bands_nb, median_price_bands_nb,
    typical_price_bands_nb, weighted_close_bands_nb, acceleration_bands_nb, high_low_bands_nb
)

from encom.indicators.composite import (
    choppiness_index, mcginley_dynamic, kaufman_efficiency_ratio, vertical_horizontal_filter,
    linear_regression_bands, price_oscillator, force_index, elder_force_index,
    chande_forecast_oscillator, center_of_gravity, linear_weighted_ma, variable_ma,
    triangular_ma, std_dev_channels, ease_of_movement_value,
    relative_momentum_index, qstick_indicator, volatility_ratio, market_facilitation_index,
    choppiness_index_nb, mcginley_dynamic_nb, kaufman_efficiency_ratio_nb, vertical_horizontal_filter_nb,
    linear_regression_bands_nb, price_oscillator_nb, force_index_nb, elder_force_index_nb,
    chande_forecast_oscillator_nb, center_of_gravity_nb, linear_weighted_ma_nb, variable_ma_nb,
    triangular_ma_nb, std_dev_channels_nb, ease_of_movement_value_nb,
    relative_momentum_index_nb, qstick_indicator_nb, volatility_ratio_nb, market_facilitation_index_nb
)

__all__ = [
    # Momentum indicators
    "rsi", "macd", "ema", "sma", "stochastic",
    "cci", "williams_r", "roc", "ultimate_oscillator", "cmo", "ppo", "tsi",
    "rsi_nb", "macd_nb", "ema_nb", "sma_nb", "stochastic_nb",
    "cci_nb", "williams_r_nb", "roc_nb", "ultimate_oscillator_nb", "cmo_nb", "ppo_nb", "tsi_nb",

    # Volatility indicators
    "atr", "bollinger_bands", "std_dev", "keltner_channels",
    "atr_nb", "bollinger_bands_nb", "std_dev_nb", "keltner_channels_nb",

    # Volume indicators
    "vwap", "obv", "ad", "cmf", "mfi", "volume_roc",
    "vwap_nb", "obv_nb", "ad_nb", "cmf_nb", "mfi_nb", "volume_roc_nb",

    # Trend indicators
    "adx", "di", "psar", "supertrend", "aroon", "true_range",
    "adx_nb", "di_nb", "psar_nb", "supertrend_nb", "aroon_nb", "true_range_nb",

    # Overlap/Moving Average indicators
    "wma", "hma", "kama", "dema", "tema", "t3", "zlema", "vwma", "trima", "midpoint", "midprice",
    "wma_nb", "hma_nb", "kama_nb", "dema_nb", "tema_nb", "t3_nb", "zlema_nb", "vwma_nb",
    "trima_nb", "midpoint_nb", "midprice_nb",

    # Statistical/Regression indicators
    "correlation", "covariance", "beta", "variance", "skewness", "kurtosis", "zscore",
    "linear_regression", "linear_regression_slope", "linear_regression_angle",
    "linear_regression_intercept", "tsf", "standard_error",
    "correlation_nb", "covariance_nb", "beta_nb", "variance_nb", "skewness_nb", "kurtosis_nb", "zscore_nb",
    "linear_regression_nb", "linear_regression_slope_nb", "linear_regression_angle_nb",
    "linear_regression_intercept_nb", "tsf_nb", "standard_error_nb",

    # Price Transform indicators
    "avgprice", "medprice", "typprice", "wclprice", "hlc3", "ohlc4", "hl2", "hlcc4",
    "avgprice_nb", "medprice_nb", "typprice_nb", "wclprice_nb", "hlc3_nb", "ohlc4_nb", "hl2_nb", "hlcc4_nb",

    # Support/Resistance indicators
    "pivot_points", "fibonacci_retracement", "fibonacci_extension", "swing_high_low", "fractal", "donchian_channel",
    "pivot_points_nb", "fibonacci_retracement_nb", "fibonacci_extension_nb", "swing_high_low_nb", "fractal_nb", "donchian_channel_nb",

    # Advanced Momentum indicators
    "trix", "bop", "apo", "kst", "dpo", "fisher_transform", "ao", "ac",
    "trix_nb", "bop_nb", "apo_nb", "kst_nb", "dpo_nb", "fisher_transform_nb", "ao_nb", "ac_nb",

    # Advanced Volatility indicators
    "historical_volatility", "ulcer_index", "chaikin_volatility", "natr", "true_range", "mass_index", "price_channels",
    "historical_volatility_nb", "ulcer_index_nb", "chaikin_volatility_nb", "natr_nb", "true_range_nb", "mass_index_nb", "price_channels_nb",

    # Hilbert Transform indicators (Cycle Analysis)
    "ht_trendline", "ht_dcperiod", "ht_dcphase", "ht_phasor", "ht_sine", "ht_trendmode", "ht_leadsine",
    "ht_trendline_nb", "ht_dcperiod_nb", "ht_dcphase_nb", "ht_phasor_nb", "ht_sine_nb", "ht_trendmode_nb",

    # Pattern Recognition indicators
    "engulfing_pattern", "doji_pattern", "hammer_pattern", "morning_evening_star", "three_soldiers_crows",
    "engulfing_pattern_nb", "doji_pattern_nb", "hammer_pattern_nb", "morning_evening_star_nb", "three_soldiers_crows_nb",

    # Market Profile indicators
    "point_of_control", "value_area", "volume_profile",
    "point_of_control_nb", "value_area_nb", "volume_profile_nb",

    # Order Flow indicators
    "delta_volume", "cumulative_volume_delta", "aggressive_ratio", "volume_pace",
    "delta_volume_nb", "cumulative_volume_delta_nb", "aggressive_ratio_nb", "volume_pace_nb",

    # Advanced Volume indicators
    "volume_roc_adv", "klinger_volume_oscillator", "ease_of_movement", "negative_volume_index", "positive_volume_index",
    "volume_roc_adv_nb", "klinger_volume_oscillator_nb", "ease_of_movement_nb", "negative_volume_index_nb", "positive_volume_index_nb",

    # Candlestick Patterns (Extended)
    "shooting_star", "piercing_dark_cloud", "harami", "marubozu", "spinning_top", "three_inside", "tweezer",
    "shooting_star_nb", "piercing_dark_cloud_nb", "harami_nb", "marubozu_nb", "spinning_top_nb", "three_inside_nb", "tweezer_nb",

    # Oscillators (Extended)
    "stochastic_rsi", "relative_vigor_index", "psychological_line", "aroon_oscillator",
    "commodity_selection_index", "detrended_oscillator", "trend_intensity_index", "momentum_oscillator",
    "rate_of_change_ratio", "smoothed_rate_of_change", "intraday_momentum_index",
    "stochastic_rsi_nb", "relative_vigor_index_nb", "psychological_line_nb", "aroon_oscillator_nb",
    "commodity_selection_index_nb", "detrended_oscillator_nb", "trend_intensity_index_nb", "momentum_oscillator_nb",
    "rate_of_change_ratio_nb", "smoothed_rate_of_change_nb", "intraday_momentum_index_nb",

    # Bands & Channels
    "envelope", "starc_bands", "price_channel_bands", "median_price_bands",
    "typical_price_bands", "weighted_close_bands", "acceleration_bands", "high_low_bands",
    "envelope_nb", "starc_bands_nb", "price_channel_bands_nb", "median_price_bands_nb",
    "typical_price_bands_nb", "weighted_close_bands_nb", "acceleration_bands_nb", "high_low_bands_nb",

    # Composite & Specialty Indicators
    "choppiness_index", "mcginley_dynamic", "kaufman_efficiency_ratio", "vertical_horizontal_filter",
    "linear_regression_bands", "price_oscillator", "force_index", "elder_force_index",
    "chande_forecast_oscillator", "center_of_gravity", "linear_weighted_ma", "variable_ma",
    "triangular_ma", "std_dev_channels", "ease_of_movement_value",
    "relative_momentum_index", "qstick_indicator", "volatility_ratio", "market_facilitation_index",
    "choppiness_index_nb", "mcginley_dynamic_nb", "kaufman_efficiency_ratio_nb", "vertical_horizontal_filter_nb",
    "linear_regression_bands_nb", "price_oscillator_nb", "force_index_nb", "elder_force_index_nb",
    "chande_forecast_oscillator_nb", "center_of_gravity_nb", "linear_weighted_ma_nb", "variable_ma_nb",
    "triangular_ma_nb", "std_dev_channels_nb", "ease_of_movement_value_nb",
    "relative_momentum_index_nb", "qstick_indicator_nb", "volatility_ratio_nb", "market_facilitation_index_nb",
]
