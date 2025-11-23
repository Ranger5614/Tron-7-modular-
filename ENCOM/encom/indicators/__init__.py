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
]
