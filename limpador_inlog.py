import pandas as pd
import numpy as np
from datetime import timedelta

# ==========================================
# ⚙️ 1. CONFIGURAÇÕES INICIAIS (DE/PARA)
# ==========================================
DE_PARA_COLUNAS = {
    'Data Execucao': 'Data',
    'Setor': 'Setor', 
    'Turno': 'Turno',
    'Identificador': 'Placa',
    'Coletores': 'Qtd_Coletores',
    'Inicio': 'Hora_Inicio',
    'Fim': 'Hora_Fim',
    'Horas Trabalhadas': 'Horas_Trabalhadas_Texto',
    'Toneladas': 'Toneladas',
    'Km Total': 'Km_Total',
    'Km Improdutivo': 'Km_Improdutivo',
    'Km Produtivo': 'Km_Produtivo',
    'Combústivel': 'Combustível'
}

FERIADOS_TRINDADE = [
    '2026-01-01', 
    '2026-04-21', 
    '2026-05-01', 
]

MAPA_FREQUENCIA = {
    "2000": "Diária", "3000": "Diária",
    "2001": "Seg/Qua/Sex", "2002": "Seg/Qua/Sex", "2003": "Seg/Qua/Sex", "2004": "Seg/Qua/Sex",
    "3001": "Seg/Qua/Sex", "3002": "Seg/Qua/Sex", "3003": "Seg/Qua/Sex", "3004": "Seg/Qua/Sex", "3005": "Seg/Qua/Sex",
    "4001": "Ter/Qui/Sab", "4002": "Ter/Qui/Sab", "4003": "Ter/Qui/Sab", "4004": "Ter/Qui/Sab",
    "5001": "Ter/Qui/Sab", "5002": "Ter/Qui/Sab", "5003": "Ter/Qui/Sab", "5004": "Ter/Qui/Sab", "5005": "Ter/Qui/Sab"
}

# ==========================================
# 🛠️ 2. FUNÇÕES DE INTELIGÊNCIA
# ==========================================
def converter_hora_para_decimal(hora_texto):
    try:
        h, m, s = str(hora_texto).split(':')
        return int(h) + (int(m) / 60) + (int(s) / 3600)
    except:
        return np.nan

def aplicar_guilhotina_20_porcento(df, coluna):
    if coluna not in df.columns: return df
    
    limites = df.groupby('Setor')[coluna].agg(['mean']).reset_index()
    limites['Piso'] = limites['mean'] * 0.80
    limites['Teto'] = limites['mean'] * 1.20
    
    df = df.merge(limites[['Setor', 'Piso', 'Teto']], on='Setor', how='left')
    df.loc[(df[coluna] < df['Piso']) | (df[coluna] > df['Teto']), coluna] = np.nan
    df = df.drop(columns=['Piso', 'Teto'])
    
    return df.dropna(subset=[coluna])

# ==========================================
# 🚀 3. O MOTOR PRINCIPAL DE FAXINA
# ==========================================
def processar_inlog(caminho_bruto, caminho_saida):
    print("⏳ 1. Extraindo dados do Inlog...")
    try:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='utf-8', skiprows=2)
    except:
        df = pd.read_csv(caminho_bruto, sep=';', encoding='latin1', skiprows=2)

    df.columns = df.columns.str.strip()
    
    colunas_presentes = [col for col in DE_PARA_COLUNAS.keys() if col in df.columns]
    df = df[colunas_presentes]
    df = df.rename(columns=DE_PARA_COLUNAS)
        
    df = df.dropna(subset=['Setor'])
    df = df[df['Setor'] != 'GARAGEM']
    
    # Blindagem Extra: Remove casas decimais e espaços do número do setor
    df['Setor'] = df['Setor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.zfill(4)

    print("📅 2. Aplicando Filtro de Feriados e Picos...")
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce') 
    df = df.dropna(subset=['Data'])
    
    datas_proibidas = set()
    for feriado in FERIADOS_TRINDADE:
        f_date = pd.to_datetime(feriado)
        datas_proibidas.add(f_date)
        datas_proibidas.add(f_date - timedelta(days=1))
        datas_proibidas.add(f_date + timedelta(days=1))
    
    df = df[~df['Data'].isin(datas_proibidas)]

    df['Dia_Semana'] = df['Data'].dt.dayofweek
    df['Frequencia'] = df['Setor'].map(MAPA_FREQUENCIA)
    
    filtro_segunda = (df['Frequencia'].isin(['Diária', 'Seg/Qua/Sex'])) & (df['Dia_Semana'] == 0)
    filtro_terca = (df['Frequencia'] == 'Ter/Qui/Sab') & (df['Dia_Semana'] == 1)
    
    # O PARAQUEDAS: Tenta aplicar o filtro de pico. Se o arquivo ficar vazio, desativa o filtro!
    df_pico = df[filtro_segunda | filtro_terca]
    if not df_pico.empty:
        df = df_pico
    else:
        print("⚠️ AVISO: Nenhuma Segunda/Terça encontrada. Usando todos os dias disponíveis na base para não zerar.")

    print("⚖️ 3. Resgatando Pesos Vazios (Imputação Histórica)...")
    df['Toneladas'] = pd.to_numeric(df['Toneladas'].astype(str).str.replace(',', '.'), errors='coerce')
    df.loc[df['Toneladas'] <= 0, 'Toneladas'] = np.nan
    df['Toneladas'] = df['Toneladas'].fillna(df.groupby('Setor')['Toneladas'].transform('mean'))
    df = df.dropna(subset=['Toneladas'])

    # Se ainda estiver vazio aqui, encerra para não dar erro lá na frente
    if df.empty:
        raise ValueError("A base ficou completamente vazia após as limpezas de lixo. Verifique o arquivo bruto.")

    print("⏱️ 4. Peneira do Relógio (Horários de Contrato)...")
    df['Hora_Inicio_Dec'] = df['Hora_Inicio'].apply(converter_hora_para_decimal)
    df['Horas_Trabalhadas'] = df['Horas_Trabalhadas_Texto'].apply(converter_hora_para_decimal)
    df = aplicar_guilhotina_20_porcento(df, 'Hora_Inicio_Dec')

    print("🪓 5. Guilhotina de 20% (Limpando Anomalias)...")
    for col in ['Km_Produtivo', 'Km_Improdutivo', 'Km_Total', 'Combustível']:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df = aplicar_guilhotina_20_porcento(df, 'Toneladas')
    df = aplicar_guilhotina_20_porcento(df, 'Km_Total')
    df = aplicar_guilhotina_20_porcento(df, 'Combustível')
    df = aplicar_guilhotina_20_porcento(df, 'Horas_Trabalhadas')

    print("🧬 6. Agrupando o Dia Padrão Perfeito...")
    def calc_moda(x): return x.mode()[0] if not x.mode().empty else np.nan
    
    padrao_ouro = df.groupby('Setor').agg({
        'Toneladas': 'mean',
        'Km_Total': 'mean',
        'Km_Produtivo': 'mean',
        'Km_Improdutivo': 'mean',
        'Combustível': 'mean',
        'Horas_Trabalhadas': 'mean',
        'Placa': calc_moda,
        'Qtd_Coletores': calc_moda,
        'Data': 'count'
    }).rename(columns={'Data': 'Amostras_Validas'}).reset_index()

    padrao_ouro['Viagens'] = 1 
    padrao_ouro['Produtividade (t/h)'] = np.where(padrao_ouro['Horas_Trabalhadas'] > 0, padrao_ouro['Toneladas'] / padrao_ouro['Horas_Trabalhadas'], 0)

    cols_arredondar = ['Toneladas', 'Km_Total', 'Km_Produtivo', 'Km_Improdutivo', 'Combustível', 'Horas_Trabalhadas', 'Produtividade (t/h)']
    padrao_ouro[cols_arredondar] = padrao_ouro[cols_arredondar].round(2)

    print(f"✅ SUCESSO! Base destilada salva em: {caminho_saida}")
    padrao_ouro.to_excel(caminho_saida, index=False)
    
    return padrao_ouro

# ==========================================
# ▶️ EXECUTAR O ROBÔ
# ==========================================
if __name__ == "__main__":
    arquivo_inlog = "base_td_bruta.csv"
    arquivo_epico = "dados_coleta.xlsx"
    
    resultado = processar_inlog(arquivo_inlog, arquivo_epico)
    print("\n--- VISÃO GERAL DO PADRÃO OURO ---")
    print(resultado[['Setor', 'Toneladas', 'Horas_Trabalhadas', 'Amostras_Validas']].head(5))