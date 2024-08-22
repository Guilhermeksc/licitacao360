from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from modules.contratos.utils import WidgetHelper, Dialogs
from diretorios import *
from datetime import datetime
import tempfile
import pandas as pd
import sqlite3
import os
import logging
from modules.contratos.database_manager import DatabaseContratosManager, SqlModel

class GerenciarInclusaoExclusaoContratos(QDialog):
    def __init__(self, icons_dir, database_path, parent=None):
        super().__init__(parent)
        self.icons_dir = icons_dir
        self.database_path = database_path
        self.setWindowTitle("Gerenciar Inclusão/Exclusão de Contratos")
        self.resize(800, 600)
        self.database_manager = DatabaseContratosManager(self.database_path)
        self.init_ui()

        self.required_columns = [
            'status', 'dias', 'pode_renovar', 'custeio', 'numero_contrato', 'tipo', 'id_processo', 'empresa', 'objeto',
            'valor_global', 'uasg', 'nup', 'cnpj', 'natureza_continuada', 'om', 'indicativo_om', 'om_extenso', 'material_servico', 'link_pncp',
            'portaria', 'posto_gestor', 'gestor', 'posto_gestor_substituto', 'gestor_substituto', 'posto_fiscal',
            'fiscal', 'posto_fiscal_substituto', 'fiscal_substituto', 'posto_fiscal_administrativo', 'fiscal_administrativo',
            'vigencia_inicial', 'vigencia_final', 'setor', 'cp', 'msg', 'comentarios', 'registro_status','termo_aditivo', 'atualizacao_comprasnet',
            'instancia_governanca', 'comprasnet_contratos', 'assinatura_contrato', 'atualizacao_comprasnet'
        ]

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        # Adicionando os botões
        self.layout.addLayout(self.create_button_layout())

    def hide_unwanted_columns(self):
        # Função para ocultar colunas não desejadas
        for column in range(self.parent().model.columnCount()):
            if column not in [4, 7, 8, 9]:
                self.table_view.setColumnHidden(column, True)
            else:
                self.table_view.setColumnHidden(column, False)

    def create_button_layout(self):
        button_layout = QHBoxLayout()
        self.excluir_database_button = QPushButton("Excluir Database", self)
        self.excluir_database_button.clicked.connect(self.excluir_database)
        button_layout.addWidget(self.excluir_database_button)

        self.carregar_tabela_button = QPushButton("Carregar Tabela", self)
        self.carregar_tabela_button.clicked.connect(self.carregar_tabela)
        button_layout.addWidget(self.carregar_tabela_button)

        # Adicionando o botão "Sincronizar CSV"
        self.sincronizar_csv_button = QPushButton("Sincronizar CSV", self)
        self.sincronizar_csv_button.clicked.connect(self.sincronizar_csv)
        button_layout.addWidget(self.sincronizar_csv_button)

        return button_layout

    def sincronizar_csv(self):
        filepath = self.selecionar_csv()
        if not filepath:
            return
        
        df_csv = self.carregar_csv(filepath)
        if df_csv is None:
            return
        
        df_db = self.carregar_dados_bd()
        if df_db is None:
            return
        # Sincronizar os dados
        # self.verificar_correspondencias(df_csv, df_db)
        self.processar_e_atualizar_dados(df_csv, df_db)

    def selecionar_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo CSV", "", "CSV Files (*.csv)")
        return filepath

    def carregar_csv(self, filepath):
        try:
            df_csv = pd.read_csv(filepath)
            return df_csv
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir CSV", f"Não foi possível abrir o arquivo CSV: {str(e)}")
            return None

    def carregar_dados_bd(self):
        try:
            conn = sqlite3.connect(self.database_path)
            df_db = pd.read_sql_query("SELECT comprasnet_contratos FROM controle_contratos", conn)
            conn.close()
            return df_db
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar dados do banco", f"Erro ao carregar dados do banco de dados: {str(e)}")
            return None

    def verificar_correspondencias(self, df_csv, df_db):
        for _, row in df_csv.iterrows():
            numero_instrumento = row['Número do instrumento']
            if numero_instrumento in df_db['comprasnet_contratos'].values:
                print(f"Correspondente encontrado: {numero_instrumento}")
            else:
                print(f"Não encontrado: {numero_instrumento}")

    def excluir_database(self):
        try:
            self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
            print("Tabela 'controle_contratos' excluída com sucesso.")
        except Exception as e:
            print(f"Erro ao excluir a tabela: {str(e)}")

    def selecionar_csv(self):
        # Abrir diálogo para selecionar o arquivo CSV
        filepath, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo CSV", "", "CSV Files (*.csv)")
        return filepath

    def carregar_csv(self, filepath):
        # Ler o arquivo CSV
        try:
            df_csv = pd.read_csv(filepath)
            return df_csv
        except Exception as e:
            QMessageBox.warning(self, "Erro ao abrir CSV", f"Não foi possível abrir o arquivo CSV: {str(e)}")
            return None

    def carregar_dados_bd(self):
        # Abrir uma conexão com o banco de dados e carregar os dados em um DataFrame
        try:
            conn = sqlite3.connect(self.database_path)
            df_db = pd.read_sql_query("SELECT * FROM controle_contratos", conn)
            conn.close()
            return df_db
        except Exception as e:
            QMessageBox.warning(self, "Erro ao carregar dados do banco", f"Erro ao carregar dados do banco de dados: {str(e)}")
            return None

    def excluir_database(self):
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_contratos?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")

    def carregar_tabela(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Abrir arquivo de tabela", "", "Tabelas (*.xlsx *.xls *.ods *.csv)")
        if filepath:
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)
                
                # Validar e processar os dados
                self.validate_and_process_data(df)
                
                # Converter a coluna 'vigencia_final' para datetime para ordenação
                df['vigencia_final'] = pd.to_datetime(df['vigencia_final'], format='%d/%m/%Y')
                
                # Ordenar o DataFrame com base na coluna 'vigencia_final', da data mais distante para a mais próxima
                df = df.sort_values(by='vigencia_final', ascending=False)
                
                # Converter a coluna 'vigencia_final' de volta para o formato string DD/MM/AAAA
                df['vigencia_final'] = df['vigencia_final'].dt.strftime('%d/%m/%Y')
                
                df['status'] = 'Seção de Contratos'

                with self.database_manager as conn:
                    DatabaseContratosManager.create_table_controle_contratos(conn)

                # Exibir o DataFrame antes de salvar
                print("DataFrame antes de salvar no banco de dados:")
                print(df)

                # Salvar o DataFrame ordenado no banco de dados
                self.database_manager.save_dataframe(df, 'controle_contratos')

                # Exibir o DataFrame após salvar
                print("DataFrame após salvar no banco de dados (confirmando os dados salvos):")
                print(df)
                
                Dialogs.info(self, "Carregamento concluído", "Dados carregados e salvos com sucesso.")
            except Exception as e:
                logging.error("Erro ao carregar tabela: %s", e)
                Dialogs.warning(self, "Erro ao carregar", str(e))


    def validate_and_process_data(self, df):
        try:
            self.validate_columns(df)
            self.add_missing_columns(df)
            # self.salvar_detalhes_uasg_sigla_nome(df)
        except ValueError as e:
            Dialogs.warning(self, "Erro de Validação", str(e))
        except Exception as e:
            Dialogs.error(self, "Erro Inesperado", str(e))

    def validate_columns(self, df):
        # Verificar se todas as colunas necessárias estão presentes
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas obrigatórias faltando: {', '.join(missing_columns)}")

    def add_missing_columns(self, df):
        # Adicionar colunas ausentes com valores vazios
        for col in self.required_columns:
            if col not in df.columns:
                df[col] = ""

    # def salvar_detalhes_uasg_sigla_nome(self, df):
    #     # Exemplo de como preencher detalhes com base no UASG
    #     with sqlite3.connect(self.database_om_path) as conn:
    #         cursor = conn.cursor()
    #         cursor.execute("SELECT uasg, sigla_om, orgao_responsavel FROM controle_om")
    #         om_details = {row[0]: {'sigla_om': row[1], 'orgao_responsavel': row[2]} for row in cursor.fetchall()}
    #     df['sigla_om'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('sigla_om', ''))
    #     df['orgao_responsavel'] = df['uasg'].map(lambda x: om_details.get(x, {}).get('orgao_responsavel', ''))

    def processar_e_atualizar_dados(self, df_csv, df_db):
        # Certificar-se de que todas as colunas estão presentes
        required_columns = [
            'comprasnet_contratos', 'uasg', 'objeto', 'pode_renovar', 'id_processo', 'cnpj', 'empresa', 
            'numero_contrato', 'nup', 'vigencia_inicial', 'vigencia_final', 'valor_global', 'atualizacao_comprasnet'
        ]
        
        for col in required_columns:
            if col not in df_db.columns:
                df_db[col] = None  # Adicionar a coluna se estiver ausente

        # Lista para armazenar novas linhas
        new_rows = []

        # Iterar sobre cada linha do CSV para fazer a sincronização
        for index, row in df_csv.iterrows():
            numero_instrumento = row['Número do instrumento']
            
            # Ajustar o valor de 'Número Compra'
            numero_compra = row['Número Compra']
            parte_numerica, ano = numero_compra.split('/')
            parte_numerica = str(int(parte_numerica))  # Remove os zeros à esquerda
            id_processo = f"PE {parte_numerica.zfill(2)}/{ano}"  # Mantém duas casas decimais

            # Verificar se existe correspondência
            if df_db['comprasnet_contratos'].str.contains(numero_instrumento).any():

                # Atualizar o DataFrame com os novos valores
                uasg_value = row['Unidade Gestora Atual'].split(' - ')[0]
                fornecedor_info = row['Fornecedor']
                parts = fornecedor_info.split(' - ')
                if len(parts) >= 2:
                    cnpj = parts[0].strip()
                    empresa = ' - '.join(parts[1:]).strip()
                else:
                    cnpj = fornecedor_info.strip()
                    empresa = fornecedor_info.strip()

                numero_contrato = self.format_numero_contrato(numero_instrumento, uasg_value)
                nup = row['Processo']
                vigencia_inicial = row['Vig. Início']
                vigencia_final = row['Vig. Fim']
                valor_global = row['Valor Global']
                atualizacao_comprasnet = row['Atualizado em']
                objeto = row['Objeto']

                # Atualiza os valores na linha correspondente no DataFrame
                df_db.loc[df_db['comprasnet_contratos'] == numero_instrumento, [
                    'uasg', 'objeto', 'id_processo', 'cnpj', 'empresa', 'numero_contrato', 
                    'nup', 'vigencia_inicial', 'vigencia_final', 'valor_global', 'atualizacao_comprasnet'
                ]] = [
                    uasg_value, objeto, id_processo, cnpj, empresa, numero_contrato, 
                    nup, vigencia_inicial, vigencia_final, valor_global, atualizacao_comprasnet
                ]

            else:
                # Preparar os valores para inserção no DataFrame
                uasg_value = row['Unidade Gestora Atual'].split(' - ')[0]
                fornecedor_info = row['Fornecedor']
                parts = fornecedor_info.split(' - ')
                if len(parts) >= 2:
                    cnpj = parts[0].strip()
                    empresa = ' - '.join(parts[1:]).strip()
                else:
                    cnpj = fornecedor_info.strip()
                    empresa = fornecedor_info.strip()

                numero_contrato = self.format_numero_contrato(numero_instrumento, uasg_value)
                nup = row['Processo']
                vigencia_inicial = row['Vig. Início']
                vigencia_final = row['Vig. Fim']
                valor_global = row['Valor Global']
                atualizacao_comprasnet = row['Atualizado em']
                objeto = row['Objeto']

                # Criar a nova linha como um dicionário
                new_row = {
                    'comprasnet_contratos': numero_instrumento,
                    'uasg': uasg_value,
                    'objeto': objeto,
                    'id_processo': id_processo,
                    'cnpj': cnpj,
                    'empresa': empresa,
                    'numero_contrato': numero_contrato,
                    'nup': nup,
                    'vigencia_inicial': vigencia_inicial,
                    'vigencia_final': vigencia_final,
                    'valor_global': valor_global,
                    'atualizacao_comprasnet': atualizacao_comprasnet
                }

                # Adicionar a nova linha à lista de novas linhas
                new_rows.append(new_row)

        # Concatenar o DataFrame existente com as novas linhas
        if new_rows:
            df_new_rows = pd.DataFrame(new_rows)
            df_db = pd.concat([df_db, df_new_rows], ignore_index=True)
        
        # Gerar o arquivo Excel
        excel_path = os.path.join(os.getcwd(), 'dados_atualizados.xlsx')
        df_db.to_excel(excel_path, index=False)
        print(f"Arquivo Excel gerado: {excel_path}")
        
        # Abrir o arquivo Excel gerado
        os.startfile(excel_path)

        return df_db

    def atualizar_bd_com_arquivo(self, temp_file_path):
        try:
            print("Iniciando a função 'atualizar_bd_com_arquivo'")
            
            # Excluir a tabela existente 'controle_contratos'
            print("Excluindo a tabela 'controle_contratos'")
            self.excluir_database()

            # Garantir que a tabela foi excluída antes de continuar
            print("Conectado ao banco de dados")
            conn = sqlite3.connect(self.database_path, timeout=10)  # Aumentar o timeout para 10 segundos
            try:
                # Recriar a tabela controle_contratos
                print("Recriando a tabela 'controle_contratos'")
                DatabaseContratosManager.create_table_controle_contratos(conn)

                # Carregar o arquivo temporário para o DataFrame
                print(f"Carregando o arquivo temporário: {temp_file_path}")
                df_temp = pd.read_csv(temp_file_path)

                # Verificar duplicatas na coluna 'numero_contrato'
                print("Verificando duplicatas na coluna 'numero_contrato'")
                duplicatas = df_temp[df_temp.duplicated(subset=['numero_contrato'], keep=False)]
                if not duplicatas.empty:
                    print("Duplicatas encontradas no DataFrame:")
                    print(duplicatas[['numero_contrato']])
                else:
                    print("Nenhuma duplicata encontrada inicialmente.")

                # Remover duplicatas com base na coluna 'numero_contrato'
                print("Removendo duplicatas")
                df_temp = df_temp.drop_duplicates(subset=['numero_contrato'])

                # Verificar novamente se há duplicatas
                print("Verificando se ainda há duplicatas após a remoção")
                duplicatas_restantes = df_temp[df_temp.duplicated(subset=['numero_contrato'], keep=False)]
                if not duplicatas_restantes.empty:
                    print("Ainda há duplicatas após a remoção:")
                    print(duplicatas_restantes[['numero_contrato']])
                else:
                    print("Nenhuma duplicata restante após a remoção.")

                # Inserir ou atualizar os dados no banco de dados
                for index, row in df_temp.iterrows():
                    # Reabrir a conexão para cada iteração de inserção
                    conn = sqlite3.connect(self.database_path, timeout=10)

                    # Verificar se o número de contrato já existe
                    existing_data = pd.read_sql_query(
                        "SELECT * FROM controle_contratos WHERE numero_contrato = ?",
                        conn,
                        params=(row['numero_contrato'],)
                    )

                    if not existing_data.empty:
                        print(f"Atualizando o contrato existente: {row['numero_contrato']}")
                        # Atualizar o registro existente
                        df_temp.loc[index:index].to_sql('controle_contratos', conn, if_exists='replace', index=False)
                    else:
                        print(f"Inserindo novo contrato: {row['numero_contrato']}")
                        # Inserir novo registro
                        df_temp.loc[index:index].to_sql('controle_contratos', conn, if_exists='append', index=False)

                    conn.close()  # Fechar a conexão após cada operação para evitar bloqueios

                print("Tabela 'controle_contratos' atualizada com sucesso.")
            except sqlite3.OperationalError as e:
                print(f"Erro ao atualizar a tabela 'controle_contratos': {str(e)}")
                raise e
            except Exception as e:
                print(f"Erro inesperado ao atualizar a tabela: {str(e)}")
                raise e
            finally:
                if conn:
                    print("Fechando a conexão com o banco de dados")
                    conn.close()
        except sqlite3.OperationalError as e:
            print(f"Erro ao atualizar a tabela 'controle_contratos': {str(e)}")
            raise e
        except Exception as e:
            print(f"Erro inesperado ao atualizar a tabela: {str(e)}")
            raise e
        finally:
            # Garantir que a conexão seja fechada, caso ainda esteja aberta
            print("Fechando a conexão com o banco de dados")
            self.database_manager.close_connection()

    def format_numero_contrato(self, contrato, uasg):
        numero, ano = contrato.split('/')
        ano_formatado = ano[-2:]
        numero_formatado = numero.lstrip('0')  # Remove apenas os zeros à esquerda
        if len(numero_formatado) < 3:
            numero_formatado = numero_formatado.zfill(3)  # Garante que tenha pelo menos 3 dígitos
        numero_contrato = f'{uasg}/{ano_formatado}-{numero_formatado}/00'
        print(f"Original: {contrato} -> Formatado: {numero_contrato}")
        return numero_contrato