


    def on_add_item(self):
        add_item_dialog = AddItemDialog(self)
        if add_item_dialog.exec() == QDialog.DialogCode.Accepted:
            item_data = add_item_dialog.get_data()
            item_data = self.completar_dados_adicionais(item_data)
            print("Dados do item a serem adicionados:", item_data)  # Print de depuração
            self.database_manager.save_to_database(item_data)
            self.refresh_model()

    def completar_dados_adicionais(self, item_data):
        # Define todas as outras colunas como None
        all_columns = [
            'status', 'dias', 'pode_renovar', 'custeio', 'numero_contrato', 'tipo', 'id_processo', 'empresa', 
            'objeto', 'valor_global', 'uasg', 'nup', 'cnpj', 'natureza_continuada', 'om', 'sigla_om', 
            'orgao_responsavel', 'material_servico', 'link_pncp', 'portaria', 'posto_gestor', 'gestor', 
            'posto_gestor_substituto', 'gestor_substituto', 'posto_fiscal', 'fiscal', 'posto_fiscal_substituto', 
            'fiscal_substituto', 'posto_fiscal_administrativo', 'fiscal_administrativo', 'vigencia_inicial', 
            'vigencia_final', 'setor', 'cp', 'msg', 'comentarios', 'termo_aditivo', 'atualizacao_comprasnet', 
            'instancia_governanca', 'comprasnet_contratos', 'registro_status'
        ]
        default_data = {col: None for col in all_columns}
        default_data.update(item_data)
        return default_data


    def excluir_database(self):
        reply = QMessageBox.question(self, 'Confirmar Exclusão', 'Tem certeza que deseja excluir a tabela controle_contratos?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.database_manager.execute_query("DROP TABLE IF EXISTS controle_contratos")
                QMessageBox.information(self, "Sucesso", "Tabela controle_contratos excluída com sucesso.")
                self.refresh_model()
            except Exception as e:
                QMessageBox.warning(self, "Erro ao excluir", f"Erro ao excluir a tabela: {str(e)}")
                