"""Stable brand tokens for charts and native Streamlit components."""

PRIMARY = "#6757E5"
PRIMARY_LIGHT = "#AA9CF5"
INCOME = "#2D8A53"
SPENDING = "#D14B41"
MUTED = "#747783"


def style_figure(figure, *, height: int = 320):
    figure.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
    )
    return figure
