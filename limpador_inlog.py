import pandas as pd
import numpy as np
from datetime import timedelta

# ==========================================
# ⚙️ CONFIGURAÇÕES INICIAIS
# ==========================================
FERIADOS_TRINDADE = [
    '2026-01-01', '2026-04-21', '2026-05-01', 
]

def aplicar_guilhotina_20_porcento(df, coluna_base):
    """Filtra as linhas com anomalias, preservando TODAS as colunas intactas"""
    if coluna_base not in df.columns: return df
    
    # Cria uma coluna temporária invisível só para fazer a conta matemática
    temp_col = coluna_base + "_temp_calc"
    df[temp_col] = pd.to_numeric(df[coluna_base].astype(str).str.replace(',', '.'), errors='coerce')
    
    # Calcula as médias por setor
    limites = df.groupby('Setor')[temp_col].agg(['mean']).reset_index()
    limites['Piso'] = limites['mean'] * 0.80
    limites['Teto'] = limites['mean'] * 1.20
    
    # Junta os limites na tabela principal
    df = df.merge(limites[['Setor', 'Piso', 'Teto']], on='Setor', how='left')
    
    # A MÁGICA: Mantém apenas as linhas que estão dentro da margem de segurança (ou vazias)
    filtro = ((df[temp_col] >= df['Piso']) & (df[temp_col] <= df['Teto'])) | (df[temp_col].isna())
    
    df_limpo = df[filtro].copy()
    
    # Apaga as colunas temporárias de cálculo para devolver a planilha original perfeita
    df_limpo = df_limpo.drop(columns=['Piso', 'Teto', temp_col])
    
    return df_limpo

# ==========================================
# 🚀 O MOTOR DE FAXINA (FILTRO DE LINHAS)
# ==========================================
def processar_inlog(caminho_bruto, caminho_saida):
    print("⏳ 1. Extraindo dados do Inlog...")
    try:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', skiprows=2)
    except:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='latin1', skiprows=2)

    # Limpa espaços em branco ocultos nos nomes das colunas
    df.columns = df.columns.str.strip()
        
    print("🧹 2. Limpeza Básica de Setores (Removendo GARAGEM)...")
    if 'Setor' in df.columns:
        df = df.dropna(subset=['Setor'])
        df = df[df['Setor'].astype(str).str.strip().str.upper() != 'GARAGEM']
        df['Setor'] = df['Setor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(4)

    print("📅 3. Aplicando Filtro de Feriados...")
    if 'Data Execucao' in df.columns:
        # Lê a data sem estragar a coluna original
        df['Data_Calculo_Temp'] = pd.to_datetime(df['Data Execucao'], format='%d/%m/%Y', errors='coerce') 
        
        datas_proibidas = set()
        for feriado in FERIADOS_TRINDADE:
            f_date = pd.to_datetime(feriado)
            datas_proibidas.add(f_date)
            datas_proibidas.add(f_date - timedelta(days=1))
            datas_proibidas.add(f_date + timedelta(days=1))
        
        # Elimina as linhas dos dias proibidos
        df = df[~df['Data_Calculo_Temp'].isin(datas_proibidas)]
        df = df.drop(columns=['Data_Calculo_Temp'])

    print("🪓 4. Guilhotina de 20% (Eliminando viagens anômalas)...")
    if 'Toneladas' in df.columns:
        df = aplicar_guilhotina_20_porcento(df, 'Toneladas')
    
    if 'Km Total' in df.columns:
        df = aplicar_guilhotina_20_porcento(df, 'Km Total')

    print(f"✅ SUCESSO! Base destilada salva em: {caminho_saida}")
    
    # Salva o arquivo em Excel mantendo absolutamente todas as colunas
    df.to_excel(caminho_saida, index=False)
    
    return df

# ==========================================
if __name__ == "__main__":
    processar_inlog("base_td_bruta.csv", "dados_coleta.xlsx")