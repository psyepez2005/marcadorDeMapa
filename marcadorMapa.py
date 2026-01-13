import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Mapa Iniciativas")

if 'puntos_manuales' not in st.session_state:
    st.session_state['puntos_manuales'] = []
if 'punto_temporal' not in st.session_state:
    st.session_state['punto_temporal'] = None

with st.sidebar:
    st.title("Panel de Control")
    archivo = st.file_uploader("Cargar CSV", type=["csv"])
    
    if st.session_state['punto_temporal']:
        st.divider()
        st.header("Nuevo Punto")
        lat_temp, lon_temp = st.session_state['punto_temporal']
        st.write(f"Coordenadas: `{lat_temp:.4f}, {lon_temp:.4f}`")
        
        with st.form("formulario_crear"):
            nombre_input = st.text_input("Nombre del lugar")
            desc_input = st.text_area("Descripción")
            
            col1, col2 = st.columns(2)
            guardar = col1.form_submit_button("Guardar", type="primary")
            cancelar = col2.form_submit_button("Cancelar")
            
            if guardar:
                if nombre_input:
                    st.session_state['puntos_manuales'].append({
                        "lat": lat_temp,
                        "lon": lon_temp,
                        "nombre": nombre_input,
                        "desc": desc_input,
                        "tipo": "Manual"
                    })
                    st.session_state['punto_temporal'] = None
                    st.success("Guardado")
                    st.rerun()
                else:
                    st.error("Falta el nombre")
            
            if cancelar:
                st.session_state['punto_temporal'] = None
                st.rerun()
    else:
        st.info("Haz clic en el mapa para añadir un punto.")

    st.divider()
    if st.button("Borrar todo"):
        st.session_state['puntos_manuales'] = []
        st.session_state['punto_temporal'] = None
        st.rerun()

puntos_totales = []

if archivo:
    try:
        try:
            df = pd.read_csv(archivo, sep=";", encoding="utf-8")
        except:
            archivo.seek(0)
            df = pd.read_csv(archivo, sep=";", encoding="latin-1")
            
        df.columns = [c.strip().upper() for c in df.columns]
        col_lat = next((c for c in df.columns if 'LAT' in c), None)
        col_lon = next((c for c in df.columns if 'LON' in c), None)
        col_nom = next((c for c in df.columns if 'NOM' in c), "NOMBRE")
        col_desc = next((c for c in df.columns if 'OBJ' in c or 'DESC' in c), None)

        if col_lat and col_lon:
            for _, row in df.iterrows():
                try:
                    puntos_totales.append({
                        "lat": float(str(row[col_lat]).replace(',', '.')),
                        "lon": float(str(row[col_lon]).replace(',', '.')),
                        "nombre": str(row[col_nom]),
                        "desc": str(row[col_desc]) if col_desc else "",
                        "tipo": "CSV"
                    })
                except: pass
    except Exception as e:
        st.error(f"Error CSV: {e}")

puntos_totales.extend(st.session_state['puntos_manuales'])

grupos = {}
for p in puntos_totales:
    c = (p['lat'], p['lon'])
    if c not in grupos: grupos[c] = []
    grupos[c].append(p)

m = folium.Map(location=[-1.8312, -78.1834], zoom_start=7)

for coord, lista in grupos.items():
    lat, lon = coord
    
    html = f'<div style="font-family:sans-serif; width:280px; max-height:250px; overflow-y:auto;">'
    hay_manual = False
    for i, p in enumerate(lista):
        if p['tipo'] == 'Manual': hay_manual = True
        html += f"""<div style="border-bottom:1px solid #ddd; margin-bottom:5px;">
        <b>{i+1}. {p['nombre']}</b><br><span style="font-size:12px; color:#555;">{p['desc']}</span></div>"""
    html += "</div>"
    
    color = "red" if hay_manual else "blue"
    
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(html, max_width=300),
        tooltip=f"{len(lista)} iniciativa(s) disponible(s)",
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

if st.session_state['punto_temporal']:
    lat_t, lon_t = st.session_state['punto_temporal']
    folium.Marker([lat_t, lon_t], popup="Nuevo", icon=folium.Icon(color="green", icon="plus")).add_to(m)

st.write("### Mapa de Iniciativas")

mapa_out = st_folium(
    m, 
    width="100%", 
    height=600, 
    returned_objects=["last_clicked"] 
)

if mapa_out.get('last_clicked'):
    nuevo_lat = mapa_out['last_clicked']['lat']
    nuevo_lon = mapa_out['last_clicked']['lng']
    
    if st.session_state['punto_temporal'] != (nuevo_lat, nuevo_lon):
        st.session_state['punto_temporal'] = (nuevo_lat, nuevo_lon)
        st.rerun()