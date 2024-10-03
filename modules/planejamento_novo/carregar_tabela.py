from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
import pandas as pd
import sqlite3

class CarregarTabelaDialog(QDialog):
    def __init__(self, database_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Carregar Tabela e Gerenciar Database")
        self.database_manager = database_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Botão para carregar a tabela
        btn_carregar_tabela = QPushButton("Carregar Tabela")
        btn_carregar_tabela.clicked.connect(self.carregar_tabela)
        layout.addWidget(btn_carregar_tabela)

        # Botão para excluir o database
        btn_excluir_database = QPushButton("Excluir Database")
        btn_excluir_database.clicked.connect(self.excluir_tabela)
        layout.addWidget(btn_excluir_database)

        # Botão de fechar
        btn_close = QPushButton("Fechar")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

    def carregar_tabela(self):
        # Abre um diálogo para selecionar o arquivo Excel
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecione a tabela Excel", "", "Excel Files (*.xlsx)")
        
        if not file_path:
            return  # Se o usuário cancelar, saia da função

        # Carrega o DataFrame do arquivo Excel
        df = pd.read_excel(file_path)

        # Verifica se os campos obrigatórios estão presentes
        campos_obrigatorios = ["tipo", "numero", "ano", "objeto", "uasg"]
        for campo in campos_obrigatorios:
            if campo not in df.columns:
                QMessageBox.warning(self, "Erro", f"O campo obrigatório '{campo}' não foi encontrado no arquivo Excel.")
                return

        # Preparar uma lista de dados para inserção em massa
        itens_para_inserir = []
        id_processos = []

        for index, row in df.iterrows():
            # Prepara o item_data com os valores necessários
            item_data = {
                'tipo': row['tipo'],
                'numero': f"{int(row['numero']):02}",
                'ano': row['ano'],
                'objeto': row['objeto'],
                'objeto_completo': row.get('objeto_completo', None),
                'sigla_om': row.get('sigla_om', None),
                'material_servico': row.get('material_servico', None),
                'id_processo': f"{row['tipo']} {int(row['numero']):02}/{row['ano']}",
                'nup': row.get('nup', None),
                'orgao_responsavel': row.get('orgao_responsavel', None),
                'uasg': row['uasg'],
                'status': row.get('status', '-'),
                'pregoeiro': row.get('pregoeiro', '-'),
                'coordenador_planejamento': row.get('coordenador_planejamento', '-'),
                'setor_responsavel': row.get('setor_responsavel', '-'),
                'data_sessao': row.get('data_sessao', None),
                'srp': row.get('srp', None),
                'msg_irp': row.get('msg_irp', None),
                'data_limite_manifestacao_irp': row.get('data_limite_manifestacao_irp', None),
                'data_limite_confirmacao_irp': row.get('data_limite_confirmacao_irp', None),
                'num_irp': row.get('num_irp', None),
                'valor_total': row.get('valor_total', None),
                'comentarios': row.get('comentarios', None),
            }

            # Adiciona o item à lista de itens para inserção
            itens_para_inserir.append(item_data)
            id_processos.append(item_data['id_processo'])

        # Desabilita atualizações na interface enquanto processa os itens
        self.parent().model.layoutAboutToBeChanged.emit()

        try:
            # Inserir todos os itens no banco de dados
            for item_data in itens_para_inserir:
                print(f"Processando id_processo: {item_data['id_processo']}")
                self.parent().save_to_database(item_data)

            # Inserir todos os id_processo no controle_prazos de uma vez
            self.parent().save_to_control_prazos_batch(id_processos)

            # Recriar o modelo e notificar a interface gráfica que o layout foi alterado
            self.parent().initialize_ui()
        finally:
            # Reabilita as atualizações na interface
            self.parent().model.layoutChanged.emit()

        QMessageBox.information(self, "Carregamento Completo", "Os dados foram carregados e salvos no banco de dados com sucesso.")

    def prepare_context(self, row):
        """
        Prepara o valor de id_processo e o valor para a coluna etapa.
        
        Args:
        row (pandas.Series): Uma linha do DataFrame contendo os dados do processo.

        Returns:
        tuple: Retorna uma tupla contendo (id_processo, etapa).
        """
        # Formata o valor de 'numero' para ter duas casas decimais
        numero_formatado = f"{int(row['numero']):02}"
        id_processo = f"{row['tipo']} {numero_formatado}/{row['ano']}"
        etapa = f"{row['status']}"
        return id_processo, etapa


    def excluir_tabela(self):
        reply = QMessageBox.question(self, "Confirmação", "Tem certeza que deseja excluir os registros e as tabelas 'controle_processos' e 'controle_prazos'?", 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                    QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.database_manager as conn:
                    cursor = conn.cursor()
                    
                    # Remover todos os registros de controle_processos
                    cursor.execute("DELETE FROM controle_processos")
                    # Remover todos os registros de controle_prazos
                    cursor.execute("DELETE FROM controle_prazos")
                    conn.commit()
                    
                    # Tentar excluir as tabelas controle_processos e controle_prazos
                    cursor.execute("DROP TABLE IF EXISTS controle_processos")
                    cursor.execute("DROP TABLE IF EXISTS controle_prazos")
                    conn.commit()

                    # Atualiza o modelo da UI se necessário
                    if self.parent().model:
                        self.parent().model.clear()  # Limpa o modelo, já que a tabela foi excluída
                        self.parent().ui_manager.table_view.viewport().update()
                    
                    QMessageBox.information(self, "Sucesso", "Os registros e as tabelas 'controle_processos' e 'controle_prazos' foram excluídos com sucesso.")
            except sqlite3.Error as e:
                print(f"Erro ao tentar excluir os registros e tabelas: {e}")
                QMessageBox.warning(self, "Erro", f"Não foi possível excluir os registros e/ou tabelas: {e}")
