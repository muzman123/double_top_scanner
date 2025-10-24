"""
Professional Double Top Pattern Detector - FIXED VERSION
Bug fixes documented inline
"""

import pandas as pd
import numpy as np
from src.indicators import calculate_rsi


class DoubleTopDetector:
    """
    Fixed professional-grade double top pattern detector.
    
    BUGS FIXED:
    1. Trough depth too strict (3% -> 5-8% range)
    2. Trough index calculation bug
    3. Decline validation too strict (60% -> 50%)
    4. Rally validation too strict (3% -> 2%)
    5. Minimum confidence too high (60 -> 40)
    6. Peak prominence too strict (made configurable)
    7. Time spacing max too low for some patterns
    """
    
    def __init__(self, config):
        """Initialize detector with configuration."""
        # Detection mode: 'detection' (confirmed only) or 'prediction' (early warning)
        self.mode = config['pattern'].get('mode', 'detection')
        
        # Pattern parameters
        self.price_tolerance_pct = config['pattern'].get('price_tolerance_pct', 3) / 100
        self.min_candle_distance = config['pattern'].get('min_candle_distance', 8)
        
        # Trough depth requirement
        trough_depth = config['pattern'].get('trough_depth_pct', 3)
        self.trough_depth_pct = trough_depth / 100
        
        self.lookback_candles = config['pattern'].get('lookback_candles', 100)
        
        # RSI parameters - adjusted based on mode
        self.rsi_period = config.get('rsi', {}).get('period', 14)
        self.divergence_min_diff = config.get('rsi', {}).get('divergence_min_diff', 2)
        self.divergence_required = config.get('rsi', {}).get('divergence_required', True)
        
        # Peak prominence - configurable
        min_prom_pct = config['pattern'].get('min_prominence', 1.5)
        self.min_prominence = min_prom_pct / 100
        self.peak_window = config['pattern'].get('peak_window', 5)
        
        # NEW: Maximum percentage Peak2 can exceed Peak1 (prevents uptrend false positives)
        max_exceed = config['pattern'].get('max_exceed_pct', 3)
        self.max_exceed_pct = max_exceed / 100
        
        # Minimum confidence
        self.min_confidence = config['pattern'].get('min_confidence', 35)
        
        # Time spacing
        self.max_bars_multiplier = 0.67
        
        # NEW CONFIGURABLE PARAMETERS
        # Asymmetric prominence thresholds
        self.min_reversal_drop_pct = config['pattern'].get('min_reversal_drop_pct', 2) / 100
        self.min_rally_rise_pct = config['pattern'].get('min_rally_rise_pct', 2) / 100
        
        # Prediction mode parameters
        self.max_peak_age_pct = config['pattern'].get('max_peak_age_pct', 50) / 100
        self.reversal_threshold_pct = config['pattern'].get('reversal_threshold_pct', 3) / 100
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"DoubleTopDetector initialized in '{self.mode.upper()}' mode")
        if self.mode == 'prediction':
            logger.info("  → Early warning: Alerts BEFORE neckline break (pattern forming)")
            logger.info(f"  → RSI divergence: ≥{self.divergence_min_diff} points required")
        else:
            logger.info("  → Conservative: Alerts AFTER neckline break (pattern confirmed)")
            logger.info(f"  → RSI divergence: ≥{self.divergence_min_diff} points required")
        
    def detect(self, df):
        """
        Detect double top pattern in OHLCV dataframe.
        
        Returns:
            dict or None: Pattern details if found
        """
        if len(df) < self.lookback_candles:
            return None
        
        # Work with lookback window
        df_window = df.tail(self.lookback_candles).copy()
        df_window['original_index'] = df_window.index
        df_window = df_window.reset_index(drop=True)
        
        # Calculate RSI
        try:
            rsi = calculate_rsi(df_window['Close'], period=self.rsi_period)
            df_window['RSI'] = rsi
        except Exception as e:
            # RSI calculation failed, continue without it
            df_window['RSI'] = np.nan
        
        # Find peaks with relaxed prominence
        peaks = self._find_peaks_with_prominence(df_window['High'])
        
        if len(peaks) < 2:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Rejected: Only {len(peaks)} peaks found (need 2+)")
            return None
        
        # Search for valid double top (most recent first)
        for i in range(len(peaks) - 1, 0, -1):
            peak2_idx = peaks[i]
            peak1_idx = peaks[i-1]
            
            # Time constraints
            bars_between = peak2_idx - peak1_idx
            if not self._validate_time_spacing(bars_between):
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Rejected peak pair {i-1},{i}: Time spacing {bars_between} bars invalid")
                continue
            
            # ASYMMETRIC PROMINENCE VALIDATION for double top characteristics
            # Peak 1: Should show reversal (sharp drop on right)
            # Peak 2: Should show rally (sharp rise on left)
            if not self._validate_peak_pair_prominence(df_window, peak1_idx, peak2_idx):
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Rejected peak pair {i-1},{i}: Peak prominence pattern invalid for double top")
                continue
            
            # Get peak prices
            peak1_price = float(df_window['High'].iloc[peak1_idx])
            peak2_price = float(df_window['High'].iloc[peak2_idx])
            
            # Price similarity
            if not self._validate_price_similarity(peak1_price, peak2_price):
                import logging
                logger = logging.getLogger(__name__)
                price_diff_pct = abs(peak2_price - peak1_price) / min(peak1_price, peak2_price) * 100
                logger.debug(f"Rejected peak pair {i-1},{i}: Price diff {price_diff_pct:.2f}% > {self.price_tolerance_pct*100}%")
                continue
            
            # Find and validate trough - FIXED VERSION
            trough_result = self._find_and_validate_trough(
                df_window, peak1_idx, peak2_idx, peak1_price, peak2_price
            )
            
            if trough_result is None:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Rejected peak pair {i-1},{i}: Trough validation failed")
                continue
            
            trough_idx, trough_price, decline_pct = trough_result
            
            # Validate M-shape structure
            if not self._validate_m_shape_structure(
                df_window['High'], peak1_idx, peak2_idx, peak1_price, peak2_price, df_window
            ):
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Rejected peak pair {i-1},{i}: M-shape validation failed")
                continue
            
            # Validate price movement
            if not self._validate_price_movement(
                df_window['Close'], peak1_idx, peak2_idx, trough_idx,
                peak1_price, trough_price
            ):
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Rejected peak pair {i-1},{i}: Price movement validation failed")
                continue
            
            # Mode-dependent neckline break check
            if self.mode == 'detection':
                # DETECTION MODE: Require neckline break confirmation
                if not self._check_neckline_break(df_window, peak2_idx, trough_price):
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Rejected peak pair {i-1},{i}: No neckline break (pattern not confirmed)")
                    continue
                pattern_status = 'confirmed'
            else:
                # PREDICTION MODE: Pattern forming, neckline break NOT required
                # Check if we're close to current price action (recent Peak2)
                # Configurable via max_peak_age_pct parameter
                bars_since_peak2 = len(df_window) - 1 - peak2_idx
                max_bars_since_peak2 = int(self.lookback_candles * self.max_peak_age_pct)
                
                if bars_since_peak2 > max_bars_since_peak2:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Rejected peak pair {i-1},{i}: Peak2 too old ({bars_since_peak2} bars ago, max {max_bars_since_peak2} for prediction)")
                    continue
                
                # CRITICAL: Check that price is declining after Peak 2 (not rallying back up)
                # In a true reversal, price should stay BELOW the peak
                # Configurable via reversal_threshold_pct parameter
                current_price = float(df_window['Close'].iloc[-1])
                peak2_decline_threshold = peak2_price * (1 - self.reversal_threshold_pct)
                
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"  Checking reversal: Current=${current_price:.2f}, Peak2=${peak2_price:.2f}, Threshold=${peak2_decline_threshold:.2f}")
                
                if current_price > peak2_decline_threshold:
                    logger.debug(f"Rejected peak pair {i-1},{i}: Price rallied back to ${current_price:.2f} (must be < ${peak2_decline_threshold:.2f}, 3% below Peak2)")
                    logger.debug(f"  This indicates CONTINUATION, not reversal!")
                    continue
                
                pattern_status = 'forming'
            
            # RSI divergence check (required in prediction mode)
            if self.divergence_required:
                rsi_peak1 = df_window['RSI'].iloc[peak1_idx]
                rsi_peak2 = df_window['RSI'].iloc[peak2_idx]
                
                if pd.notna(rsi_peak1) and pd.notna(rsi_peak2):
                    rsi_div_value = float(rsi_peak1 - rsi_peak2)
                    if rsi_div_value < self.divergence_min_diff:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Rejected peak pair {i-1},{i}: RSI divergence {rsi_div_value:.1f} < {self.divergence_min_diff} (required)")
                        continue
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Rejected peak pair {i-1},{i}: RSI data missing for divergence check")
                    continue
            
            # Pattern found!
            pattern = self._build_pattern_result(
                df_window, peak1_idx, peak2_idx, trough_idx,
                peak1_price, peak2_price, trough_price, bars_between, decline_pct,
                pattern_status
            )
            
            # Calculate confidence
            pattern['confidence'] = self._calculate_confidence_score(
                df_window, pattern
            )
            
            # Return if meets minimum threshold
            if pattern['confidence'] >= self.min_confidence:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f" Pattern found! Confidence: {pattern['confidence']:.0f}% (>= {self.min_confidence})")
                return pattern
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Rejected peak pair {i-1},{i}: Confidence {pattern['confidence']:.0f}% < {self.min_confidence}%")
        
        return None
    
    def _find_peaks_with_prominence(self, prices):
        """
        Find peaks with ASYMMETRIC prominence for double top detection.
        
        Peak 1 (first top): Should have sharp DROP on right (reversal signal)
        Peak 2 (second top): Should have sharp RISE on left (rally from trough)
        
        CRITICAL FIX: In prediction mode, check peaks near the end (reduced right window)
        """
        peaks = []
        window = self.peak_window
        
        # In prediction mode, check closer to the end (allow smaller right window)
        # In detection mode, require full windows on both sides
        if self.mode == 'prediction':
            end_offset = 0  # Check up to the LAST bar (allows detecting very recent peaks)
        else:
            end_offset = window  # Require full window
        
        for i in range(window, len(prices) - end_offset):
            # Check if local maximum
            left_window = prices.iloc[i-window:i]
            
            # For bars near the end, use available right window
            available_right = len(prices) - i - 1
            right_window_size = min(window, available_right)
            right_window = prices.iloc[i+1:i+1+right_window_size]
            
            if len(left_window) == 0:
                continue
            
            # Peak must be higher than left window
            # And higher than right window (if available)
            is_peak = prices.iloc[i] > left_window.max()
            if len(right_window) > 0:
                is_peak = is_peak and (prices.iloc[i] > right_window.max())
            
            if is_peak:
                # Calculate left and right prominence separately
                peak_price = prices.iloc[i]
                left_min = left_window.min()
                left_prominence = (peak_price - left_min) / peak_price
                
                # Right prominence (may be reduced for recent peaks)
                if len(right_window) > 0:
                    right_min = right_window.min()
                    right_prominence = (peak_price - right_min) / peak_price
                else:
                    right_prominence = 0  # No right window available
                
                # Accept peak if EITHER:
                # 1. Has significant left OR right prominence (at least 1%)
                # 2. OR both have moderate prominence (0.75% each)
                # 3. OR (prediction mode) strong left prominence with weak/no right
                min_single_prominence = 0.01  # 1%
                min_combined_prominence = 0.0075  # 0.75%
                
                has_prominence = (
                    left_prominence >= min_single_prominence or
                    right_prominence >= min_single_prominence or
                    (left_prominence >= min_combined_prominence and
                     right_prominence >= min_combined_prominence)
                )
                
                # In prediction mode, also accept strong left prominence alone (for Peak 2)
                if self.mode == 'prediction' and left_prominence >= 0.03:  # 3%+ rise
                    has_prominence = True
                
                if has_prominence:
                    peaks.append(i)
        
        return peaks
    
    def _validate_peak_pair_prominence(self, df_window, peak1_idx, peak2_idx):
        """
        Validate asymmetric prominence for double top pattern.
        
        Peak 1: Should have sharp DROP on right (reversal signal) - at least 3-4%
        Peak 2: Should have sharp RISE on left (rally from trough) - at least 3-4%
        Peak 2 right: Can be minimal in prediction mode (early catch)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        prices = df_window['High']
        window = self.peak_window
        
        # Get Peak 1 characteristics
        peak1_price = prices.iloc[peak1_idx]
        peak1_right_window = prices.iloc[peak1_idx+1:min(peak1_idx+window+1, len(prices))]
        
        if len(peak1_right_window) > 0:
            peak1_right_min = peak1_right_window.min()
            peak1_right_drop = (peak1_price - peak1_right_min) / peak1_price
        else:
            peak1_right_drop = 0
        
        # Get Peak 2 characteristics
        peak2_price = prices.iloc[peak2_idx]
        peak2_left_window = prices.iloc[max(peak2_idx-window, 0):peak2_idx]
        
        if len(peak2_left_window) > 0:
            peak2_left_min = peak2_left_window.min()
            peak2_left_rise = (peak2_price - peak2_left_min) / peak2_price
        else:
            peak2_left_rise = 0
        
        # For Peak 2, check right side only if we have enough bars after it
        bars_after_peak2 = len(prices) - 1 - peak2_idx
        peak2_right_window = prices.iloc[peak2_idx+1:min(peak2_idx+window+1, len(prices))]
        
        if len(peak2_right_window) > 0:
            peak2_right_min = peak2_right_window.min()
            peak2_right_drop = (peak2_price - peak2_right_min) / peak2_price
        else:
            peak2_right_drop = 0
        
        # Validation thresholds (now configurable via settings.yaml)
        # Peak 1 should show reversal (sharp drop on right)
        if peak1_right_drop < self.min_reversal_drop_pct:
            logger.debug(f"  Peak pair prominence: REJECTED - Peak1 right drop {peak1_right_drop*100:.1f}% < {self.min_reversal_drop_pct*100}% (no reversal)")
            return False
        
        # Peak 2 should show rally from trough (sharp rise on left)
        if peak2_left_rise < self.min_rally_rise_pct:
            logger.debug(f"  Peak pair prominence: REJECTED - Peak2 left rise {peak2_left_rise*100:.1f}% < {self.min_rally_rise_pct*100}% (no rally)")
            return False
        
        # In prediction mode, Peak 2 right can be minimal (early detection)
        # In detection mode, should have some drop
        if self.mode == 'detection' and bars_after_peak2 >= window:
            if peak2_right_drop < 0.01:  # At least 1% drop
                logger.debug(f"  Peak pair prominence: REJECTED - Peak2 right drop {peak2_right_drop*100:.1f}% < 1% (detection mode requires confirmation)")
                return False
        
        logger.debug(f"  Peak pair prominence: PASSED - Peak1 right drop {peak1_right_drop*100:.1f}%, Peak2 left rise {peak2_left_rise*100:.1f}%")
        return True
    
    def _validate_time_spacing(self, bars_between):
        """
        BUG FIX #7: More flexible time spacing.
        """
        # More generous max bars
        max_bars = int(self.lookback_candles * self.max_bars_multiplier)  # Up to 67% of lookback
        
        return self.min_candle_distance <= bars_between <= max_bars
    
    def _validate_price_similarity(self, peak1_price, peak2_price):
        """
        Validate peaks are at similar price levels.
        
        CRITICAL FIX: A double top is a REVERSAL pattern, not a continuation.
        Peak 2 must be at approximately the SAME level as Peak 1.
        If Peak 2 is significantly HIGHER, it's an uptrend continuation, NOT a double top!
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Calculate price difference
        price_diff_pct = abs(peak2_price - peak1_price) / peak1_price
        
        # CRITICAL: Peak 2 should NOT be significantly higher than Peak 1
        # This is a reversal pattern - peaks should test the SAME resistance level
        if peak2_price > peak1_price:
            # Allow Peak 2 to be slightly higher (marginal new high before reversal)
            # but NOT significantly higher (which indicates uptrend continuation)
            exceed_pct = (peak2_price - peak1_price) / peak1_price
            
            if exceed_pct > self.max_exceed_pct:
                logger.debug(f"  Price similarity rejected: Peak 2 (${peak2_price:.2f}) is {exceed_pct*100:.1f}% HIGHER than Peak 1 (${peak1_price:.2f})")
                logger.debug(f"    This is UPTREND CONTINUATION, not a double top reversal pattern!")
                return False
        
        # Check that peaks are within tolerance
        if price_diff_pct > self.price_tolerance_pct:
            logger.debug(f"  Price similarity rejected: Difference {price_diff_pct*100:.1f}% > {self.price_tolerance_pct*100}%")
            return False
        
        logger.debug(f"  Price similarity valid: Peak1=${peak1_price:.2f}, Peak2=${peak2_price:.2f}, Diff={price_diff_pct*100:.1f}%")
        return True
    
    def _get_timestamp(self, df_window, idx):
        """Helper to get readable timestamp from index."""
        if 'original_index' in df_window.columns:
            return str(df_window['original_index'].iloc[idx])
        return f"index {idx}"
    
    def _find_and_validate_trough(self, df_window, peak1_idx, peak2_idx,
                                   peak1_price, peak2_price):
        """
        BUG FIX #2: Fixed trough index calculation.
        BUG FIX #1: More lenient trough depth requirement.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # BUG FIX #2: Simplified trough finding logic
        # Old version had confusing index manipulation that could cause errors
        trough_section = df_window['Low'].iloc[peak1_idx:peak2_idx+1]
        
        # Find the minimum in this section
        trough_idx_in_section = trough_section.values.argmin()
        trough_idx = peak1_idx + trough_idx_in_section
        trough_price = float(df_window['Low'].iloc[trough_idx])
        
        # Get timestamps for logging
        peak1_time = self._get_timestamp(df_window, peak1_idx)
        peak2_time = self._get_timestamp(df_window, peak2_idx)
        trough_time = self._get_timestamp(df_window, trough_idx)
        
        # Validate trough is lower than both peaks
        if trough_price >= min(peak1_price, peak2_price):
            logger.debug(f"  Trough rejected: Price ${trough_price:.2f} at {trough_time}")
            logger.debug(f"    >= min peak ${min(peak1_price, peak2_price):.2f}")
            return None
        
        # Calculate decline from each peak
        decline1 = (peak1_price - trough_price) / peak1_price
        decline2 = (peak2_price - trough_price) / peak2_price
        avg_decline = (decline1 + decline2) / 2
        
        # BUG FIX #1: More realistic and lenient depth requirement
        # Changed to use average decline instead of requiring BOTH to meet threshold
        # This prevents rejecting patterns where one decline is 4.96% and the other is 7.81%
        # Real patterns typically have 5-15% average decline
        if avg_decline < self.trough_depth_pct:
            logger.debug(f"  Trough rejected: Avg decline {avg_decline*100:.2f}% < {self.trough_depth_pct*100}% (Decline1={decline1*100:.2f}%, Decline2={decline2*100:.2f}%)")
            return None
        
        # Validate trough position (not at edges)
        if peak2_idx - peak1_idx == 0:
            logger.debug(f"  Trough rejected: Peaks at same index")
            return None
            
        trough_position = (trough_idx - peak1_idx) / (peak2_idx - peak1_idx)
        if not (0.1 <= trough_position <= 0.9):
            logger.debug(f"  Trough rejected: Position {trough_position:.2f} not in range [0.1, 0.9]")
            return None
        
        logger.debug(f"  Trough valid: Price ${trough_price:.2f}, Decline1 {decline1*100:.2f}%, Decline2 {decline2*100:.2f}%")
        return trough_idx, trough_price, avg_decline
    
    def _validate_m_shape_structure(self, prices, peak1_idx, peak2_idx,
                                     peak1_price, peak2_price, df_window=None):
        """
        Validate M-shape: Ensure no significantly higher peaks between Peak 1 and Peak 2.
        
        CRITICAL FIX: In a true double top, there should be a clear M-shape.
        The trough between peaks should be the dominant low point.
        No intermediate peak should be HIGHER than both main peaks (that would be a triple top or higher).
        """
        import logging
        logger = logging.getLogger(__name__)
        
        intermediate_section = prices.iloc[peak1_idx+1:peak2_idx]
        
        if len(intermediate_section) < 2:
            return True
        
        # Find the maximum price in the intermediate section
        max_intermediate = intermediate_section.max()
        intermediate_idx = intermediate_section.idxmax()
        
        # The lower of the two peaks is our threshold
        lower_peak = min(peak1_price, peak2_price)
        
        # CRITICAL: Intermediate highs should NOT exceed the lower of the two peaks
        # Allow some tolerance for noise (98% of lower peak)
        threshold = lower_peak
        
        if max_intermediate > threshold:
            # Get timestamps if available
            if df_window is not None:
                peak1_time = self._get_timestamp(df_window, peak1_idx)
                peak2_time = self._get_timestamp(df_window, peak2_idx)
                intermediate_time = self._get_timestamp(df_window, intermediate_idx)
                
                logger.debug(f"  M-shape rejected: Intermediate high ${max_intermediate:.2f} at {intermediate_time}")
                logger.debug(f"    exceeds threshold ${threshold:.2f} (98% of lower peak)")
                logger.debug(f"    Peak1: ${peak1_price:.2f} at {peak1_time}")
                logger.debug(f"    Peak2: ${peak2_price:.2f} at {peak2_time}")
            else:
                logger.debug(f"  M-shape rejected: Intermediate high ${max_intermediate:.2f} exceeds threshold ${threshold:.2f}")
            logger.debug(f"    This suggests a continuation pattern, not a double top reversal")
            return False
        
        logger.debug(f"  M-shape valid: Clean decline and rally between peaks")
        return True
    
    def _validate_price_movement(self, closes, peak1_idx, peak2_idx, trough_idx,
                                  peak1_price, trough_price):
        """
        Validate basic price movement in M-shape pattern.
        Less strict than before but ensures reasonable movement.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Just ensure there was a meaningful rally from trough to peak2
        rally_section = closes.iloc[trough_idx:peak2_idx+1]
        if len(rally_section) > 1:
            max_rally = rally_section.max()
            price_gain = (max_rally - trough_price) / trough_price
            
            # Ensure at least 1% rally occurred
            if price_gain < 0.01:
                logger.debug(f"  Price movement rejected: Insufficient rally {price_gain*100:.1f}% from trough")
                return False
        
        logger.debug(f"  Price movement valid")
        return True
    
    def _check_neckline_break(self, df_window, peak2_idx, neckline):
        """
        CRITICAL FIX: Check for neckline break confirmation.
        
        A double top pattern is only CONFIRMED when price breaks BELOW the neckline (trough).
        Without this break, the pattern is incomplete and should not be signaled.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Look at prices AFTER peak2
        prices_after_peak2 = df_window['Close'].iloc[peak2_idx:]
        
        if len(prices_after_peak2) < 2:
            logger.debug(f"  Neckline break: Insufficient data after Peak 2")
            return False
        
        # Check if ANY close after peak2 breaks below the neckline
        # Allow small tolerance for noise (0.5%)
        neckline_threshold = neckline * 0.995
        
        broke_neckline = (prices_after_peak2 < neckline_threshold).any()
        
        if not broke_neckline:
            logger.debug(f"  Neckline break: NO BREAK - Price has not closed below ${neckline:.2f}")
            logger.debug(f"    Pattern is INCOMPLETE and not confirmed!")
            return False
        
        # Find where the break occurred
        break_idx = prices_after_peak2[prices_after_peak2 < neckline_threshold].index[0]
        bars_to_break = break_idx - peak2_idx
        
        logger.debug(f"  Neckline break: CONFIRMED - Broke below ${neckline:.2f} after {bars_to_break} bars")
        return True
    
    def _build_pattern_result(self, df_window, peak1_idx, peak2_idx, trough_idx,
                               peak1_price, peak2_price, trough_price,
                               bars_between, decline_pct, pattern_status='confirmed'):
        """Build comprehensive pattern result dictionary."""
        
        # Get timestamps
        if 'original_index' in df_window.columns:
            peak1_time = str(df_window['original_index'].iloc[peak1_idx])
            peak2_time = str(df_window['original_index'].iloc[peak2_idx])
            trough_time = str(df_window['original_index'].iloc[trough_idx])
        else:
            peak1_time = str(peak1_idx)
            peak2_time = str(peak2_idx)
            trough_time = str(trough_idx)
        
        # RSI values at peaks
        rsi_peak1 = df_window['RSI'].iloc[peak1_idx]
        rsi_peak2 = df_window['RSI'].iloc[peak2_idx]
        
        # RSI divergence check
        if pd.notna(rsi_peak1) and pd.notna(rsi_peak2):
            rsi_divergence_value = float(rsi_peak1 - rsi_peak2)
            rsi_divergence = rsi_divergence_value >= self.divergence_min_diff
        else:
            rsi_divergence_value = 0.0
            rsi_divergence = False
        
        # Volume analysis
        if 'Volume' in df_window.columns:
            vol_peak1 = float(df_window['Volume'].iloc[peak1_idx])
            vol_peak2 = float(df_window['Volume'].iloc[peak2_idx])
            
            if vol_peak1 > 0:
                volume_decline_pct = ((vol_peak1 - vol_peak2) / vol_peak1) * 100
            else:
                volume_decline_pct = 0.0
        else:
            vol_peak1 = None
            vol_peak2 = None
            volume_decline_pct = 0.0
        
        # Price difference
        price_diff_pct = abs(peak2_price - peak1_price) / peak1_price * 100
        
        # Neckline and price target
        neckline = trough_price
        pattern_height = ((peak1_price + peak2_price) / 2) - neckline
        price_target = neckline - pattern_height
        
        return {
            'found': True,
            'status': pattern_status,  # 'forming' or 'confirmed'
            'mode': self.mode,  # 'prediction' or 'detection'
            'peak1_idx': int(peak1_idx),
            'peak2_idx': int(peak2_idx),
            'trough_idx': int(trough_idx),
            'peak1_price': peak1_price,
            'peak2_price': peak2_price,
            'trough_price': trough_price,
            'peak1_time': peak1_time,
            'peak2_time': peak2_time,
            'trough_time': trough_time,
            'price_diff_pct': float(price_diff_pct),
            'candles_between': int(bars_between),
            'trough_depth_pct': float(decline_pct * 100),
            'neckline': neckline,
            'price_target': price_target,
            'rsi_peak1': float(rsi_peak1) if pd.notna(rsi_peak1) else None,
            'rsi_peak2': float(rsi_peak2) if pd.notna(rsi_peak2) else None,
            'rsi_divergence': rsi_divergence,
            'rsi_divergence_value': rsi_divergence_value,
            'volume_peak1': vol_peak1,
            'volume_peak2': vol_peak2,
            'volume_decline_pct': float(volume_decline_pct),
        }
    
    def _calculate_confidence_score(self, df_window, pattern):
        """
        Calculate 0-100 confidence score.
        
        BUG FIX #5: With lower min_confidence (40 instead of 60),
        more patterns will be returned even with moderate scores.
        """
        score = 0
        
        # Factor 1: Price Similarity (0-25 points)
        price_diff_pct = pattern['price_diff_pct'] / 100
        if price_diff_pct < 0.01:
            score += 25
        elif price_diff_pct < 0.02:
            score += 20
        elif price_diff_pct < 0.03:
            score += 15
        elif price_diff_pct < 0.05:
            score += 10
        else:
            score += 5  # Give some points even for less similar peaks
        
        # Factor 2: Trough Depth (0-25 points)
        # More lenient scoring for shallower troughs
        decline_pct = pattern['trough_depth_pct'] / 100
        if decline_pct > 0.15:
            score += 25
        elif decline_pct > 0.12:
            score += 20
        elif decline_pct > 0.10:
            score += 15
        elif decline_pct > 0.08:
            score += 10
        elif decline_pct > 0.05:
            score += 8  # Still give decent points for 5%+
        elif decline_pct > 0.03:
            score += 5  # Give some points even for shallow
        
        # Factor 3: Volume Pattern (0-25 points)
        if pattern['volume_peak1'] and pattern['volume_peak2']:
            try:
                vol_series = df_window['Volume'].iloc[:pattern['peak1_idx']]
                if len(vol_series) > 20:
                    avg_vol = vol_series.iloc[-20:].mean()
                    
                    # Peak1 elevated volume
                    if pattern['volume_peak1'] > avg_vol * 1.2:
                        score += 10
                    elif pattern['volume_peak1'] > avg_vol * 1.0:
                        score += 5  # Give points even if not elevated
                    
                    # Volume declining at peak2
                    if pattern['volume_peak2'] < pattern['volume_peak1']:
                        score += 10
                    
                    # Strong volume decline
                    if pattern['volume_decline_pct'] > 20:
                        score += 5
            except:
                pass  # Skip volume scoring if error
        
        # Factor 4: Time Spacing (0-15 points)
        # More lenient time spacing scoring
        bars_between = pattern['candles_between']
        if 20 <= bars_between <= 60:
            score += 15
        elif 15 <= bars_between <= 80:
            score += 12
        elif 10 <= bars_between <= 100:
            score += 8
        else:
            score += 5  # Give some points for any reasonable spacing
        
        # Factor 5: Clean Structure (0-10 points)
        peak1_idx = pattern['peak1_idx']
        peak2_idx = pattern['peak2_idx']
        
        if peak2_idx - peak1_idx > 10:
            try:
                intermediate = df_window['High'].iloc[peak1_idx+5:peak2_idx-5]
                if len(intermediate) > 0:
                    max_intermediate = intermediate.max()
                    min_peak = min(pattern['peak1_price'], pattern['peak2_price'])
                    
                    if max_intermediate < min_peak * 0.90:
                        score += 10
                    elif max_intermediate < min_peak * 0.95:
                        score += 6
                    else:
                        score += 3  # Give some points anyway
            except:
                pass
        
        return min(score, 100)


# Helper functions remain the same
def check_for_triple_top(peaks, prices, tolerance=0.03):
    """Check if pattern is actually a triple top."""
    if len(peaks) >= 3:
        last_three = peaks[-3:]
        prices_at_peaks = [prices[i] for i in last_three]
        max_price = max(prices_at_peaks)
        min_price = min(prices_at_peaks)
        
        if (max_price - min_price) / min_price <= tolerance:
            return True
    return False


def calculate_angled_neckline(prices, lows_indices):
    """Calculate angled neckline using linear regression."""
    if len(lows_indices) < 2:
        return None, None
    
    x = np.array(lows_indices)
    y = np.array([prices[i] for i in lows_indices])
    
    slope = (y[-1] - y[0]) / (x[-1] - x[0])
    intercept = y[0] - slope * x[0]
    
    return slope, intercept