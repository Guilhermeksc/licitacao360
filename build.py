import subprocess
from diretorios import *
import os
def build_executable():
    # Caminho para o script principal
    main_script = "home.py"
    
    # Recursos para adicionar
    resources = [
        (DATABASE_DIR, "database"),
        (ICONS_DIR, "database/icons"),
        (IMAGE_PATH, "database/image"),
        # (PDF_DIR, "database/pasta_pdf"),
        # (SICAF_DIR, "database/pasta_sicaf"),
        (PASTA_TEMPLATE, "database/template"),
        # (SICAF_TXT_DIR, "database/pasta_sicaf/sicaf_txt"),
        # (TXT_DIR, "database/pasta_pdf/homolog_txt"),
        (RELATORIO_PATH, "database"),
        (LV_FINAL_DIR, "database/Nova pasta"),
        (LV_BASE_DIR, "database/Nova pasta"),
        (WEBDRIVER_DIR, "database/selenium"),
        (TEMPLATE_DIR, "database/template"),
        (CP_DIR, "database/template/comunicacao_padronizada"),
        (GERAR_RELATORIO_DIR, "database/template/relatorio_controle_pregao"),
        (CONTROLE_CONTRATOS_DIR, "controle_contratos"),
        (DATABASE_CONTRATOS, "controle_contratos/data_contratos"),
        (CP_CONTRATOS_DIR, "controle_contratos/comunicacao_padronizada")
    ]


    pyinstaller_args = [
        "pyinstaller",
        "--noconfirm",
        # "--windowed",
        # Se necessário, descomente a linha abaixo e ajuste o caminho para o ícone do seu aplicativo
        # "--icon=seu_icone.ico",
    ]

   # Adicionando importações ocultas
    pyinstaller_args.extend(["--hidden-import", "PyQt6"])
    pyinstaller_args.extend(["--hidden-import", "qdarkstyle"])
    pyinstaller_args.extend(["--hidden-import", "pdfplumber"])
    pyinstaller_args.extend(["--hidden-import", "openpyxl"])


    # Adicionando recursos com o separador correto
    for src, dest in resources:
        # Aqui é verificado se 'src' é uma instância de Path, e caso seja, é convertido para string
        src_str = str(src) if isinstance(src, Path) else src
        data_string = f"{src_str};{dest}" if os.name == 'nt' else f"{src_str}:{dest}"
        pyinstaller_args.extend(["--add-data", data_string])

    pyinstaller_args.append(main_script)

    subprocess.run(pyinstaller_args)

if __name__ == "__main__":
    build_executable()