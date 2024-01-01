
import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas
import folium

from folium.features import CustomIcon
from folium.plugins import MarkerCluster
from folium import Circle, Marker
from folium import GeoJson
from streamlit_folium import st_folium

import requests
import branca
from babel.numbers import format_currency



sns.set(style='dark')

# Helper function yang dibutuhkan untuk menyiapkan berbagai dataframe

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='M', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "total_price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "total_price": "revenue"
    }, inplace=True)

    return daily_orders_df

def create_sum_order_items_df(df):
    #sum_order_items_df = df.groupby("product_category_name").product_id.sum().sort_values(ascending=False).reset_index()
    sum_order_items_df = df.groupby(by="product_category_name_english").count().reset_index() #jumlah pembelian
    sum_order_items_df = sum_order_items_df.rename(columns={"product_category_name_english": "category", "product_id": "quantity_x"})
    return sum_order_items_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", #mengambil tanggal order terakhir
        "order_id": "nunique",
        "total_price": "sum"
    })
    rfm_df.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    return rfm_df


# Load cleaned data
all_df = pd.read_csv("https://raw.githubusercontent.com/abdul-rohman-lab/projek_olist/main/Dashboard/otp_orders_customers.csv")
poi_df = pd.read_csv("https://raw.githubusercontent.com/abdul987a/resource/main/poi_data.csv")
revenue_from_customer_geo = pd.read_csv("https://raw.githubusercontent.com/abdul-rohman-lab/projek_olist/main/Dashboard/revenue_from_customer_geo.csv")

st.set_page_config(layout="wide")

#st.dataframe(data=all_df)

datetime_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date']
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)

for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

# Filter data
min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()


with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://github.com/abdul-rohman-lab/projek_olist/blob/main/logo_olist_d7309b5f20.png")

    st.image(
            "https://github.com/abdul-rohman-lab/projek_olist/blob/main/logo_olist_d7309b5f20.png",
            width=400, # Manually Adjust the width of the image as per requirement
        )



    # Menambahkan logo perusahaan
    st.subheader("Olist Store")

    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) &
                (all_df["order_purchase_timestamp"] <= str(end_date))]



# # Menyiapkan berbagai dataframe
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(poi_df)
rfm_df = create_rfm_df(main_df)
#st.dataframe(daily_orders_df)

# plot number of daily orders (2021)
st.header('Olist Store Dashboard :sparkles:')
st.subheader('Daily Orders')

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total orders", value=total_orders)

with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL ", locale='es_CO')
    st.metric("Total Revenue", value=total_revenue)


# ===========================================
st.subheader("Tren Order Olist Shop")

fig, ax = plt.subplots(figsize=(30, 10))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
ax.set_title('Tren Order 2016=2018', loc="center", fontsize=20, pad=20)
for x,y in zip(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"]):

    label = "{:.2f}".format(y)

    ax.annotate(label, # this is the text
                 (x,y), # these are the coordinates to position the label
                 textcoords="offset points", # how to position the text
                 xytext=(0,10), # distance from text to points (x,y)
                 ha='center') # horizontal alignment can be left, right or center)

st.pyplot(fig)

#===========================================================
# Product performance
st.subheader("Best & Worst Performing Category Product")

#st.dataframe(sum_order_items_df)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 12))

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="quantity_x", y="category", data=sum_order_items_df.sort_values('quantity_x', ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=30)
ax[0].set_title("Best Performing Product", loc="center", fontsize=50, pad=20)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)
ax[0].bar_label(ax[0].containers[0], label_type='center', fontsize=20)

sns.barplot(x="quantity_x", y="category", data=sum_order_items_df.sort_values(by="quantity_x", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=30)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50, pad=20)
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
ax[1].bar_label(ax[1].containers[0], label_type='center', fontsize=20)

st.pyplot(fig)

# ===============================================================

st.subheader("5 Customer Cities with the highest and lowest revenue")

city_revenue = all_df.groupby('customer_city', as_index=False).agg({'total_price': 'sum'})
city_revenue['%_revenue'] = (city_revenue.total_price/city_revenue.total_price.sum())*100

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 10))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(city_revenue.sort_values(by="%_revenue", ascending=False).head(5), x="customer_city", y="%_revenue", palette=colors, ax=ax[0])
ax[0].set_ylabel('Persen Revenue', fontsize=12)
ax[0].set_xlabel(None)
# ticks = [0, 500000, 1500000, 2000000]
# ax[0].set_yticks(ticks)
ax[0].set_title("Pendapatan 5 terbesar per Kota Customer", loc="center", fontsize=15)
ax[0].tick_params(axis ='y', labelsize=12)
ax[0].tick_params(axis ='x', labelsize=20, rotation=90)
ax[0].bar_label(ax[0].containers[0], label_type='center', fontsize=12)



sns.barplot(city_revenue.sort_values(by="%_revenue").head(5), x="customer_city", y="%_revenue", palette=colors, ax=ax[1])
ax[1].set_ylabel('Persen Revenue', fontsize=12)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Pendapatan 5 terkecil per kota Customer", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)
ax[1].tick_params(axis ='x', labelsize=20, rotation=90)
ax[1].bar_label(ax[1].containers[0], label_type='center', fontsize=12)

plt.suptitle("5 Kota Customer Dengan Revenue Yang Terbanyak dan Terkecil", fontsize=20)
plt.show()
st.pyplot(fig)


# ================================================================
st.subheader("Best & Worst Revenue From Customer")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 10))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(all_df.sort_values(by="total_price", ascending=False).head(5), x="customer_unique_id", y="total_price", palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Pendapatan 5 Customer terbesar", loc="center", fontsize=15)
ax[0].tick_params(axis ='y', labelsize=12)
ax[0].tick_params(axis ='x', labelsize=12, rotation=90)
ax[0].bar_label(ax[0].containers[0], label_type='center', fontsize=12)



sns.barplot(all_df.sort_values(by="total_price").head(5), x="customer_unique_id", y="total_price", palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Pendapatan 5 Customer Terkecil", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=12)
ax[1].tick_params(axis ='x', labelsize=12, rotation=90)
ax[1].bar_label(ax[1].containers[0], label_type='center', fontsize=12)

plt.suptitle("5 Pendapatan Terbesar & Terkecil Dari Customer ID", fontsize=20)
plt.show()
st.pyplot(fig)


#=================================================================

st.subheader("Geoanalysist Sebaran Total Revenue Per State")

revenue_perstate = all_df.groupby(by='customer_state').agg({'total_price': 'sum'})
revenue_perstate['in_%'] = (revenue_perstate.total_price/revenue_perstate.total_price.sum())*100


state_geo = requests.get(
    "https://raw.githubusercontent.com/giuliano-oliveira/geodata-br-states/main/geojson/br_states.json"
).json()

states = geopandas.GeoDataFrame.from_features(state_geo, crs="EPSG:4326")

df = pd.merge(
    left = states,
    right = revenue_perstate,
    how = 'left',
    left_on = 'SIGLA',
    right_on = 'customer_state',
)

colormap = branca.colormap.LinearColormap(
    vmin=df["in_%"].quantile(0.0),
    vmax=df["in_%"].quantile(1),
    colors=["red", "orange", "lightblue", "green", "darkgreen"],
    caption="State Level Median County Household Income (%)",
)

m = folium.Map(location=[-7.656919199019851, -55.3408624450622], zoom_start=4)

popup = folium.GeoJsonPopup(
    fields=["SIGLA", "in_%"],
    aliases=["State", "% Revenue"],
    localize=True,
    labels=True,
    style="background-color: yellow;",
)

tooltip = folium.GeoJsonTooltip(
    fields=["SIGLA", "in_%"],
    aliases=["State:", "% Revenue"],
    localize=True,
    sticky=False,
    labels=True,
    style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
    """,
    max_width=800,
)


g = folium.GeoJson(
    df,
    style_function=lambda x: {
        "fillColor": colormap(x["properties"]["in_%"])
        if x["properties"]["in_%"] is not None
        else "transparent",
        "color": "black",
        "fillOpacity": 0.4,
    },
    tooltip=tooltip,
    popup=popup,
).add_to(m)

colormap.add_to(m)


#st_data = st_folium(m, width=725)
st_data = st_folium(m)







#==================================================================
# Best Customer Based on RFM Parameters
st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "BRL ", locale='es_CO')
    st.metric("Average Monetary", value=avg_frequency)


fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="customer_unique_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=20, rotation = 90)
ax[0].bar_label(ax[0].containers[0], label_type='center')

sns.barplot(y="frequency", x="customer_unique_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=20, rotation = 90)
ax[1].bar_label(ax[1].containers[0], label_type='center')

sns.barplot(y="monetary", x="customer_unique_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=20, rotation = 90)
ax[2].bar_label(ax[2].containers[0], label_type='center')

st.pyplot(fig)

#=====================================================
# Cluster Segment Customers
st.subheader("Cluster Segment Customers")

rfm_df['segment'] = 'low value'
rfm_df.loc[rfm_df['frequency'] > 3, 'segment'] = 'mid_value'
rfm_df.loc[rfm_df['frequency'] > 6, 'segment'] = 'high_value'

segment = rfm_df.groupby(by='segment', as_index=False).agg({'customer_unique_id': 'nunique'})
segment['in_%'] = (segment.customer_unique_id/segment.customer_unique_id.sum())*100


fig = plt.figure(figsize=(10, 4))
ax = sns.barplot(x='segment', y='in_%',
                 data=segment,
                 errwidth=0)

for i in ax.containers:
    ax.bar_label(i,)

st.pyplot(fig)


for i in ax.containers:
    ax.bar_label(i,)

st.caption('Copyright © Abdul Rohman 2023')
