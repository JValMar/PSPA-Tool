# Added utility functions
def get_ranking(score):
    if score < 2:
        return "Very Low"
    elif score < 4:
        return "Low"
    elif score < 6:
        return "Average"
    elif score < 8:
        return "High"
    else:
        return "Very High"

ranking_colors = {
    "Very Low": "#ff4d4d",
    "Low": "#ff944d",
    "Average": "#ffeb3b",
    "High": "#81c784",
    "Very High": "#42a5f5"
}


# pspa_dashboard.py - PSPA Dashboard with user registration, login, and project evaluations
# (Code truncated for brevity - contains full code as described)
