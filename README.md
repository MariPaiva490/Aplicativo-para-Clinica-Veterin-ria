🐾 Sistema Cantinho Animal - Gestão de Vacinas
O Sistema Cantinho Animal é uma aplicação desktop desenvolvida em Python para auxiliar clínicas veterinárias e pet shops no controle de vacinação de animais. O software permite cadastrar pets, gerenciar datas de vencimento de vacinas e facilitar a comunicação com os clientes via WhatsApp.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.x

Interface Gráfica: customtkinter (interface moderna e responsiva)

Banco de Dados: SQLite3 (banco de dados local leve e integrado)

Outras Bibliotecas: webbrowser (links externos), shutil (backups), tkinter (diálogos de sistema).

🚀 Funcionalidades Principais
1. Cadastro de Pets e Vacinas
No painel esquerdo, você pode realizar o registro completo:

Campos: Nome do Dono, Nome do Pet, Telefone (com DDD) e a primeira vacina com data de vencimento.

Auto-formatação: O campo de data formata automaticamente enquanto você digita (DD/MM/AAAA).

2. Edição e Correção de Dados (Novo!)
Caso tenha digitado um nome ou telefone errado:

Como usar: Dê dois cliques sobre o registro do pet na tabela principal.

Ação: Os dados serão carregados nos campos de entrada. Após corrigir, clique no botão "Atualizar Dados Editados" para salvar as mudanças no banco de dados.

3. Sistema de Alertas Inteligentes
Ao iniciar o programa, o sistema varre o banco de dados e exibe uma janela de alerta:

🔴 Bolinha Vermelha: Vacinas que já passaram da data de vencimento.

🟡 Bolinha Amarela: Vacinas que vencem nos próximos 7 dias.

4. Integração com WhatsApp
Facilita o agendamento e o aviso aos clientes:

Selecione um pet na lista e clique em "Enviar WhatsApp".

O sistema gera automaticamente uma mensagem personalizada. Se o pet tiver vacinas vencendo, a mensagem listará quais são elas. Caso contrário, envia uma mensagem de cortesia.

5. Pesquisa em Tempo Real
A barra de busca acima da tabela permite localizar rapidamente um cliente ou um pet pelo nome, filtrando os resultados instantaneamente conforme você digita.

6. Segurança e Backup
Excluir Pet: Remove o pet e todo o histórico de vacinas dele (com confirmação de segurança).

Backup: O botão "Fazer Backup" permite salvar uma cópia completa do seu banco de dados em um local seguro (pendrive, nuvem, etc.), evitando perda de informações.
