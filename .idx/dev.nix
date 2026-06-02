# Arquivo de configuração do Google Project IDX para o EPICO
{ pkgs, ... }: {
  channel = "stable-24.05"; 
  
  # Instala o Python automaticamente na máquina virtual do Google
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
  ];

  idx = {
    # Instala a extensão oficial de Python no seu IDX de qualquer lugar
    extensions = [
      "ms-python.python"
    ];

    # Executado uma única vez quando o ambiente é criado
    onCreate = {
      install-dependencies = "pip install -r requirements.txt";
    };

    # Configura a janelinha de Preview (visualização) do Streamlit em tempo real
    previews = {
      enable = true;
      previews = {
        web = {
          command = ["streamlit" "run" "1_Visao_Executiva.py" "--server.port" "$PORT" "--server.address" "0.0.0.0"];
          manager = "web";
        };
      };
    };
  };
}
