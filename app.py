import streamlit as st
import pandas as pd
from datetime import date
from database import init_db, query_df, execute, rows
from calculations import with_distance_consumption, eur

st.set_page_config(page_title="AutoControl", page_icon="🚘", layout="wide")

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #101914; }
[data-testid="stSidebar"] { background: #14221a; border-right: 1px solid #263b2e; }
h1,h2,h3 { color: #e8f3ec; }
[data-testid="stMetric"] { background:#18271e; border:1px solid #294333; padding:16px; border-radius:14px; }
.stButton>button, .stDownloadButton>button { background:#168653; color:white; border:0; border-radius:9px; }
.stButton>button:hover, .stDownloadButton>button:hover { background:#35b779; color:#07130c; }
div[data-baseweb="tab-list"] button[aria-selected="true"] { color:#35b779; }
</style>
""", unsafe_allow_html=True)

st.title("🚘 AutoControl")
st.caption("Gestão automóvel • Dados numa base Turso nova e independente")

try:
    init_db()
except Exception as e:
    st.error(f"Não foi possível ligar à base de dados: {e}")
    st.info("Configura os Secrets do Turso antes de utilizar a aplicação. Consulta README.md.")
    st.stop()

def vehicles_df():
    return query_df("SELECT * FROM vehicles ORDER BY status, name")

def vehicle_selector(df, key="vehicle"):
    if df.empty:
        st.warning("Ainda não existem veículos. Adiciona primeiro um veículo no módulo Veículos.")
        return None
    labels = {f'{r["name"]} · {r["fuel_type"]} · ID {r["id"]}': int(r["id"]) for _,r in df.iterrows()}
    label = st.selectbox("Veículo", list(labels), key=key)
    return labels[label]

def add_vehicle():
    st.subheader("Adicionar veículo")
    with st.form("new_vehicle"):
        c1,c2 = st.columns(2)
        name = c1.text_input("Nome / designação *", placeholder="BYD Dolphin Comfort")
        brand = c2.text_input("Marca", placeholder="BYD")
        model = c1.text_input("Modelo", placeholder="Dolphin Comfort")
        plate = c2.text_input("Matrícula")
        fuel = c1.selectbox("Tipo", ["Elétrico","Gasolina","Gasóleo","Híbrido","Híbrido plug-in","Outro"])
        year = c2.number_input("Ano", 1950, 2100, 2024)
        c3,c4 = st.columns(2)
        battery = c3.number_input("Capacidade bateria (kWh)", min_value=0.0, value=60.4 if fuel=="Elétrico" else 0.0, step=0.1)
        wltp = c4.number_input("Autonomia WLTP (km)", min_value=0.0, value=420.0 if fuel=="Elétrico" else 0.0, step=1.0)
        purchase_date = st.date_input("Data de aquisição", value=date.today())
        purchase_km = st.number_input("Quilometragem na aquisição", min_value=0, step=1)
        notes = st.text_area("Notas")
        ok = st.form_submit_button("Guardar veículo")
    if ok:
        if not name.strip():
            st.error("Indica pelo menos o nome do veículo.")
        else:
            execute("""INSERT INTO vehicles(name,brand,model,year,plate,fuel_type,battery_kwh,wltp_km,purchase_date,purchase_km,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(name.strip(),brand,model,int(year),plate,fuel,battery,wltp,str(purchase_date),int(purchase_km),notes))
            st.success("Veículo criado.")
            st.rerun()

menu = st.sidebar.radio("Navegação", ["Dashboard","Veículos","Carregamentos","Abastecimentos","Despesas","Manutenção","Viagens","Documentos","Importar / Exportar"])
st.sidebar.caption("AutoControl · versão inicial")

vdf = vehicles_df()

if menu == "Dashboard":
    st.header("Visão geral")
    if vdf.empty:
        st.info("Começa por adicionar o teu primeiro veículo.")
        add_vehicle()
    else:
        charge = query_df("SELECT * FROM charging")
        fuel = query_df("SELECT * FROM fuelings")
        exp = query_df("SELECT * FROM expenses")
        maint = query_df("SELECT * FROM maintenance")
        total_cost = (charge["total_cost"].sum() if not charge.empty else 0) + (fuel["total_cost"].sum() if not fuel.empty else 0) + (exp["amount"].sum() if not exp.empty else 0) + (maint["amount"].sum() if not maint.empty else 0)
        total_kwh = charge["kwh"].sum() if not charge.empty else 0
        total_l = fuel["litres"].sum() if not fuel.empty else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Veículos", len(vdf))
        c2.metric("Custos registados", eur(total_cost))
        c3.metric("Energia carregada", f"{total_kwh:.1f} kWh")
        c4.metric("Combustível", f"{total_l:.1f} L")
        st.subheader("Veículos")
        st.dataframe(vdf[["name","brand","model","plate","fuel_type","status"]], use_container_width=True, hide_index=True)
        if not charge.empty or not fuel.empty:
            st.subheader("Evolução de custos mensais")
            frames=[]
            for d,col,label in [(charge,"total_cost","Carregamentos"),(fuel,"total_cost","Abastecimentos"),(exp,"amount","Despesas"),(maint,"amount","Manutenção")]:
                if not d.empty:
                    x=d.copy(); x["Mês"]=pd.to_datetime(x["event_date"]).dt.to_period("M").astype(str); x=x.groupby("Mês")[col].sum().rename(label); frames.append(x)
            if frames: st.line_chart(pd.concat(frames,axis=1).fillna(0))
        st.caption("Os quilómetros e consumos só são calculados quando existe uma sequência cronológica válida de odómetros. Não se estima distância a partir de energia carregada.")

elif menu == "Veículos":
    st.header("Garagem")
    add_vehicle()
    st.divider()
    if not vdf.empty:
        st.dataframe(vdf, use_container_width=True, hide_index=True)
        with st.expander("Alterar estado de um veículo"):
            vid=vehicle_selector(vdf,"status_vehicle")
            status=st.selectbox("Estado",["Atual","Vendido","Desativado"])
            if st.button("Atualizar estado"): execute("UPDATE vehicles SET status=? WHERE id=?",(status,vid)); st.success("Estado atualizado."); st.rerun()

elif menu in ["Carregamentos","Abastecimentos"]:
    is_ev = menu == "Carregamentos"
    st.header(menu)
    vid=vehicle_selector(vdf, f"{menu}_vehicle")
    if vid:
        with st.form(f"new_{menu}"):
            d=st.date_input("Data",value=date.today())
            od=st.number_input("Quilometragem (km)",min_value=0,step=1,value=0)
            if is_ev:
                soc1=st.number_input("SoC inicial (%)",0,100,20)
                soc2=st.number_input("SoC final (%)",0,100,80)
                kwh=st.number_input("Energia carregada (kWh)",min_value=0.0,step=0.1)
                price=st.number_input("Preço (€/kWh)",min_value=0.0,step=0.001,format="%.3f")
                cost=st.number_input("Custo total (€)",min_value=0.0,step=0.01,value=round(kwh*price,2))
                place=st.text_input("Local / operador")
                note=st.text_area("Notas")
            else:
                litres=st.number_input("Litros",min_value=0.0,step=0.1)
                price=st.number_input("Preço (€/L)",min_value=0.0,step=0.001,format="%.3f")
                cost=st.number_input("Custo total (€)",min_value=0.0,step=0.01,value=round(litres*price,2))
                full=st.checkbox("Depósito cheio")
                place=st.text_input("Posto")
                note=st.text_area("Notas")
            ok=st.form_submit_button("Guardar registo")
        if ok:
            if is_ev:
                if soc2 < soc1: st.error("O SoC final não pode ser inferior ao inicial.")
                else:
                    execute("""INSERT INTO charging(vehicle_id,event_date,soc_start,soc_end,kwh,price_kwh,total_cost,odometer,location,provider,notes)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(vid,str(d),soc1,soc2,kwh,price,cost,int(od) if od else None,place,place,note))
                    st.success("Carregamento guardado."); st.rerun()
            else:
                execute("""INSERT INTO fuelings(vehicle_id,event_date,odometer,litres,price_litre,total_cost,full_tank,station,notes)
                VALUES(?,?,?,?,?,?,?,?,?)""",(vid,str(d),int(od) if od else None,litres,price,cost,int(full),place,note))
                st.success("Abastecimento guardado."); st.rerun()
    table = "charging" if is_ev else "fuelings"
    df=query_df(f"SELECT t.*,v.name AS vehicle_name FROM {table} t JOIN vehicles v ON v.id=t.vehicle_id ORDER BY event_date DESC,id DESC")
    if not df.empty:
        st.subheader("Histórico")
        st.dataframe(df,use_container_width=True,hide_index=True)
        csv=df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("Exportar histórico CSV",csv,f"{table}.csv","text/csv")

elif menu == "Despesas":
    st.header("Despesas")
    with st.form("expense"):
        vid=vehicle_selector(vdf,"expense_vehicle")
        d=st.date_input("Data",value=date.today())
        cat=st.selectbox("Categoria",["Seguro","IUC","Inspeção","Portagens","Estacionamento","Lavagem","Imposto","Outro"])
        desc=st.text_input("Descrição")
        amount=st.number_input("Valor (€)",min_value=0.0,step=0.01)
        od=st.number_input("Quilometragem (opcional)",min_value=0,step=1)
        recurring=st.checkbox("Despesa recorrente")
        note=st.text_area("Notas")
        ok=st.form_submit_button("Guardar despesa")
    if ok and vid:
        execute("INSERT INTO expenses(vehicle_id,event_date,category,description,amount,odometer,recurring,notes) VALUES(?,?,?,?,?,?,?,?)",(vid,str(d),cat,desc,amount,int(od) if od else None,int(recurring),note))
        st.success("Despesa guardada."); st.rerun()
    df=query_df("SELECT e.*,v.name AS vehicle_name FROM expenses e LEFT JOIN vehicles v ON v.id=e.vehicle_id ORDER BY event_date DESC")
    st.dataframe(df,use_container_width=True,hide_index=True)

elif menu == "Manutenção":
    st.header("Manutenção e alertas")
    vid=vehicle_selector(vdf,"maintenance_vehicle")
    if vid:
        with st.form("maintenance"):
            d=st.date_input("Data",value=date.today())
            cat=st.selectbox("Tipo",["Revisão","Pneus","Travões","Bateria","Reparação","Inspeção","Outro"])
            desc=st.text_input("Descrição")
            amount=st.number_input("Custo (€)",min_value=0.0,step=0.01)
            od=st.number_input("Quilometragem",min_value=0,step=1)
            next_date=st.date_input("Próxima data (opcional)",value=None)
            next_km=st.number_input("Próxima quilometragem (opcional)",min_value=0,step=100)
            workshop=st.text_input("Oficina")
            note=st.text_area("Notas")
            ok=st.form_submit_button("Guardar manutenção")
        if ok:
            execute("""INSERT INTO maintenance(vehicle_id,event_date,category,description,amount,odometer,next_date,next_odometer,workshop,notes)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",(vid,str(d),cat,desc,amount,int(od) if od else None,str(next_date) if next_date else None,int(next_km) if next_km else None,workshop,note))
            st.success("Manutenção guardada."); st.rerun()
    df=query_df("SELECT m.*,v.name AS vehicle_name FROM maintenance m JOIN vehicles v ON v.id=m.vehicle_id ORDER BY event_date DESC")
    st.dataframe(df,use_container_width=True,hide_index=True)

elif menu == "Viagens":
    st.header("Viagens")
    vid=vehicle_selector(vdf,"trip_vehicle")
    if vid:
        with st.form("trip"):
            d=st.date_input("Data de partida",value=date.today())
            end=st.date_input("Data de regresso (opcional)",value=None)
            origin=st.text_input("Origem")
            dest=st.text_input("Destino")
            km=st.number_input("Distância (km)",min_value=0.0,step=1.0)
            cost=st.number_input("Custo total (€)",min_value=0.0,step=0.01)
            note=st.text_area("Notas")
            ok=st.form_submit_button("Guardar viagem")
        if ok:
            execute("INSERT INTO trips(vehicle_id,start_date,end_date,origin,destination,distance_km,total_cost,notes) VALUES(?,?,?,?,?,?,?,?)",(vid,str(d),str(end) if end else None,origin,dest,km,cost,note))
            st.success("Viagem guardada."); st.rerun()
    df=query_df("SELECT t.*,v.name AS vehicle_name FROM trips t JOIN vehicles v ON v.id=t.vehicle_id ORDER BY start_date DESC")
    st.dataframe(df,use_container_width=True,hide_index=True)

elif menu == "Documentos":
    st.header("Documentos e validade")
    vid=vehicle_selector(vdf,"document_vehicle")
    with st.form("document"):
        title=st.text_input("Documento")
        cat=st.selectbox("Categoria",["Seguro","Inspeção","IUC","Registo","Garantia","Outro"])
        expiry=st.date_input("Validade (opcional)",value=None)
        note=st.text_area("Notas")
        ok=st.form_submit_button("Guardar documento")
    if ok and vid:
        execute("INSERT INTO documents(vehicle_id,title,category,expiry_date,notes) VALUES(?,?,?,?,?)",(vid,title,cat,str(expiry) if expiry else None,note))
        st.success("Documento registado."); st.rerun()
    df=query_df("SELECT d.*,v.name AS vehicle_name FROM documents d LEFT JOIN vehicles v ON v.id=d.vehicle_id ORDER BY expiry_date")
    st.dataframe(df,use_container_width=True,hide_index=True)

elif menu == "Importar / Exportar":
    st.header("Importar dados históricos")
    st.warning("A importação não apaga registos. Os ficheiros são analisados antes da gravação e os duplicados são sinalizados.")
    kind=st.selectbox("Tipo de dados",["Carregamentos","Abastecimentos"])
    upload=st.file_uploader("Seleciona um CSV",type=["csv"])
    if upload:
        try:
            raw=pd.read_csv(upload)
            st.write("Pré-visualização",raw.head(20))
            st.caption(f"{len(raw)} linhas encontradas. A importação automática será ativada após mapearmos os cabeçalhos do teu CSV original.")
            st.info("Nesta versão inicial, não importamos automaticamente para evitar associar colunas erradas ou duplicar registos.")
        except Exception as e: st.error(f"Não foi possível ler o CSV: {e}")
    st.divider()
    for table in ["vehicles","charging","fuelings","expenses","maintenance","trips","documents"]:
        df=query_df(f"SELECT * FROM {table}")
        st.download_button(f"Exportar {table} (CSV)",df.to_csv(index=False).encode("utf-8-sig"),f"{table}.csv","text/csv",key=f"export_{table}")
