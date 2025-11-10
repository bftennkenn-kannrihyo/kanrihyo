import pandas as pd


def read_excel(upload):
if upload is None:
return None
df = pd.read_excel(upload)
df.columns = [str(c).strip() for c in df.columns]
return df
