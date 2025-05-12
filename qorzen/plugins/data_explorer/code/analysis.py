# qorzen/plugins/data_explorer/analysis.py
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats


class DataStatsCalculator:
    """Calculator for dataset statistics."""

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initialize statistics calculator.

        Args:
            df: DataFrame to analyze
        """
        self.df = df

    def calculate_summary(self) -> Dict[str, Any]:
        """
        Calculate summary statistics.

        Returns:
            Dictionary of summary statistics
        """
        # Get numeric columns
        numeric_df = self.df.select_dtypes(include=['number'])

        # Basic stats
        result = {
            "rows": len(self.df),
            "columns": len(self.df.columns),
            "numeric_columns": len(numeric_df.columns),
            "categorical_columns": len(self.df.select_dtypes(include=['object', 'category']).columns),
            "missing_values": self.df.isna().sum().sum(),
            "memory_usage_mb": self.df.memory_usage().sum() / 1024 ** 2
        }

        if not numeric_df.empty:
            # Add aggregate statistics for numeric columns
            result.update({
                "mean_values": {col: round(numeric_df[col].mean(), 4) for col in numeric_df.columns},
                "median_values": {col: round(numeric_df[col].median(), 4) for col in numeric_df.columns},
                "std_values": {col: round(numeric_df[col].std(), 4) for col in numeric_df.columns},
                "min_values": {col: round(numeric_df[col].min(), 4) for col in numeric_df.columns},
                "max_values": {col: round(numeric_df[col].max(), 4) for col in numeric_df.columns}
            })

            # Calculate skewness and kurtosis
            result.update({
                "skewness": {col: round(numeric_df[col].skew(), 4) for col in numeric_df.columns},
                "kurtosis": {col: round(numeric_df[col].kurtosis(), 4) for col in numeric_df.columns}
            })

        # Count null values by column
        result["null_counts"] = {col: int(self.df[col].isna().sum()) for col in self.df.columns}

        return result


class CorrelationAnalyzer:
    """Analyzer for correlations between columns."""

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initialize correlation analyzer.

        Args:
            df: DataFrame to analyze
        """
        self.df = df

    def find_notable_correlations(self) -> List[Dict[str, Any]]:
        """
        Find notable correlations in the dataset.

        Returns:
            List of notable correlations
        """
        # Get numeric columns
        numeric_df = self.df.select_dtypes(include=['number'])

        if len(numeric_df.columns) < 2:
            return []

        # Calculate correlation matrix
        corr_matrix = numeric_df.corr()

        # Get upper triangle of correlation matrix
        corr_values = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Upper triangle only
                    corr_val = corr_matrix.loc[col1, col2]
                    if not np.isnan(corr_val):
                        corr_values.append({
                            "var1": col1,
                            "var2": col2,
                            "value": corr_val,
                            "abs_value": abs(corr_val)
                        })

        # Sort by absolute correlation value
        corr_values.sort(key=lambda x: x["abs_value"], reverse=True)

        # Add strength classification
        for item in corr_values:
            abs_val = item["abs_value"]
            if abs_val > 0.7:
                if item["value"] > 0:
                    item["strength"] = "Strong Positive"
                else:
                    item["strength"] = "Strong Negative"
            elif abs_val > 0.5:
                if item["value"] > 0:
                    item["strength"] = "Moderate Positive"
                else:
                    item["strength"] = "Moderate Negative"
            elif abs_val > 0.3:
                if item["value"] > 0:
                    item["strength"] = "Weak Positive"
                else:
                    item["strength"] = "Weak Negative"
            else:
                item["strength"] = "Negligible"

        # Return top correlations
        return corr_values[:20]  # Limit to top 20


class TrendDetector:
    """Detector for trends in dataset."""

    def __init__(self, df: pd.DataFrame) -> None:
        """
        Initialize trend detector.

        Args:
            df: DataFrame to analyze
        """
        self.df = df

    def detect_trends(self) -> List[str]:
        """
        Detect trends in the dataset.

        Returns:
            List of trend descriptions
        """
        # Get numeric columns
        numeric_df = self.df.select_dtypes(include=['number'])

        if len(numeric_df.columns) < 2:
            return ["Not enough numeric columns for trend analysis"]

        trends = []

        # Check for highly skewed columns
        for col in numeric_df.columns:
            skew = numeric_df[col].skew()
            if abs(skew) > 2:
                direction = "positively" if skew > 0 else "negatively"
                trends.append(f"Column '{col}' is highly {direction} skewed ({skew:.2f})")

        # Check for potential time-based columns
        time_cols = [col for col in numeric_df.columns if 'time' in col.lower()
                     or 'date' in col.lower() or 'year' in col.lower()
                     or 'month' in col.lower() or 'day' in col.lower()
                     or 'id' in col.lower() or 'index' in col.lower()]

        # If we have potential time columns, check for trends over time
        for time_col in time_cols:
            # Try other numeric columns against this time column
            for col in [c for c in numeric_df.columns if c != time_col]:
                # Sort by time column
                sorted_data = numeric_df[[time_col, col]].sort_values(by=time_col).dropna()

                if len(sorted_data) >= 10:  # Need enough data points
                    # Check for monotonic trend
                    is_increasing = sorted_data[col].is_monotonic_increasing
                    is_decreasing = sorted_data[col].is_monotonic_decreasing

                    if is_increasing:
                        trends.append(f"'{col}' consistently increases as '{time_col}' increases")
                    elif is_decreasing:
                        trends.append(f"'{col}' consistently decreases as '{time_col}' increases")

                    # Check for correlation with time
                    corr = sorted_data[[time_col, col]].corr().iloc[0, 1]
                    if abs(corr) > 0.7:
                        direction = "positive" if corr > 0 else "negative"
                        trends.append(f"'{col}' shows strong {direction} correlation ({corr:.2f}) with '{time_col}'")

                    # Try to fit regression and check if significant
                    try:
                        x = sorted_data[time_col].values
                        y = sorted_data[col].values
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

                        # If regression is significant
                        if p_value < 0.05 and abs(r_value) > 0.5:
                            direction = "increases" if slope > 0 else "decreases"
                            trends.append(
                                f"'{col}' {direction} by {abs(slope):.4f} units per unit of '{time_col}' "
                                f"(p={p_value:.4f}, R²={r_value ** 2:.2f})"
                            )
                    except Exception:
                        # Skip if regression fails
                        pass

        # Check for outliers
        for col in numeric_df.columns:
            data = numeric_df[col].dropna()
            if len(data) >= 10:
                q1 = data.quantile(0.25)
                q3 = data.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = data[(data < lower_bound) | (data > upper_bound)]

                if len(outliers) > 0:
                    pct = (len(outliers) / len(data)) * 100
                    if pct > 5:
                        trends.append(f"'{col}' contains {len(outliers)} outliers ({pct:.1f}% of data)")

        # Find correlated groups
        corr_matrix = numeric_df.corr()
        high_corr_pairs = []

        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Upper triangle only
                    corr_val = corr_matrix.loc[col1, col2]
                    if abs(corr_val) > 0.7:  # High correlation threshold
                        high_corr_pairs.append((col1, col2, corr_val))

        # If we have multiple highly correlated pairs
        if len(high_corr_pairs) >= 3:
            trends.append(f"Found {len(high_corr_pairs)} highly correlated variable pairs")

        # Group variables that might be related
        if len(high_corr_pairs) > 0:
            trends.append("Variables that may be related:")
            for col1, col2, corr in high_corr_pairs[:5]:  # Limit to top 5
                direction = "positively" if corr > 0 else "negatively"
                trends.append(f"  - '{col1}' and '{col2}' are {direction} correlated ({corr:.2f})")

        return trends