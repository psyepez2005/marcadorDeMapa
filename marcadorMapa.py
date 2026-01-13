import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide", page_title="Mapa Iniciativas STEM")

if 'puntos_manuales' not in st.session_state:
    st.session_state['puntos_manuales'] = []
if 'punto_temporal' not in st.session_state:
    st.session_state['punto_temporal'] = None
if 'mostrar_csv' not in st.session_state:
    st.session_state['mostrar_csv'] = True

def activar_vista_csv():
    st.session_state['mostrar_csv'] = True

with st.sidebar:
    st.title("Panel de Control")
    
    archivo = st.file_uploader("Cargar otro CSV", type=["csv"], on_change=activar_vista_csv)
    
    if st.session_state['punto_temporal']:
        st.divider()
        st.header("Nuevo Punto")
        lat_temp, lon_temp = st.session_state['punto_temporal']
        st.write(f"Coordenadas: `{lat_temp:.4f}, {lon_temp:.4f}`")
        
        with st.form("formulario_crear"):
            nombre_input = st.text_input("Nombre / Título")
            desc_input = st.text_area("Descripción")
            url_input = st.text_input("URL Web (http...)")
            logo_input = st.text_input("URL Logo (Imagen)")
            anio_input = st.text_input("Año de creación")
            
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
                        "url": url_input,
                        "logo": logo_input,
                        "anio": anio_input,
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
        st.info("Haz clic en el mapa para añadir un punto manualmente.")

    st.divider()
    if st.button("Borrar todos los puntos"):
        st.session_state['puntos_manuales'] = []
        st.session_state['punto_temporal'] = None
        st.session_state['mostrar_csv'] = False  
        st.rerun()

puntos_totales = []
df = None

if st.session_state['mostrar_csv']:
    if archivo:
        try:
            df = pd.read_csv(archivo, sep=";", encoding="utf-8")
        except:
            archivo.seek(0)
            df = pd.read_csv(archivo, sep=";", encoding="latin-1")
    elif os.path.exists("IniciativasSTEMParaImportar.csv"):
        try:
            df = pd.read_csv("IniciativasSTEMParaImportar.csv", sep=";", encoding="utf-8")
        except:
            df = pd.read_csv("IniciativasSTEMParaImportar.csv", sep=";", encoding="latin-1")

if df is not None:
    try:
        df.columns = [c.strip().upper() for c in df.columns]
        
        col_lat = next((c for c in df.columns if 'LAT' in c), None)
        col_lon = next((c for c in df.columns if 'LON' in c), None)
        col_nom = next((c for c in df.columns if 'NOM' in c), "NOMBRE")
        col_desc = next((c for c in df.columns if 'OBJ' in c or 'DESC' in c), None)
        col_url = next((c for c in df.columns if 'URL' in c or 'LINK' in c), None)
        col_logo = next((c for c in df.columns if 'LOGO' in c or 'IMG' in c), None)
        col_anio = next((c for c in df.columns if 'AÑO' in c or 'CREACION' in c), None)

        if col_lat and col_lon:
            for _, row in df.iterrows():
                try:
                    punto = {
                        "lat": float(str(row[col_lat]).replace(',', '.')),
                        "lon": float(str(row[col_lon]).replace(',', '.')),
                        "nombre": str(row[col_nom]),
                        "desc": str(row[col_desc]) if col_desc and pd.notna(row[col_desc]) else "",
                        "url": str(row[col_url]) if col_url and pd.notna(row[col_url]) else "",
                        "logo": str(row[col_logo]) if col_logo and pd.notna(row[col_logo]) else "",
                        "anio": str(row[col_anio]).replace('.0','') if col_anio and pd.notna(row[col_anio]) else "",
                        "tipo": "CSV"
                    }
                    puntos_totales.append(punto)
                except: 
                    continue
    except Exception as e:
        st.error(f"Error procesando estructura del CSV: {e}")

puntos_totales.extend(st.session_state['puntos_manuales'])

grupos = {}
for p in puntos_totales:
    c = (p['lat'], p['lon'])
    if c not in grupos: grupos[c] = []
    grupos[c].append(p)

m = folium.Map(location=[-1.8312, -78.1834], zoom_start=7)

for coord, lista in grupos.items():
    lat, lon = coord
    
    html = f'<div style="font-family:sans-serif; width:260px; max-height:300px; overflow-y:auto; padding-right:5px;">'
    
    hay_manual = False
    
    for i, p in enumerate(lista):
        if p.get('tipo') == 'Manual': hay_manual = True
        
        if i > 0: html += '<hr style="margin: 10px 0; border: 0; border-top: 1px solid #ccc;">'
        
        html += f'<div style="margin-bottom:5px;">'
        html += f'<h4 style="margin:0 0 5px 0; color:#333;">{p["nombre"]}</h4>'
        
        if p.get('logo') and p['logo'].startswith('http'):
            html += f'<img src="{p["logo"]}" style="width:100%; max-height:120px; object-fit:contain; margin-bottom:8px; border-radius:4px;">'
        
        if p.get('desc'):
            html += f'<p style="font-size:13px; color:#555; margin-bottom:5px;">{p["desc"]}</p>'
            
        if p.get('anio'):
            html += f'<p style="font-size:12px; margin:0 0 5px 0;"><b>Año:</b> {p["anio"]}</p>'
            
        if p.get('url') and p['url'].startswith('http'):
            html += f"""<div style="text-align:center;">
                        <a href="{p['url']}" target="_blank" 
                           style="background-color:#007bff; color:white; padding:6px 12px; text-decoration:none; border-radius:15px; font-size:12px; display:inline-block;">
                           Visitar Sitio Web
                        </a></div>"""
        
        html += '</div>'
        
    html += "</div>"
    
    color = "red" if hay_manual else "blue"
    
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(html, max_width=300),
        tooltip=f"{len(lista)} iniciativa(s) aquí",
        icon=folium.Icon(color=color, icon="info-sign")
    ).add_to(m)

if st.session_state['punto_temporal']:
    lat_t, lon_t = st.session_state['punto_temporal']
    folium.Marker([lat_t, lon_t], popup="Nuevo Punto", icon=folium.Icon(color="green", icon="plus")).add_to(m)

st.write("### Mapa de Iniciativas STEM en Ecuador")

mapa_out = st_folium(
    m, 
    width="100%", 
    height=600, 
    returned_objects=["last_clicked"] 
)

if mapa_out.get('last_clicked'):
    nuevo_lat = mapa_out['last_clicked']['lat']
    nuevo_lon = mapa_out['last_clicked']['lng']
    
    if st.session_state['punto_temporal'] is None or \
       abs(st.session_state['punto_temporal'][0] - nuevo_lat) > 0.00001:
        
        st.session_state['punto_temporal'] = (nuevo_lat, nuevo_lon)
        st.rerun()