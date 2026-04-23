import pandas as pd
import numpy as np
from datetime import timedelta

from config_loader import get_feriados, get_setores_noturnos

DIAS_SEMANA_PT = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
    3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
}

# ==========================================
# 🚀 O MOTOR DE FAXINA (SEM GUILHOTINA)
# ==========================================
def processar_inlog(caminho_bruto: str, caminho_saida: str) -> pd.DataFrame:
    print("⏳ 1. Extraindo dados do Inlog...")

    if caminho_bruto.lower().endswith('.csv'):
        try:
            df = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', skiprows=2)
        except Exception:
            df = pd.read_csv(caminho_bruto, sep=';', encoding='latin1', skiprows=2)
    else:
        df = pd.read_excel(caminho_bruto, skiprows=2)

    df.columns = df.columns.astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()

    print("📅 2. Leitor Universal de Datas...")
    if 'Data Execucao' in df.columns:
        df['Data_Calendario'] = pd.to_datetime(df['Data Execucao'], format='mixed', dayfirst=True, errors='coerce')
        df.loc[df['Data_Calendario'].notna(), 'Dia da Semana'] = df['Data_Calendario'].dt.dayofweek.map(DIAS_SEMANA_PT)

    print("🧹 3. Correção de Turnos (Ignorando erros do Inlog)...")
    setores_noturnos = get_setores_noturnos()
    if 'Setor' in df.columns:
        df = df.dropna(subset=['Setor'])
        df = df[df['Setor'].astype(str).str.strip().str.upper() != 'GARAGEM']
        df['Setor'] = df['Setor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(4)

        if 'Turno' in df.columns:
            df.loc[df['Setor'].isin(setores_noturnos), 'Turno'] = 'NOTURNO'
            df.loc[df['Setor'] == '3000', 'Turno'] = 'DIURNO'

    print("🚫 4. Aplicando Filtro de Feriados...")
    if 'Data_Calendario' in df.columns:
        feriados = get_feriados()
        datas_proibidas = set()
        for feriado in feriados:
            f_date = pd.to_datetime(feriado)
            datas_proibidas.add(f_date)
            datas_proibidas.add(f_date - timedelta(days=1))
            datas_proibidas.add(f_date + timedelta(days=1))

        df = df[~df['Data_Calendario'].isin(datas_proibidas)]
        df = df.drop(columns=['Data_Calendario'])

    print("🪓 5. Filtro de Viagens Reais (Eliminando viagens zeradas do Inlog)...")
    for col in ['Toneladas', 'Km Total']:
        if col in df.columns:
            temp_col = col + "_temp_calc"
            df[temp_col] = df[col].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
            df = df[(df[temp_col] > 0) | (df[temp_col].isna())]
            df = df.drop(columns=[temp_col])

    print(f"✅ SUCESSO! Base limpa salva em: {caminho_saida}")
    df.to_excel(caminho_saida, index=False)

    return df

if __name__ == "__main__":
    processar_inlog("base_td_bruta.csv", "dados_coleta.xlsx")
