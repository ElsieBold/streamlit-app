import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import re

# Fetch credentials from secrets
VALID_USERNAME = st.secrets["username"]
VALID_PASSWORD = st.secrets["password"]

# Session state to track login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔒 Please Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Invalid username or password")


def color_enabled(val):
    color = 'green' if val=='true' else 'yellow' if val==False else 'red'
    return f'background-color: {color}'


def clear_cache():
    st.cache_data.clear()

@st.cache_data
def getData():
    r = requests.get('https://api.qa.trellis.arizona.edu/ws/rest/v1/util/getScheduledJobs/trellis/') 
    return r 

# @st.cache_data
def getJobs(table, field):
    target_field = f"{table}/{field}" if table and field else None
 
    if target_field:
        st.markdown(f"🔍 Searching for: `{target_field}`")

        birdGIF = "https://media1.tenor.com/m/dd4FpdbO7cIAAAAd/cute-bird-loader-loader.gif"
        

        placeholder = st.empty()
        placeholder.image(birdGIF, caption="Loading... please wait 🐦 The initial load takes more than a minute")
        
        r = getData()
        placeholder.empty()
        
        # st.text(r.text)
    # st.text(r.content)

        xml_string = r.text

        if xml_string:
            try:
                found = False
                maps = []
                components = re.findall(r'(<Component.*?</Component>)', r.text, re.DOTALL)
                for comp in components:
                    # st.text("Component length: " + str(len(components))) 
                    root = ET.fromstring(comp)
                    ns = {'bns': 'http://api.platform.boomi.com/'}
                    mappings = root.findall('.//bns:object/Map/Mappings/Mapping', namespaces=ns)
                    for mapping in mappings:
                        if (mapping.attrib.get('toNamePath') != None):
                        #     st.text("Mapping in mappings: " + mapping.attrib.get('toNamePath'))
                            if mapping.attrib.get('toNamePath').lower() == target_field.lower():
                                found = True
                                # st.code(ET.tostring(mapping, encoding='unicode'), language='xml')
                                # map_name = comp.attrib.get('name')
                                # st.text("Component name: " + comp)
                                map_name = root.attrib.get('name')
                                if map_name:
                                    maps.append(map_name)
                                    # st.text("Map name: " + map_name)
                                break
                    
            except ET.ParseError as e:
                st.error(f"XML Parse Error: {e}")
        else:
            target_field = None
            st.text("Please enter both table and field names to proceed.")

        if maps:
            st.success("Found mapping to " + target_field)
            df = pd.DataFrame(maps, columns=["Map Name"])
            st.table(df)
        else:
            st.warning("No maps found.")
        
    return


def main_app():
    st.sidebar.title('Boomi SF Mapping Search')
    table = st.sidebar.text_input("Enter Salesforce Object name (e.g., Contact)")
    field = st.sidebar.text_input("Enter field name (e.g., EDS_Primary_Affiliation__c)")

    st.sidebar.button('Search',  on_click=getJobs, args=(table, field), type="primary")

    st.sidebar.button('Clear Cache', on_click=clear_cache)

# Render login or app
if not st.session_state.logged_in:
    login()
else:
    main_app()