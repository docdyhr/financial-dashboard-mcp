"""ISIN Analytics data quality components."""

import streamlit as st
from .isin_analytics_data import get_quality_metrics
from .isin_analytics_charts import create_quality_charts


def data_quality_analysis():
    """Analyze data quality metrics."""
    st.subheader("🎯 Data Quality Analysis")

    quality_metrics = get_quality_metrics()
    if not quality_metrics:
        st.error("Unable to load quality metrics")
        return

    # Quality overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        overall_score = quality_metrics.get("overall_score", 0)
        st.metric(
            "Overall Score",
            f"{overall_score:.1f}",
            delta=f"{overall_score - 85:.1f}" if overall_score > 85 else None,
        )

    with col2:
        validation_accuracy = quality_metrics.get("validation_accuracy", 0)
        st.metric(
            "Validation Accuracy",
            f"{validation_accuracy:.1f}%",
            delta=f"{validation_accuracy - 90:.1f}%" if validation_accuracy > 90 else None,
        )

    with col3:
        completeness = quality_metrics.get("completeness", 0)
        st.metric(
            "Data Completeness",
            f"{completeness:.1f}%",
            delta=f"{completeness - 85:.1f}%" if completeness > 85 else None,
        )

    with col4:
        timeliness = quality_metrics.get("timeliness", 0)
        st.metric(
            "Timeliness",
            f"{timeliness:.1f}%",
            delta=f"{timeliness - 80:.1f}%" if timeliness > 80 else None,
        )

    # Quality breakdown chart
    col1, col2 = st.columns(2)
    
    with col1:
        create_quality_charts(quality_metrics)

    with col2:
        st.subheader("Quality Insights")
        
        # Quality recommendations based on scores
        consistency = quality_metrics.get("consistency", 0)
        
        if overall_score >= 95:
            st.success("🎉 Excellent data quality! System is performing optimally.")
        elif overall_score >= 85:
            st.info("📊 Good data quality with room for improvement.")
        elif overall_score >= 70:
            st.warning("⚠️ Data quality needs attention in some areas.")
        else:
            st.error("🔴 Data quality requires immediate action.")

        st.write("**Quality Factors:**")
        
        # Individual quality indicators
        if validation_accuracy >= 95:
            st.write("✅ Validation accuracy is excellent")
        elif validation_accuracy >= 90:
            st.write("🟡 Validation accuracy is good")
        else:
            st.write("🔴 Validation accuracy needs improvement")

        if completeness >= 90:
            st.write("✅ Data completeness is excellent")
        elif completeness >= 80:
            st.write("🟡 Data completeness is acceptable")
        else:
            st.write("🔴 Data completeness needs improvement")

        if timeliness >= 85:
            st.write("✅ Data timeliness is excellent")
        elif timeliness >= 75:
            st.write("🟡 Data timeliness is acceptable")
        else:
            st.write("🔴 Data timeliness needs improvement")

        if consistency >= 95:
            st.write("✅ Data consistency is excellent")
        elif consistency >= 90:
            st.write("🟡 Data consistency is good")
        else:
            st.write("🔴 Data consistency needs improvement")

    # Detailed quality metrics table
    st.subheader("📋 Detailed Quality Metrics")
    
    quality_data = [
        {"Metric": "Overall Score", "Value": f"{overall_score:.1f}", "Target": "≥90", "Status": "✅" if overall_score >= 90 else "⚠️"},
        {"Metric": "Validation Accuracy", "Value": f"{validation_accuracy:.1f}%", "Target": "≥95%", "Status": "✅" if validation_accuracy >= 95 else "⚠️"},
        {"Metric": "Data Completeness", "Value": f"{completeness:.1f}%", "Target": "≥90%", "Status": "✅" if completeness >= 90 else "⚠️"},
        {"Metric": "Timeliness", "Value": f"{timeliness:.1f}%", "Target": "≥85%", "Status": "✅" if timeliness >= 85 else "⚠️"},
        {"Metric": "Consistency", "Value": f"{consistency:.1f}%", "Target": "≥95%", "Status": "✅" if consistency >= 95 else "⚠️"},
    ]
    
    st.dataframe(
        quality_data,
        column_config={
            "Metric": "Quality Metric",
            "Value": "Current Value",
            "Target": "Target Threshold",
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )

    # Quality improvement recommendations
    st.subheader("💡 Improvement Recommendations")
    
    recommendations = []
    
    if validation_accuracy < 95:
        recommendations.append("🔍 Review and improve ISIN validation algorithms")
    if completeness < 90:
        recommendations.append("📝 Enhance data collection processes to improve completeness")
    if timeliness < 85:
        recommendations.append("⚡ Optimize data synchronization frequency and performance")
    if consistency < 95:
        recommendations.append("🔄 Implement stricter data consistency checks")
    if overall_score < 90:
        recommendations.append("📊 Conduct comprehensive data quality audit")

    if recommendations:
        for rec in recommendations:
            st.write(f"• {rec}")
    else:
        st.success("🎯 All quality metrics are meeting or exceeding targets!")

    # Quality trends (placeholder for future enhancement)
    with st.expander("📈 Quality Trends (Coming Soon)"):
        st.info("Quality trend analysis and historical tracking will be available in future releases.")
        st.write("Features will include:")
        st.write("• Historical quality score tracking")
        st.write("• Quality degradation alerts")
        st.write("• Automated quality reports")
        st.write("• Quality SLA monitoring")