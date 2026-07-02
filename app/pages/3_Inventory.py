"""Inventory dashboard page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.database.base import session_scope
from app.services.inventory_service import InventoryService

st.title("Inventory")
st.caption("On-hand stock levels and reorder alerts.")

with session_scope() as session:
    service = InventoryService(session)
    on_hand_rows = service.on_hand_report()
    low_stock = service.low_stock_alert()

    on_hand_df = pd.DataFrame(on_hand_rows, columns=["SKU", "Product", "On Hand"])
    total_active_skus = len(on_hand_df)
    total_units = on_hand_df["On Hand"].sum() if not on_hand_df.empty else 0

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Active SKUs", total_active_skus)
kpi2.metric("Low stock products", len(low_stock))
kpi3.metric("Total units on hand", f"{total_units:,.0f}")

st.subheader("Top 15 products by on-hand quantity")
if on_hand_df.empty:
    st.info("No active products found. Run the synthetic data generator first.")
else:
    top15 = on_hand_df.sort_values("On Hand", ascending=False).head(15)
    st.bar_chart(top15.set_index("SKU")["On Hand"])
