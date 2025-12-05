LayOver-e-Notes
Ferramenta desenvolvida para auxiliar na auditoria e conferência de sistemas hoteleiros (Opera Cloud). O objetivo principal é facilitar a visualização de quartos sem comentários informativos sobre o tipo de pagamento e validar os valores de tarifas aplicados a companhias aéreas (Layover).

🚀 Funcionalidades
Auditoria de Notas (GIH01128): Verifica se as reservas possuem comentários internos ("Notes") obrigatórios e se a tarifa está citada nesses comentários.

Conferência de Tarifas Layover: Valida se o valor cobrado nas reservas de companhias aéreas está de acordo com o preço base da unidade.

📋 Modo de Uso
1. Auditoria de Notas (Report GIH01128)
Esta função analisa o relatório XML para identificar reservas Checked In que não possuem notas internas ou que possuem notas, mas sem a informação da tarifa.

Como extrair o relatório no Opera Cloud:

Vá em Reports e busque pelo Report Name: GIH01128.

Clique em Edit Report Parameters.

Marque as seguintes caixas/opções:

[x] Notes

[x] Include Internal Notes

[x] Note Types: Selecione Resv. - GEN

[x] Reservation Status: Selecione Checked In

Em "Generate Report", escolha Download as XML File.

O que o script faz: O sistema percorre o arquivo gerado buscando pelo Número do Quarto, Quantidade de Adultos e Comentários Internos. Ele retorna uma lista de pendências (quem não tem comentário ou quem tem comentário sem tarifa).

2. Conferência de Tarifa de Layover (CSV)
Esta função compara o valor das diárias com o valor acordado para LAyOver

Como extrair os dados no Opera Cloud:

Navegue até Bookings > Reservations > Manage Reservation.

Configure os filtros de busca:

Arrival From: Coloque uma data de início abrangente (ex: 01/01/2025).

Arrival To: Coloque a data atual da conferência (ex: 05/12/2025).

Reservation Status: Selecione IN HOUSE.

Clique em Search.

Para exportar:

Vá em View Options > Export > CSV.

Selecione Loaded Rows e clique em Export.

⚠️ Atenção: O sistema carrega apenas 100 reservas por vez. É necessário rolar a página para carregar mais reservas e repetir a exportação para garantir que todos os dados sejam capturados.

Execução: Carregue os arquivos CSV gerados no script. O sistema retornará uma lista de reservas Corretas e Incorretas baseadas no preço base configurado.

⚙️ Configuração
Preço de Layover: O valor da tarifa de referência deve ser ajustado diretamente no código de acordo com a necessidade da unidade ou mudanças contratuais.


**Irei deixar relatórios XML e CSV de exemplos**
