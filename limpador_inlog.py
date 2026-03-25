import pandas as pd
import numpy as np
from datetime import timedelta

# ==========================================
# ⚙️ PAINEL DE CONTROLO (AJUSTE AQUI)
# ==========================================
MARGEM_ERRO = 0.40          # ALARGADO PARA 40% (Permite a variação natural dos dias)
MINIMO_VIAGENS_LIVRE = 5    # Setores com menos de 5 viagens não sofrem nenhum corte

FERIADOS_TRINDADE = [
    '2026-01-01', '2026-04-21', '2026-05-01', 
]

DIAS_SEMANA_PT = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
    3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
}

SETORES_NOTURNOS = ['3001', '3002', '3003', '3004', '3005', '5001', '5002', '5003', '5004', '5005']

def aplicar_guilhotina(df, coluna_base):
    if coluna_base not in df.columns: return df
    
    temp_col = coluna_base + "_temp_calc"
    
    # Blindagem extra para números brasileiros (remove ponto de milhar, troca vírgula por ponto)
    df[temp_col] = df[coluna_base].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
    
    limites = df.groupby('Setor')[temp_col].agg(['mean', 'count']).reset_index()
    limites['Piso'] = limites['mean'] * (1 - MARGEM_ERRO)
    limites['Teto'] = limites['mean'] * (1 + MARGEM_ERRO)
    
    df = df.merge(limites[['Setor', 'Piso', 'Teto', 'count']], on='Setor', how='left')
    
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

    df.columns = df.columns.astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
    
    print("📅 2. Leitor Universal de Datas...")
    if 'Data Execucao' in df.columns:
        df['Data_Calendario'] = pd.to_datetime(df['Data Execucao'], format='mixed', dayfirst=True, errors='coerce') 
        df.loc[df['Data_Calendario'].notna(), 'Dia da Semana'] = df['Data_Calendario'].dt.dayofweek.map(DIAS_SEMANA_PT)
        
    print("🧹 3. Correção de Turnos (Ignorando erros do Inlog)...")
    if 'Setor' in df.columns:
        df = df.dropna(subset=['Setor'])
        df = df[df['Setor'].astype(str).str.strip().str.upper() != 'GARAGEM']
        df['Setor'] = df['Setor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(4)
        
        if 'Turno' in df.columns:
            # 1. Garante que os setores noturnos sejam NOTURNO
            df.loc[df['Setor'].isin(SETORES_NOTURNOS), 'Turno'] = 'NOTURNO'
            
            # 2. Garante que o 3000 (e outros diários) sejam DIURNO, corrigindo o erro do sistema
            df.loc[df['Setor'] == '3000', 'Turno'] = 'DIURNO'

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

    print(f"🪓 5. Guilhotina Flexível de {int(MARGEM_ERRO*100)}%...")
    if 'Toneladas' in df.columns:
        df = aplicar_guilhotina(df, 'Toneladas')
    
    if 'Km Total' in df.columns:
        df = aplicar_guilhotina(df, 'Km Total')

    print(f"✅ SUCESSO! Base limpa salva em: {caminho_saida}")
    df.to_excel(caminho_saida, index=False)
    
    return df

if __name__ == "__main__":
    processar_inlog("base_td_bruta.csv", "dados_coleta.xlsx")
