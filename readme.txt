Projeto 01 - Agente de Rotas para Comida Local (IA 2026-27)
Inteligência Artificial - Licenciatura em Engenharia de Sistemas Informáticos (UPCA / EST)

Grupo G04
  Diogo Apolinário   6731
  Raúl Ribeiro       22552
  Miguel Correia     31028
  José Ferreira      31556

Repositório GitHub:
  https://github.com/JoseFerreira31556/IA26_P01_G04.git


CONTEÚDO
--------
  01_eda_tiny.ipynb           Contexto do projeto, análise exploratória dos dados (EDA)
                              e testes com rotas escritas à mão.
  02_problem_solving.ipynb    Resolução do problema (Greedy e A*, Hill-Climbing, CSP),
                              análise de resultados e conclusão.
  model.py                    Modelo do problema: classes Request, Vehicle, State e Problem,
                              leitura dos CSVs, função de custo (routeCost, solutionCost),
                              verificador de rotas (checkRoute) e tradutora (buildCheckData).
  test_handwritten_routes.py  Testes do verificador com rotas escritas à mão.
  data/data_tiny_20261020/    Ficheiros CSV do dataset tiny.
  readme.txt                  Este ficheiro.


COMO CORRER
-----------
1. Instalar as bibliotecas (Python 3):
     pip install pandas matplotlib python-constraint2 jupyter

2. Manter todos os ficheiros na mesma pasta, com os CSVs em ./data/data_tiny_20261020/
   (os notebooks e o model.py usam este caminho).

3. Abrir os notebooks no Jupyter e correr cada um do início ao fim
   (Kernel > Restart Kernel and Run All), por esta ordem:
     a) 01_eda_tiny.ipynb
     b) 02_problem_solving.ipynb

   Os testes também podem ser corridos sozinhos, no terminal:
     python test_handwritten_routes.py


NOTA SOBRE O USO DE INTELIGÊNCIA ARTIFICIAL
-------------------------------------------
Este projeto foi desenvolvido com o apoio de uma ferramenta de IA generativa
(Claude, da Anthropic). A ferramenta foi usada para:
  - orientar a análise exploratória dos dados, com explicações e pistas;
  - gerar partes do código, em particular os algoritmos do notebook 02
    (adaptados dos notebooks das aulas), o verificador de rotas e a tradutora
    do model.py;
  - rever o código e a documentação, e identificar incongruências entre ficheiros.

Todo o código foi revisto, executado e testado pelo grupo, que assume a
responsabilidade pelo trabalho entregue e está preparado para explicar
cada uma das suas partes.
