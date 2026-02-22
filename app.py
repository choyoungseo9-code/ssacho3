import streamlit as st
import pandas as pd
import random
import requests
import PublicDataReader as pdr
from bs4 import BeautifulSoup
from datetime import datetime
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Real Estate Dashboard", page_icon="H", layout="wide")
st.title("Real Estate Dashboard")

def generate_mock_summary(title):
      return "Summary: Latest real estate news and trends."

@st.cache_data(ttl=3600)
def get_latest_news(query, num=5):
      url = f"https://search.naver.com/search.naver?where=news&query={query}"
      headers = {"User-Agent": "Mozilla/5.0"}
      response = requests.get(url, headers=headers)
      soup = BeautifulSoup(response.text, 'html.parser')
      news_list = []
      today_date = datetime.now().strftime("%Y-%m-%d")
      all_links = soup.find_all('a')
      seen_links = set()
      for a in all_links:
                if len(news_list) >= num: break
                          href = a.get('href', '')
                title = a.get('title', a.text.strip())
                if title and len(title) > 15 and ('news' in href or 'article' in href) and href not in seen_links:
                              seen_links.add(href)
                              news_list.append({"title": title, "link": href, "date": today_date})
                      return news_list

@st.cache_data(ttl=86400)
def get_bdong_data():
      try:
                bdong = pdr.code_bdong()
                return bdong
            except:
        return pd.DataFrame()

              import urllib.parse
              import xml.etree.ElementTree as ET

              def get_real_estate_data(sigungu_code, dong_name, api_key):
                    if not api_key:
                              st.error("API Key missing")
                              return pd.DataFrame()
                          sigungu_code_5 = str(sigungu_code)[:5]
                    decoded_key = urllib.parse.unquote(api_key)
                    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
                    now = datetime.now()
                    df_list = []
                    for i in range(6):
                              target_month = (now - pd.DateOffset(months=i)).strftime("%Y%m")
                              params = {"serviceKey": decoded_key, "pageNo": "1", "numOfRows": "9999", "LAWD_CD": sigungu_code_5, "DEAL_YMD": target_month}
                              try:
                                            res = requests.get(url, params=params, verify=False, timeout=10)
                                            root = ET.fromstring(res.content)
                                            items = root.findall('.//item')
                                            month_data = []
                                            for item in items:
                                                              month_data.append({
                                                                                    'aptNm': item.findtext('aptNm'),
                                                                                    'excluUseAr': item.findtext('excluUseAr'),
                                                                                    'dealAmount': item.findtext('dealAmount'),
                                                                                    'dealYear': item.findtext('dealYear'),
                                                                                    'dealMonth': item.findtext('dealMonth'),
                                                                                    'dealDay': item.findtext('dealDay'),
                                                                                    'floor': item.findtext('floor'),
                                                                                    'umdNm': item.findtext('umdNm')
                                                              })
                                                          if month_data: df_list.append(pd.DataFrame(month_data))
                                                                    except: pass
                                                                          if not df_list: return pd.DataFrame()
                                                                                df = pd.concat(df_list, ignore_index=True)
                          return df

@st.cache_data(ttl=604800)
def get_lat_lon(query):
      url = "https://nominatim.openstreetmap.org/search"
    params = {'q': query, 'format': 'json', 'limit': 1, 'countrycodes': 'kr'}
    headers = {'User-Agent': 'Dashboard/1.0'}
    try:
              res = requests.get(url, params=params, headers=headers, timeout=5).json()
              if res: return float(res[0]['lat']), float(res[0]['lon'])
                    except: pass
                          return 37.4200, 127.1267

@st.cache_data(ttl=3600)
def reverse_geocode(lat, lon):
      url = "https://nominatim.openstreetmap.org/reverse"
    params = {'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 16}
    headers = {'User-Agent': 'Dashboard/1.0'}
    try:
              res = requests.get(url, params=params, headers=headers, timeout=5).json()
        addr = res.get('address', {})
        return {'display': res.get('display_name', ''), 'sido': addr.get('state', ''), 'sigungu': addr.get('city', ''), 'dong': addr.get('suburb', '')}
    except: return None

bdong_df = get_bdong_data()
st.sidebar.header("Location Selection")
selected_sido, selected_sigungu, selected_dong, sigungu_code = "Gyeonggi-do", "Seongnam-si", "All", "41135"
st.sidebar.info(f"Region: {selected_sido} {selected_sigungu} {selected_dong}")

api_key_input = st.sidebar.text_input("API Key", type="password", value="a87ba726bf60fe1410dba0dd0cba7b90cc095c917c3bb31b0e1b0b76d8d33675")

st.markdown("---")
map_col, info_col = st.columns([1, 2])
with map_col:
      search_query_map = f"{selected_sido} {selected_sigungu} {selected_dong}"
    lat, lon = get_lat_lon(search_query_map)
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], tooltip=selected_dong).add_to(m)
    map_data = st_folium(m, width=None, height=350, returned_objects=["center"])

with info_col:
      st.markdown(f"#### Location: {selected_sigungu} {selected_dong}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Sido", selected_sido)
    m2.metric("Sigungu", selected_sigungu)
    m3.metric("Dong", selected_dong)

st.markdown("---")
tab_trade, tab_news = st.tabs(["Real Estate Transactions", "Local News"])

with tab_trade:
      df = get_real_estate_data(sigungu_code, selected_dong, api_key_input)
    if not df.empty:
              st.dataframe(df, use_container_width=True)
else:
        st.warning("No data found or check API key.")

with tab_news:
      news = get_latest_news(f"{selected_sigungu} Real Estate", num=5)
    if news:
              for n in news:
                            st.markdown(f"- [{n['title']}]({n['link']})")
else:
        st.info("No news found.")
