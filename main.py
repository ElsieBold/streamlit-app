import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import re
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
def getJobs():
    st.text(table)
    target_field = f"{table}/{field}" if table and field else None
 
    if target_field:
        st.markdown(f"🔍 Searching for: `{target_field}`")
        r = getData()
    
        
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



st.sidebar.title('Boomi SF Mapping Search')

table = st.sidebar.text_input("Enter Salesforce Object name (e.g., Contact)")
field = st.sidebar.text_input("Enter field name (e.g., EDS_Primary_Affiliation__c)")


st.sidebar.button('Search',  on_click=getJobs, type="primary")
st.sidebar.button('Clear Cache', on_click=clear_cache)