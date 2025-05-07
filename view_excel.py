import pandas as pd

# 查看2023级数据
file_path_2023 = "历史数据/2023级.xlsx"
df_2023 = pd.read_excel(file_path_2023)
print("2023级数据结构:")
print(df_2023.head())
print("\n列名:", df_2023.columns.tolist())
print("\n数据形状:", df_2023.shape)

# 查看2024级数据
file_path_2024 = "历史数据/2024级.xlsx"
df_2024 = pd.read_excel(file_path_2024)
print("\n\n2024级数据结构:")
print(df_2024.head())
print("\n列名:", df_2024.columns.tolist())
print("\n数据形状:", df_2024.shape) 