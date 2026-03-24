import pandas as pd
import numpy as np
from datetime import timedelta

# ==========================================
# ⚙️ PAINEL DE CONTROLO (AJUSTE AQUI)
# ==========================================
MARGEM_ERRO = 0.10          # 0.10 = 10% de margem (Guilhotina a 10%)
MINIMO_VIAGENS_LIVRE = 3    # Setores com menos de 3 viagens não sofrem cortes (Passe Livre)

FERIADOS_TRINDADE = [
    '2026-01-01', '2026-04-21', '2026-05-01', 
]

# Dicionário inteligente para o robô calcular o dia correto
DIAS_SEMANA_PT = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
    3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
}

def aplicar_guilhotina(df, coluna_base):
    """Filtra anomalias com base na margem definida, mas poupa setores com poucos dados"""
    if coluna_base not in df.columns: return df
    
    temp_col = coluna_base + "_temp_calc"
    df[temp_col] = pd.to_numeric(df[coluna_base].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Calcula a média e conta quantas viagens o setor teve
    limites = df.groupby('Setor')[temp_col].agg(['mean', 'count']).reset_index()
    
    # Aplica os 10% (ou o valor que definir no Painel de Controlo)
    limites['Piso'] = limites['mean'] * (1 - MARGEM_ERRO)
    limites['Teto'] = limites['mean'] * (1 + MARGEM_ERRO)
    
    df = df.merge(limites[['Setor', 'Piso', 'Teto', 'count']], on='Setor', how='left')
    
    # A MÁGICA: Corta fora da margem, MAS dá Passe Livre a quem tem poucas viagens
    filtro = (
        (df['count'] < MINIMO_VIAGENS_LIVRE) | 
        ((df[temp_col] >= df['Piso']) & (df[temp_col] <= df['Teto'])) | 
        (df[temp_col].isna())
    )
    
    df_limpo = df[filtro].copy()
    df_limpo = df_limpo.drop(columns=['Piso', 'Teto', 'count', temp_col])
    
    return df_limpo

# ==========================================
# 🚀 O MOTOR DE FAXINA
# ==========================================
def processar_inlog(caminho_bruto, caminho_saida):
    print("⏳ 1. Extraindo dados do Inlog...")
    try:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', skiprows=2)
    except:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='latin1', skiprows=2)

    df.columns = df.columns.str.strip()
    
    print("📅 2. Recalculando o Dia da Semana pelo Calendário...")
    if 'Data Execucao' in df.columns:
        df['Data_Calendario'] = pd.to_datetime(df['Data Execucao'], format='%d/%m/%Y', errors='coerce') 
        df.loc[df['Data_Calendario'].notna(), 'Dia da Semana'] = df['Data_Calendario'].dt.dayofweek.map(DIAS_SEMANA_PT)
        
    print("🧹 3. Limpeza Básica de Setores...")
    if 'Setor' in df.columns:
        df = df.dropna(subset=['Setor'])
        df = df[df['Setor'].astype(str).str.strip().str.upper() != 'GARAGEM']
        df['Setor'] = df['Setor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(4)

    print("🚫 4. Aplicando Filtro de Feriados...")
    if 'Data_Calendario' in df.columns:
        datas_proibidas = set()
        for feriado in FERIADOS_TRINDADE:
            f_date = pd.to_datetime(feriado)
            datas_proibidas.add(f_date)
            datas_proibidas.add(f_date - timedelta(days=1))
            datas_proibidas.add(f_date + timedelta(days=1))
        
        df = df[~df['Data_Calendario'].isin(datas_proibidas)]
        df = df.drop(columns=['Data_Calendario'])

    print(f"🪓 5. Guilhotina de {int(MARGEM_ERRO*100)}% (Protegendo setores com menos de {MINIMO_VIAGENS_LIVRE} viagens)...")
    if 'Toneladas' in df.columns:
        df = aplicar_guilhotina(df, 'Toneladas')
    
    if 'Km Total' in df.columns:
        df = aplicar_guilhotina(df, 'Km Total')

    print(f"✅ SUCESSO! Base limpa salva em: {caminho_saida}")
    df.to_excel(caminho_saida, index=False)
    
    return df

if __name__ == "__main__":
    processar_inlog("base_td_bruta.csv", "dados_coleta.xlsx")
