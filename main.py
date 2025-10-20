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

    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

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
    st.success("🔄 Cache cleared")

@st.cache_data
def getData():
    api_key = st.secrets["qa-x-api-key"]
    headers = {
        "x-api-key": api_key  

    }
    r = requests.get('https://api.qa.trellis.arizona.edu/ws/rest/bft-component-search/v1/sf-mappings/', headers=headers) 
    return r 

# @st.cache_data
def searchByFieldName(r, table, field):
    target_field = f"{table}/{field}" if table and field else None
    if not target_field:
        st.warning("⚠️ Please enter both table and field names.")
        return None
 
    if target_field:
        st.markdown(f"🔍 Searching for: `{target_field}`")
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
                                map_name = root.attrib.get('name')
                                if map_name:
                                    if (mapping.attrib.get('fromNamePath') != None):
                                        maps.append([map_name, mapping.attrib.get('fromNamePath'), mapping.attrib.get('toNamePath')])
                                    else:
                                        maps.append([map_name, mapping.attrib.get('fromType'), mapping.attrib.get('toNamePath')])
                                break
                    
            except ET.ParseError as e:
                st.error(f"XML Parse Error: {e}")
        else:
            target_field = None
            st.text("Please enter both table and field names to proceed.")

        if maps:
            st.success("Found mapping to " + target_field)
            df = pd.DataFrame(maps, columns=["Map Name","From Field", "To Field"])
            st.table(df)
        else:
            st.warning("No maps found.")
        
    return

# @st.cache_data
def searchByObject(r, obj):
    target_obj = f"{obj}/" if obj else None
    if not target_obj:
        st.warning("⚠️ Please enter table/object name.")
        return None
 
    if target_obj:
        st.markdown(f"🔍 Searching for: `{target_obj}`")
        xml_string = r.text
        if xml_string:
            try:
                found = False
                maps = []
                maps_dict = {}
                components = re.findall(r'(<Component.*?</Component>)', r.text, re.DOTALL)
                for comp in components:
                    # st.text("Component length: " + str(len(components))) 
                    root = ET.fromstring(comp)
                    ns = {'bns': 'http://api.platform.boomi.com/'}
                    mappings = root.findall('.//bns:object/Map/Mappings/Mapping', namespaces=ns)
                    
                    for mapping in mappings:
                        to_name = mapping.attrib.get('toNamePath')
                        from_name = mapping.attrib.get('fromNamePath')
                        from_type = mapping.attrib.get('fromType')
                        
                        if to_name is not None and target_obj.lower() in to_name.lower():
                            found = True
                            map_name = root.attrib.get('name')
                            from_field = from_name if from_name is not None else from_type
        
                            if map_name not in maps_dict:
                                maps_dict[map_name] = []
                            maps_dict[map_name].append([from_field, to_name])

            except ET.ParseError as e:
                st.error(f"XML Parse Error: {e}")
        # After processing all mappings
        if maps_dict:
            st.success(f"Found mapping(s) for {target_obj} object")
            
            for map_name, field_pairs in maps_dict.items():
                with st.expander("Map name: " + map_name):
                    df = pd.DataFrame(field_pairs, columns=["From Field", "To Field"])
                    st.table(df)
        else:
            st.warning("No maps found.")
    return

def main_app():
    birdGIF = "https://media1.tenor.com/m/dd4FpdbO7cIAAAAd/cute-bird-loader-loader.gif"
    

    placeholder = st.empty()
    placeholder.image(birdGIF, caption="Loading data...")
    
    r = getData()
    placeholder.empty()
    st.sidebar.title('Boomi SF Mapping Search')
    
    # Sidebar buttons
    search_by_field = st.sidebar.button('🔍 Search By Field Name', type="primary")
    search_by_object = st.sidebar.button('🔍 Search By Object', type="primary")
    st.sidebar.button('🧹 Clear Cache', on_click=clear_cache)

    # Use session_state to remember which route was chosen
    if search_by_field:
        st.session_state["mode"] = "field"
    elif search_by_object:
        st.session_state["mode"] = "object"

    # Conditionally render inputs in main area
    mode = st.session_state.get("mode")

    if mode == "field":
        table = st.text_input("Enter Salesforce Object name (e.g., Contact)")
        field = st.text_input("Enter field name (e.g., EDS_Primary_Affiliation__c)")
        if table and field:
            searchByFieldName(r, table, field)
        else:
            st.info("Please enter both table and field names.")

    elif mode == "object":
        obj = st.text_input("Enter Salesforce Object name (e.g., Account)")
        if obj:
            searchByObject(r, obj)
        else:
            st.info("Please enter the object name.")

# Render login or app
if not st.session_state.logged_in:
    login()
else:
    main_app()