import pandas as pd
import numpy as np
from datetime import timedelta

# ==========================================
# ⚙️ CONFIGURAÇÕES INICIAIS
# ==========================================
FERIADOS_TRINDADE = [
    '2026-01-01', '2026-04-21', '2026-05-01', 
]

def converter_hora_para_decimal(hora_texto):
    try:
        h, m, s = str(hora_texto).split(':')
        return int(h) + (int(m) / 60) + (int(s) / 3600)
    except:
        return np.nan

def aplicar_guilhotina_20_porcento(df, coluna_base):
    """Filtra anomalias baseado em uma coluna numérica"""
    if coluna_base not in df.columns: return df
    
    # Faz uma cópia limpa da coluna para fazer a conta
    df['Temp_Calculo'] = pd.to_numeric(df[coluna_base].astype(str).str.replace(',', '.'), errors='coerce')
    
    limites = df.groupby('Setor')['Temp_Calculo'].agg(['mean']).reset_index()
    limites['Piso'] = limites['mean'] * 0.80
    limites['Teto'] = limites['mean'] * 1.20
    
    df = df.merge(limites[['Setor', 'Piso', 'Teto']], on='Setor', how='left')
    
    # Mantém apenas as linhas que estão dentro da margem de 20%
    filtro = (df['Temp_Calculo'] >= df['Piso']) & (df['Temp_Calculo'] <= df['Teto'])
    
    df_limpo = df[filtro].copy()
    df_limpo = df_limpo.drop(columns=['Piso', 'Teto', 'Temp_Calculo'])
    
    return df_limpo

# ==========================================
# 🚀 O MOTOR DE FAXINA (MANTENDO O HISTÓRICO)
# ==========================================
def processar_inlog(caminho_bruto, caminho_saida):
    print("⏳ 1. Extraindo dados do Inlog...")
    try:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', skiprows=2)
    except:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='latin1', skiprows=2)

    df.columns = df.columns.str.strip()
        
    print("🧹 2. Limpeza Básica de Setores...")
    df = df.dropna(subset=['Setor'])
    df = df[df['Setor'] != 'GARAGEM']
    df['Setor'] = df['Setor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(4)

    print("📅 3. Aplicando Filtro de Feriados...")
    if 'Data Execucao' in df.columns:
        df['Data Temp'] = pd.to_datetime(df['Data Execucao'], format='%d/%m/%Y', errors='coerce') 
        df = df.dropna(subset=['Data Temp'])
        
        datas_proibidas = set()
        for feriado in FERIADOS_TRINDADE:
            f_date = pd.to_datetime(feriado)
            datas_proibidas.add(f_date)
            datas_proibidas.add(f_date - timedelta(days=1))
            datas_proibidas.add(f_date + timedelta(days=1))
        
        df = df[~df['Data Temp'].isin(datas_proibidas)]
        df = df.drop(columns=['Data Temp'])

    print("🪓 4. Guilhotina de 20% (Limpando Anomalias)...")
    # Limpa as principais métricas sem agrupar a tabela
    if 'Toneladas' in df.columns:
        df = aplicar_guilhotina_20_porcento(df, 'Toneladas')
    
    if 'Km Total' in df.columns:
        df = aplicar_guilhotina_20_porcento(df, 'Km Total')

    print(f"✅ SUCESSO! Base limpa e com histórico mantido salva em: {caminho_saida}")
    
    # Salva exatamente do jeito que o Streamlit ama ler
    df.to_excel(caminho_saida, index=False)
    
    return df

# ==========================================
if __name__ == "__main__":
    processar_inlog("base_td_bruta.csv", "dados_coleta.xlsx")