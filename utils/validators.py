import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Comprehensive DataFrame validation and quality assessment"""
    try:
        if df is None or df.empty:
            return {
                'is_valid': False,
                'errors': ['DataFrame is empty or None'],
                'warnings': [],
                'info': {},
                'suggestions': ['Please upload a valid data file']
            }
        
        errors = []
        warnings = []
        info = {}
        suggestions = []
        
        # Basic info
        info['shape'] = df.shape
        info['columns'] = list(df.columns)
        info['dtypes'] = df.dtypes.to_dict()
        info['memory_usage'] = df.memory_usage(deep=True).sum()
        
        # Check for duplicate columns
        if len(df.columns) != len(set(df.columns)):
            duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
            errors.append(f"Duplicate column names found: {duplicates}")
            suggestions.append("Rename duplicate columns to unique names")
        
        # Check for completely empty columns
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            warnings.append(f"Completely empty columns: {empty_cols}")
            suggestions.append("Consider removing empty columns")
        
        # Check data quality
        missing_data = df.isnull().sum()
        high_missing_cols = missing_data[missing_data > len(df) * 0.5].index.tolist()
        if high_missing_cols:
            warnings.append(f"Columns with >50% missing data: {high_missing_cols}")
            suggestions.append("Review columns with high missing data rates")
        
        # Check for potential data type issues
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if numeric data is stored as string
                try:
                    pd.to_numeric(df[col].dropna(), errors='raise')
                    suggestions.append(f"Column '{col}' appears to contain numeric data but is stored as text")
                except:
                    pass
                
                # Check for date-like strings
                if df[col].dropna().astype(str).str.match(r'\d{4}-\d{2}-\d{2}').any():
                    suggestions.append(f"Column '{col}' appears to contain dates")
        
        info['missing_data'] = missing_data.to_dict()
        info['data_quality_score'] = calculate_data_quality_score(df)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'info': info,
            'suggestions': suggestions
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'errors': [f"Validation error: {str(e)}"],
            'warnings': [],
            'info': {},
            'suggestions': ['Please check your data format']
        }

def calculate_data_quality_score(df: pd.DataFrame) -> float:
    """Calculate a data quality score (0-100)"""
    try:
        if df.empty:
            return 0.0
        
        score = 100.0
        
        # Penalize missing data
        missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        score -= missing_ratio * 30
        
        # Penalize duplicate rows
        duplicate_ratio = df.duplicated().sum() / len(df)
        score -= duplicate_ratio * 20
        
        # Penalize columns with single unique value
        single_value_cols = sum(1 for col in df.columns if df[col].nunique() <= 1)
        single_value_ratio = single_value_cols / len(df.columns)
        score -= single_value_ratio * 15
        
        return max(0.0, min(100.0, score))
        
    except Exception:
        return 50.0  # Default score if calculation fails

def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators
    clean_phone = re.sub(r'[\s\-$$$$\.]', '', phone.strip())
    
    # Check for valid phone patterns
    patterns = [
        r'^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$',  # US format
        r'^\+?[1-9]\d{1,14}$',  # International format
    ]
    
    return any(re.match(pattern, clean_phone) for pattern in patterns)

def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    return bool(re.match(pattern, url.strip()))

def validate_date(date_str: str, formats: List[str] = None) -> bool:
    """Validate date string against common formats"""
    if not date_str or not isinstance(date_str, str):
        return False
    
    if formats is None:
        formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
            '%d-%m-%Y', '%Y/%m/%d'
        ]
    
    for fmt in formats:
        try:
            datetime.strptime(date_str.strip(), fmt)
            return True
        except ValueError:
            continue
    
    return False

def clean_data(df: pd.DataFrame, strategy: str = 'basic') -> pd.DataFrame:
    """Clean DataFrame based on strategy"""
    try:
        df_clean = df.copy()
        
        if strategy == 'basic':
            # Remove completely empty rows and columns
            df_clean = df_clean.dropna(how='all')
            df_clean = df_clean.dropna(axis=1, how='all')
            
        elif strategy == 'aggressive':
            # Remove rows with any missing values
            df_clean = df_clean.dropna()
            
        elif strategy == 'smart':
            # Remove columns with >80% missing data
            missing_threshold = 0.8
            missing_ratio = df_clean.isnull().sum() / len(df_clean)
            cols_to_keep = missing_ratio[missing_ratio <= missing_threshold].index
            df_clean = df_clean[cols_to_keep]
            
            # Remove rows with >50% missing data
            row_missing_ratio = df_clean.isnull().sum(axis=1) / len(df_clean.columns)
            df_clean = df_clean[row_missing_ratio <= 0.5]
        
        return df_clean
        
    except Exception as e:
        st.error(f"Error cleaning data: {str(e)}")
        return df

def suggest_data_types(df: pd.DataFrame) -> Dict[str, str]:
    """Suggest appropriate data types for DataFrame columns"""
    suggestions = {}
    
    try:
        for col in df.columns:
            current_type = str(df[col].dtype)
            sample_data = df[col].dropna()
            
            if len(sample_data) == 0:
                suggestions[col] = current_type
                continue
            
            # Check for numeric data
            if current_type == 'object':
                try:
                    pd.to_numeric(sample_data, errors='raise')
                    # Check if integers
                    if sample_data.astype(str).str.match(r'^-?\d+$').all():
                        suggestions[col] = 'int64'
                    else:
                        suggestions[col] = 'float64'
                    continue
                except:
                    pass
                
                # Check for datetime
                if sample_data.astype(str).str.match(r'\d{4}-\d{2}-\d{2}').any():
                    suggestions[col] = 'datetime64[ns]'
                    continue
                
                # Check for boolean
                unique_vals = set(sample_data.astype(str).str.lower())
                if unique_vals.issubset({'true', 'false', '1', '0', 'yes', 'no'}):
                    suggestions[col] = 'bool'
                    continue
            
            suggestions[col] = current_type
            
    except Exception as e:
        st.error(f"Error suggesting data types: {str(e)}")
    
    return suggestions

def profile_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate comprehensive data profile"""
    try:
        profile = {
            'overview': {
                'rows': len(df),
                'columns': len(df.columns),
                'missing_cells': df.isnull().sum().sum(),
                'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                'duplicate_rows': df.duplicated().sum(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            },
            'columns': {},
            'correlations': {},
            'recommendations': []
        }
        
        # Column-level analysis
        for col in df.columns:
            col_data = df[col]
            col_profile = {
                'dtype': str(col_data.dtype),
                'missing_count': col_data.isnull().sum(),
                'missing_percentage': (col_data.isnull().sum() / len(col_data)) * 100,
                'unique_count': col_data.nunique(),
                'unique_percentage': (col_data.nunique() / len(col_data)) * 100 if len(col_data) > 0 else 0
            }
            
            # Numeric columns
            if pd.api.types.is_numeric_dtype(col_data):
                col_profile.update({
                    'mean': col_data.mean(),
                    'median': col_data.median(),
                    'std': col_data.std(),
                    'min': col_data.min(),
                    'max': col_data.max(),
                    'zeros_count': (col_data == 0).sum(),
                    'outliers_count': len(detect_outliers(col_data))
                })
            
            # Text columns
            elif col_data.dtype == 'object':
                col_profile.update({
                    'avg_length': col_data.astype(str).str.len().mean(),
                    'max_length': col_data.astype(str).str.len().max(),
                    'min_length': col_data.astype(str).str.len().min()
                })
            
            profile['columns'][col] = col_profile
        
        # Generate recommendations
        profile['recommendations'] = generate_recommendations(df, profile)
        
        return profile
        
    except Exception as e:
        st.error(f"Error profiling data: {str(e)}")
        return {'overview': {}, 'columns': {}, 'correlations': {}, 'recommendations': []}

def detect_outliers(series: pd.Series, method: str = 'iqr') -> List[int]:
    """Detect outliers in a numeric series"""
    try:
        if not pd.api.types.is_numeric_dtype(series):
            return []
        
        clean_series = series.dropna()
        if len(clean_series) < 4:
            return []
        
        if method == 'iqr':
            Q1 = clean_series.quantile(0.25)
            Q3 = clean_series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = series[(series < lower_bound) | (series > upper_bound)]
            return outliers.index.tolist()
        
        elif method == 'zscore':
            z_scores = np.abs((clean_series - clean_series.mean()) / clean_series.std())
            outliers = series[z_scores > 3]
            return outliers.index.tolist()
        
        return []
        
    except Exception:
        return []

def generate_recommendations(df: pd.DataFrame, profile: Dict[str, Any]) -> List[str]:
    """Generate data quality recommendations"""
    recommendations = []
    
    try:
        # High missing data
        for col, col_info in profile['columns'].items():
            if col_info['missing_percentage'] > 50:
                recommendations.append(f"Consider removing column '{col}' - {col_info['missing_percentage']:.1f}% missing data")
            elif col_info['missing_percentage'] > 20:
                recommendations.append(f"Review column '{col}' - {col_info['missing_percentage']:.1f}% missing data")
        
        # Low variance columns
        for col, col_info in profile['columns'].items():
            if col_info['unique_percentage'] < 1:
                recommendations.append(f"Column '{col}' has very low variance - consider removing")
        
        # Duplicate rows
        if profile['overview']['duplicate_rows'] > 0:
            recommendations.append(f"Remove {profile['overview']['duplicate_rows']} duplicate rows")
        
        # Data type suggestions
        type_suggestions = suggest_data_types(df)
        for col, suggested_type in type_suggestions.items():
            current_type = str(df[col].dtype)
            if suggested_type != current_type and suggested_type in ['int64', 'float64', 'datetime64[ns]', 'bool']:
                recommendations.append(f"Consider converting column '{col}' to {suggested_type}")
        
        # Memory optimization
        if profile['overview']['memory_usage_mb'] > 100:
            recommendations.append("Consider optimizing data types to reduce memory usage")
        
    except Exception as e:
        recommendations.append(f"Error generating recommendations: {str(e)}")
    
    return recommendations
