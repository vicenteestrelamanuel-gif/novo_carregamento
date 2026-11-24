import pandas as pd

def with_distance_consumption(df, quantity_col):
    """Calcula distância pela cronologia e odómetro; não inventa km quando faltam dados."""
    if df.empty:
        return df.copy()
    out = df.copy()
    out["event_date"] = pd.to_datetime(out["event_date"], errors="coerce")
    out = out.sort_values(["vehicle_id", "event_date", "id"]).copy()
    out["previous_odometer"] = out.groupby("vehicle_id")["odometer"].shift(1)
    out["distance_km"] = out["odometer"] - out["previous_odometer"]
    out.loc[(out["distance_km"] <= 0) | out["odometer"].isna() | out["previous_odometer"].isna(), "distance_km"] = pd.NA
    out["consumption"] = out[quantity_col] / out["distance_km"] * 100
    return out

def eur(value):
    return f"{float(value or 0):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
