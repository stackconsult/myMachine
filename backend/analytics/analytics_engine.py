"""
Advanced Analytics Engine for CEP Machine
Production-ready analytics with ML-powered insights and predictions
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """
    Advanced analytics engine for business intelligence and predictions.
    Provides conversion analysis, prospect clustering, and predictive scoring.
    """
    
    def __init__(self):
        self._scaler = None
        self._kmeans = None
    
    def _get_scaler(self):
        """Lazy load StandardScaler"""
        if self._scaler is None:
            try:
                from sklearn.preprocessing import StandardScaler
                self._scaler = StandardScaler()
            except ImportError:
                logger.warning("scikit-learn not installed. Some features will be limited.")
        return self._scaler
    
    def _get_kmeans(self, n_clusters: int):
        """Lazy load KMeans"""
        try:
            from sklearn.cluster import KMeans
            return KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        except ImportError:
            logger.warning("scikit-learn not installed. Clustering not available.")
            return None
    
    async def analyze_prospect_conversion(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze prospect conversion patterns and identify key factors"""
        if not data:
            return {"error": "No data provided", "success": False}
        
        df = pd.DataFrame(data)
        
        result = {
            "success": True,
            "total_prospects": len(df),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        # Overall conversion rate
        if 'converted' in df.columns:
            result["overall_conversion_rate"] = float(df['converted'].mean() * 100)
            result["total_converted"] = int(df['converted'].sum())
            result["total_unconverted"] = int((~df['converted']).sum())
        
        # Conversion rate by source
        if 'source' in df.columns and 'converted' in df.columns:
            conversion_by_source = df.groupby('source')['converted'].agg(['mean', 'count'])
            result["conversion_by_source"] = {
                source: {
                    "conversion_rate": float(row['mean'] * 100),
                    "count": int(row['count'])
                }
                for source, row in conversion_by_source.iterrows()
            }
        
        # Conversion rate by industry
        if 'industry' in df.columns and 'converted' in df.columns:
            conversion_by_industry = df.groupby('industry')['converted'].agg(['mean', 'count'])
            result["conversion_by_industry"] = {
                industry: {
                    "conversion_rate": float(row['mean'] * 100),
                    "count": int(row['count'])
                }
                for industry, row in conversion_by_industry.iterrows()
            }
        
        # Conversion rate by location
        if 'location' in df.columns and 'converted' in df.columns:
            conversion_by_location = df.groupby('location')['converted'].agg(['mean', 'count'])
            top_locations = conversion_by_location.nlargest(10, 'mean')
            result["top_converting_locations"] = {
                location: {
                    "conversion_rate": float(row['mean'] * 100),
                    "count": int(row['count'])
                }
                for location, row in top_locations.iterrows()
            }
        
        # Time to convert analysis
        if 'converted' in df.columns and 'days_to_convert' in df.columns:
            converted_df = df[df['converted'] == True]
            if len(converted_df) > 0:
                result["time_to_convert"] = {
                    "avg_days": float(converted_df['days_to_convert'].mean()),
                    "median_days": float(converted_df['days_to_convert'].median()),
                    "min_days": float(converted_df['days_to_convert'].min()),
                    "max_days": float(converted_df['days_to_convert'].max())
                }
        
        # Best performing pitch types
        if 'pitch_type' in df.columns and 'converted' in df.columns:
            pitch_performance = df.groupby('pitch_type')['converted'].agg(['mean', 'count'])
            pitch_performance = pitch_performance.sort_values('mean', ascending=False)
            result["pitch_performance"] = {
                pitch_type: {
                    "conversion_rate": float(row['mean'] * 100),
                    "count": int(row['count'])
                }
                for pitch_type, row in pitch_performance.iterrows()
            }
            if len(pitch_performance) > 0:
                result["best_pitch_type"] = pitch_performance.index[0]
        
        # Conversion funnel
        if 'status' in df.columns:
            status_counts = df['status'].value_counts().to_dict()
            result["funnel"] = {str(k): int(v) for k, v in status_counts.items()}
        
        return result
    
    async def cluster_prospects(
        self, 
        data: List[Dict[str, Any]], 
        n_clusters: int = 5
    ) -> Dict[str, Any]:
        """Cluster prospects for targeted marketing using K-Means"""
        if not data:
            return {"error": "No data provided", "success": False}
        
        df = pd.DataFrame(data)
        
        # Select numerical features for clustering
        potential_features = ['revenue', 'employee_count', 'growth_rate', 'engagement_score', 
                            'email_opens', 'website_visits', 'meetings_scheduled']
        available_features = [f for f in potential_features if f in df.columns]
        
        if len(available_features) < 2:
            return {
                "success": False,
                "error": "Insufficient numerical features for clustering",
                "available_features": available_features,
                "required_features": 2
            }
        
        # Prepare data
        X = df[available_features].fillna(0)
        
        scaler = self._get_scaler()
        kmeans = self._get_kmeans(n_clusters)
        
        if scaler is None or kmeans is None:
            return {
                "success": False,
                "error": "scikit-learn not available for clustering"
            }
        
        try:
            X_scaled = scaler.fit_transform(X)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Calculate silhouette score
            try:
                from sklearn.metrics import silhouette_score
                silhouette_avg = float(silhouette_score(X_scaled, cluster_labels))
            except:
                silhouette_avg = None
            
            # Add cluster labels to dataframe
            df['cluster'] = cluster_labels
            
            # Analyze clusters
            cluster_analysis = {}
            for i in range(n_clusters):
                cluster_data = df[df['cluster'] == i]
                cluster_info = {
                    "size": int(len(cluster_data)),
                    "percentage": float(len(cluster_data) / len(df) * 100)
                }
                
                # Add feature averages
                for feature in available_features:
                    if feature in cluster_data.columns:
                        cluster_info[f"avg_{feature}"] = float(cluster_data[feature].mean())
                
                # Add conversion rate if available
                if 'converted' in cluster_data.columns:
                    cluster_info["conversion_rate"] = float(cluster_data['converted'].mean() * 100)
                
                cluster_analysis[f"cluster_{i}"] = cluster_info
            
            # Identify best cluster for targeting
            if 'converted' in df.columns:
                best_cluster = max(
                    cluster_analysis.items(),
                    key=lambda x: x[1].get('conversion_rate', 0)
                )
                best_cluster_name = best_cluster[0]
            else:
                best_cluster_name = None
            
            return {
                "success": True,
                "cluster_analysis": cluster_analysis,
                "silhouette_score": silhouette_avg,
                "n_clusters": n_clusters,
                "features_used": available_features,
                "total_prospects": len(df),
                "best_cluster_for_targeting": best_cluster_name,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Clustering error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def predict_likely_conversions(
        self, 
        data: List[Dict[str, Any]], 
        top_n: int = 10
    ) -> Dict[str, Any]:
        """Predict prospects most likely to convert using scoring model"""
        if not data:
            return {"error": "No data provided", "success": False}
        
        df = pd.DataFrame(data)
        
        # Initialize conversion score
        df['conversion_score'] = 0.0
        
        # Scoring weights
        weights = {
            'email_opens': 0.1,
            'website_visits': 0.15,
            'meetings_scheduled': 0.3,
            'engagement_score': 0.2,
            'growth_rate': 0.15,
            'revenue': 0.05,
            'employee_count': 0.05
        }
        
        # Calculate score based on available features
        for feature, weight in weights.items():
            if feature in df.columns:
                # Normalize feature to 0-1 range
                col = df[feature].fillna(0)
                if col.max() > col.min():
                    normalized = (col - col.min()) / (col.max() - col.min())
                else:
                    normalized = col
                df['conversion_score'] += normalized * weight
        
        # Boost score for certain conditions
        if 'status' in df.columns:
            df.loc[df['status'] == 'qualified', 'conversion_score'] *= 1.2
            df.loc[df['status'] == 'contacted', 'conversion_score'] *= 1.1
        
        if 'last_contact_days' in df.columns:
            # Penalize prospects not contacted recently
            df.loc[df['last_contact_days'] > 30, 'conversion_score'] *= 0.8
            df.loc[df['last_contact_days'] > 60, 'conversion_score'] *= 0.6
        
        # Sort by score and get top prospects
        df_sorted = df.nlargest(top_n, 'conversion_score')
        
        # Prepare results
        top_prospects = []
        for _, row in df_sorted.iterrows():
            prospect = {
                "conversion_score": float(row['conversion_score']),
                "score_percentile": float(
                    (df['conversion_score'] <= row['conversion_score']).mean() * 100
                )
            }
            
            # Add available fields
            for field in ['id', 'name', 'company', 'email', 'industry', 'location', 'status']:
                if field in row.index:
                    prospect[field] = row[field]
            
            top_prospects.append(prospect)
        
        return {
            "success": True,
            "top_prospects": top_prospects,
            "total_analyzed": len(df),
            "score_distribution": {
                "min": float(df['conversion_score'].min()),
                "max": float(df['conversion_score'].max()),
                "mean": float(df['conversion_score'].mean()),
                "median": float(df['conversion_score'].median())
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def generate_performance_report(
        self,
        data: List[Dict[str, Any]],
        period: str = "30d"
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not data:
            return {"error": "No data provided", "success": False}
        
        df = pd.DataFrame(data)
        
        # Parse period
        days = int(period.replace('d', ''))
        
        report = {
            "success": True,
            "period": period,
            "period_days": days,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {},
            "trends": {},
            "recommendations": []
        }
        
        # Summary statistics
        report["summary"]["total_records"] = len(df)
        
        if 'converted' in df.columns:
            report["summary"]["conversion_rate"] = float(df['converted'].mean() * 100)
            report["summary"]["total_conversions"] = int(df['converted'].sum())
        
        if 'revenue' in df.columns:
            report["summary"]["total_revenue"] = float(df['revenue'].sum())
            report["summary"]["avg_revenue"] = float(df['revenue'].mean())
        
        if 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
            report["summary"]["date_range"] = {
                "start": df['created_at'].min().isoformat(),
                "end": df['created_at'].max().isoformat()
            }
        
        # Trends analysis
        if 'created_at' in df.columns and 'converted' in df.columns:
            df['week'] = df['created_at'].dt.isocalendar().week
            weekly_conversion = df.groupby('week')['converted'].mean() * 100
            
            if len(weekly_conversion) >= 2:
                trend = "increasing" if weekly_conversion.iloc[-1] > weekly_conversion.iloc[0] else "decreasing"
                report["trends"]["conversion_trend"] = trend
                report["trends"]["weekly_conversion_rates"] = weekly_conversion.to_dict()
        
        # Generate recommendations
        recommendations = []
        
        if 'converted' in df.columns:
            conversion_rate = df['converted'].mean() * 100
            if conversion_rate < 10:
                recommendations.append({
                    "priority": "high",
                    "area": "conversion",
                    "recommendation": "Conversion rate is below 10%. Consider reviewing pitch quality and targeting criteria."
                })
            elif conversion_rate < 20:
                recommendations.append({
                    "priority": "medium",
                    "area": "conversion",
                    "recommendation": "Conversion rate has room for improvement. A/B test different pitch approaches."
                })
        
        if 'source' in df.columns and 'converted' in df.columns:
            source_performance = df.groupby('source')['converted'].mean()
            best_source = source_performance.idxmax()
            worst_source = source_performance.idxmin()
            
            if source_performance[best_source] > source_performance[worst_source] * 2:
                recommendations.append({
                    "priority": "medium",
                    "area": "sourcing",
                    "recommendation": f"Focus more on '{best_source}' source which has significantly higher conversion rates than '{worst_source}'."
                })
        
        if 'last_contact_days' in df.columns:
            stale_prospects = (df['last_contact_days'] > 30).mean() * 100
            if stale_prospects > 30:
                recommendations.append({
                    "priority": "high",
                    "area": "engagement",
                    "recommendation": f"{stale_prospects:.1f}% of prospects haven't been contacted in 30+ days. Prioritize re-engagement."
                })
        
        report["recommendations"] = recommendations
        
        return report
    
    async def analyze_outreach_effectiveness(
        self,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze outreach campaign effectiveness"""
        if not data:
            return {"error": "No data provided", "success": False}
        
        df = pd.DataFrame(data)
        
        result = {
            "success": True,
            "total_outreach": len(df),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        # Response rates
        if 'responded' in df.columns:
            result["response_rate"] = float(df['responded'].mean() * 100)
            result["total_responses"] = int(df['responded'].sum())
        
        # Channel effectiveness
        if 'channel' in df.columns:
            channel_stats = df.groupby('channel').agg({
                'responded': ['mean', 'count'] if 'responded' in df.columns else ['count']
            }).round(4)
            
            result["channel_effectiveness"] = {}
            for channel in channel_stats.index:
                result["channel_effectiveness"][channel] = {
                    "count": int(channel_stats.loc[channel, ('responded', 'count')] if 'responded' in df.columns else channel_stats.loc[channel, ('count',)]),
                }
                if 'responded' in df.columns:
                    result["channel_effectiveness"][channel]["response_rate"] = float(channel_stats.loc[channel, ('responded', 'mean')] * 100)
        
        # Best time to send
        if 'sent_at' in df.columns and 'responded' in df.columns:
            df['sent_at'] = pd.to_datetime(df['sent_at'])
            df['hour'] = df['sent_at'].dt.hour
            df['day_of_week'] = df['sent_at'].dt.day_name()
            
            hourly_response = df.groupby('hour')['responded'].mean() * 100
            daily_response = df.groupby('day_of_week')['responded'].mean() * 100
            
            result["best_send_hour"] = int(hourly_response.idxmax())
            result["best_send_day"] = daily_response.idxmax()
            result["hourly_response_rates"] = hourly_response.to_dict()
            result["daily_response_rates"] = daily_response.to_dict()
        
        return result
    
    async def calculate_roi(
        self,
        revenue_data: List[Dict[str, Any]],
        cost_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate ROI and financial metrics"""
        revenue_df = pd.DataFrame(revenue_data) if revenue_data else pd.DataFrame()
        cost_df = pd.DataFrame(cost_data) if cost_data else pd.DataFrame()
        
        result = {
            "success": True,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        # Calculate totals
        total_revenue = revenue_df['amount'].sum() if 'amount' in revenue_df.columns else 0
        total_cost = cost_df['amount'].sum() if 'amount' in cost_df.columns else 0
        
        result["total_revenue"] = float(total_revenue)
        result["total_cost"] = float(total_cost)
        result["net_profit"] = float(total_revenue - total_cost)
        
        # ROI calculation
        if total_cost > 0:
            result["roi_percentage"] = float((total_revenue - total_cost) / total_cost * 100)
        else:
            result["roi_percentage"] = None
        
        # Revenue breakdown by source
        if 'source' in revenue_df.columns:
            result["revenue_by_source"] = revenue_df.groupby('source')['amount'].sum().to_dict()
        
        # Cost breakdown by category
        if 'category' in cost_df.columns:
            result["cost_by_category"] = cost_df.groupby('category')['amount'].sum().to_dict()
        
        return result

# Global analytics engine instance
analytics_engine = AnalyticsEngine()
