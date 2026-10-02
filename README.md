# elpis-vagas
Buscador de Vagas com IA
Élpis — Buscador de Vagas com IA v23.1
Aplicação Streamlit para pesquisar oportunidades de emprego no Brasil e no exterior, 
consolidar resultados, exibir mapa e, opcionalmente, analisar vagas com Gemini.
Arquivos necessários
Plain Text
elpis_app_v23_1.py
elpis_fontes.py
elpis_boas_vindas.py
requirements.txt
elpis_fontes.py é obrigatório porque o aplicativo importa:
Python
import elpis_fontes as core
elpis_boas_vindas.py também é obrigatório porque o aplicativo importa:
Python
import elpis_boas_vindas as bv
Instalação local
Plain Text
python -m pip install -r .\requirements.txt
python -m py_compile .\elpis_app_v23_1.py
python -m streamlit run .\elpis_app_v23_1.py
Abra no navegador:
Plain Text
http://localhost:8501
Gemini
A chave Gemini é opcional. A busca funciona sem ela.
Para usar análise de aderência das vagas:
1. digite a chave no painel lateral;
2. clique em Conectar;
3. use a opção de análise por IA;
4. clique em Desconectar quando terminar.
A chave não deve ser colocada diretamente no código ou publicada no GitHub.
Publicação gratuita
O app pode ser publicado no Streamlit Community Cloud conectado a um repositório 
GitHub. No momento da publicação, use:
Plain Text
Main file path: elpis_app_v23_1.py
O repositório pode ser privado.
Observações
•
elpis_sessoes.sqlite3 é criado automaticamente e não precisa ser enviado.
•
.v
env , 
__pycache__ e arquivos 
• 
O arquivo 
.pyc não devem ser publicados.
testar_elpis_v23_1.py é opcional e serve apenas para testes locais.
• 
Não publique chaves de API, senhas ou arquivos 
secrets.toml com valores reais
