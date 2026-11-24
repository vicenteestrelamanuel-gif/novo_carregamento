# AutoControl — versão inicial

Aplicação pessoal de gestão automóvel em Streamlit, com base de dados Turso independente.

## Incluído
- Dashboard inicial com indicadores e evolução mensal de custos.
- Gestão de veículos (atuais, vendidos e desativados).
- Registo de carregamentos, abastecimentos, despesas, manutenção, viagens e documentos.
- Exportação CSV das tabelas.
- Tema escuro com apontamentos verdes.
- Esquema de dados separado da aplicação antiga.

## Configuração local
1. Instalar Python 3.10 ou superior.
2. Criar ambiente virtual e instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Criar uma base de dados nova no Turso (não reutilizar a base de dados antiga).
4. Copiar `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`.
5. Preencher `TURSO_DATABASE_URL` e `TURSO_AUTH_TOKEN`.
6. Executar:
   ```bash
   streamlit run app.py
   ```

## Publicação no Streamlit Community Cloud
- Criar um repositório GitHub privado para o projeto.
- Adicionar os ficheiros do projeto.
- Criar uma nova app Streamlit apontando para `app.py`.
- Em App settings → Secrets, configurar:
  ```toml
  TURSO_DATABASE_URL = "libsql://..."
  TURSO_AUTH_TOKEN = "..."
  ```
- Não adicionar `secrets.toml` ao GitHub.

## Segurança e dados
- Esta versão não liga nem altera a base de dados antiga.
- A aplicação cria as tabelas da base nova na primeira execução.
- Não importar CSVs até validar o mapeamento das colunas e a regra de duplicados.
- Fazer exportações periódicas das tabelas através da página Importar / Exportar.

## Estado
É uma primeira versão funcional de estrutura e registo, ainda não é a versão final auditada.
Antes de utilização diária, testar os formulários e cálculos com registos de teste. A importação inteligente, edição/eliminação de registos, alertas de validade, relatórios PDF e testes automatizados ficam para a próxima iteração.
