"""
Bieu do tuong tac (Plotly) cho lich tau, mo trong trinh duyet.

- Re chuot vao tau: hien ten, ma, terminal, hang/tuyen, D/L/S, so cau, gio bat dau/ket thuc, gio cho.
- Phong to: keo chon mot vung; nhay dup de tro ve.
- Bam vao ten hang o chu thich ben phai de an/hien tau cua hang do.
- Bieu do duoi: so cau dang dung moi gio so voi Q.

File nay khong tu chay; run.py va random_case.py goi ham show_schedule().
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from plot_schedule import OP_COLOR, BERTHS

pio.renderers.default = "browser"   # chay script thuong -> mo tab trinh duyet


def _hover(r):
    lines = [
        f"<b>{r['name']}</b>  ({r['code']})",
        f"Terminal: {r.get('terminal', '') or '-'}  |  {r['operator']} / {r['service']}",
        f"D: {int(r['dis'])}  L: {int(r['load'])}  S: {int(r['shift'])}  (W = {int(r['W'])} moves)",
        f"Position: {r['start_m']:.0f}–{r['end_m']:.0f} m  |  length {r['loa_m']:.0f} m",
        f"Start: {pd.Timestamp(r['start']):%d/%m %H:%M}  →  Finish: {pd.Timestamp(r['end']):%d/%m %H:%M}",
        f"Cranes: {int(r['k'])}",
    ]
    if "wait_h" in r and pd.notna(r.get("wait_h")):
        lines.append(f"Waiting: {r['wait_h']:.0f} h  |  At berth: {r['stay_h']:.0f} h")
    if r.get("fixed"):
        lines.append("<i>Already at berth before the plan starts (fixed)</i>")
    return "<br>".join(lines)


def build_figure(sched: pd.DataFrame, t_from, t_to, title, quay_len=2000, Q=None):
    t_from, t_to = pd.Timestamp(t_from), pd.Timestamp(t_to)
    rows = 2 if Q is not None else 1
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        row_heights=[0.8, 0.2] if rows == 2 else [1.0])

    # dai ben B4..B8
    berth_len = quay_len / len(BERTHS)
    for b, name in enumerate(BERTHS):
        fig.add_hrect(y0=b * berth_len, y1=(b + 1) * berth_len, row=1, col=1,
                      fillcolor="#eef1f7" if b % 2 else "white", line_width=0, layer="below")
        fig.add_annotation(x=1.005, xref="paper", y=(b + 0.5) * berth_len, yref="y",
                           text=f"<b>{name}</b>", showarrow=False, xanchor="left",
                           font=dict(size=13, color="#555"))

    # moi tau la mot hinh chu nhat (Scatter fill = toself), re chuot vao hien thong tin
    shown_ops = set()
    for _, r in sched.iterrows():
        x0, x1 = pd.Timestamp(r["start"]), pd.Timestamp(r["end"])
        y0, y1 = r["start_m"], r["end_m"]
        op = r["operator"]
        col = OP_COLOR.get(op, "#cccccc")
        fig.add_trace(go.Scatter(
            x=[x0, x1, x1, x0, x0], y=[y0, y0, y1, y1, y0],
            mode="lines", fill="toself", fillcolor=col, opacity=0.55 if r.get("fixed") else 0.95,
            line=dict(color="#333", width=1, dash="dot" if r.get("fixed") else "solid"),
            hoveron="fills", hoverinfo="text", text=_hover(r),
            name=op, legendgroup=op, showlegend=op not in shown_ops,
        ), row=1, col=1)
        shown_ops.add(op)
        # nhan ngan o giua hinh
        fig.add_trace(go.Scatter(
            x=[x0 + (x1 - x0) / 2], y=[(y0 + y1) / 2], mode="text",
            text=[f"{r['code']}<br>{int(r['k'])} cranes"], textfont=dict(size=10, color="#111"),
            hoverinfo="skip", legendgroup=op, showlegend=False,
        ), row=1, col=1)

    fig.update_yaxes(title_text="Position along quay (m)", range=[quay_len, 0], row=1, col=1)

    # so cau dang dung
    if Q is not None:
        hours = pd.date_range(t_from, t_to, freq="h")
        used = [int(sched[(sched["start"] <= h) & (sched["end"] > h)]["k"].sum()) for h in hours]
        fig.add_trace(go.Scatter(x=hours, y=used, mode="lines", line_shape="hv",
                                 line=dict(color="#2b6fd6", width=2), name="Cranes in use",
                                 hovertemplate="%{x|%d/%m %H:%M}: %{y} cranes<extra></extra>"),
                      row=2, col=1)
        fig.add_hline(y=Q, line=dict(color="#d33a3a", dash="dash"), row=2, col=1,
                      annotation_text=f"Q = {Q}", annotation_position="top left")
        fig.update_yaxes(title_text="Cranes", range=[0, Q + 3], row=2, col=1)

    fig.update_xaxes(range=[t_from, t_to], dtick=6 * 3600 * 1000, tickformat="%H\n%d/%m",
                     showgrid=True, gridcolor="#ddd")
    fig.update_layout(title=dict(text=title, x=0.01), height=850 if rows == 2 else 700,
                      hovermode="closest", plot_bgcolor="white",
                      legend=dict(title="Operator (click to hide/show)", x=1.04, y=1),
                      margin=dict(l=70, r=200, t=70, b=40))
    return fig


def show_schedule(sched, t_from, t_to, title, quay_len=2000, Q=None, html_path=None):
    """Mo bieu do trong trinh duyet. Neu html_path duoc dua vao thi luu them file .html."""
    fig = build_figure(sched, t_from, t_to, title, quay_len, Q)
    if html_path:
        fig.write_html(html_path, include_plotlyjs="cdn")
    fig.show()
    return fig
