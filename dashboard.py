# dashboard_v6.py
import streamlit as st
import pandas as pd
import gspread
import matplotlib.pyplot as plt
from datetime import datetime
import urllib.parse
import hmac
import hashlib
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Resultados - Lifenergy",
    layout="wide"
)

st.markdown(f"""
    <style>
        
        #autoclick-div {{
            display: none;
        }}

    </style>
""", unsafe_allow_html=True)

# --- LISTA MESTRA DE TODAS AS PERGUNTAS ---
@st.cache_data
def carregar_itens_master():
    """Retorna um DataFrame com todos os itens de todos os formulários e seu status de reverso."""
    # IMPORTANTE: Você precisa preencher esta lista com os itens de TODOS os seus formulários.
    # Adicionei apenas alguns exemplos para a lógica funcionar.
    todos_os_itens = [
        ('IF01', 'Instalações Físicas', 'O espaço físico é suficiente...', 'NÃO'),
        ('IF12', 'Instalações Físicas', 'Há obstáculos ou áreas obstruídas...', 'SIM'),
        ('EQ01', 'Equipamentos', 'Os equipamentos necessários estão disponíveis...', 'NÃO'),
        ('EQ11', 'Equipamentos', 'Paradas não planejadas atrapalham...', 'SIM'),
        ('FE01', 'Ferramentas', 'As ferramentas necessárias estão disponíveis...', 'NÃO'),
        ('FE08', 'Ferramentas', 'Ferramentas compartilhadas raramente estão...', 'SIM'),
        ('PT01', 'Postos de Trabalho', 'O posto permite ajuste ergonômico...', 'NÃO'),
        ('PT10', 'Postos de Trabalho', 'O desenho do posto induz posturas forçadas...', 'SIM'),
        ('RN01', 'Regras e Normas', 'As regras da empresa são claras...', 'NÃO'),
        ('PI02', 'Práticas Informais', 'A cultura do “jeitinho”...', 'NÃO'),
        ('RE01', 'Recompensas e Benefícios', 'A política de recompensas e benefícios é justa...', 'NÃO'),
        ('EX01', 'Fatores de Risco (Reversos)', 'Sacrifico frequentemente minha vida pessoal...', 'SIM'),
        ('CU01', 'Cultura Organizacional', 'As práticas diárias refletem...', 'NÃO'),
        ('FRPS01', 'Fatores de Risco Psicossocial (FRPS)', 'No meu ambiente há piadas...', 'SIM'),
        ('RE01', 'A política de recompensas e benefícios é justa e clara.', 'NÃO'),
        ('RE02', 'A remuneração é compatível com as responsabilidades do cargo.', 'NÃO'),
        ('SE01', 'As condições de trabalho garantem minha saúde e segurança.', 'NÃO'),
        ('SE02', 'A empresa investe em prevenção de acidentes e treinamentos de segurança.', 'NÃO'),
        ('RC01', 'Meu esforço e resultados são reconhecidos com frequência.', 'NÃO'),
        ('RC02', 'Sinto que minhas contribuições são valorizadas pela liderança.', 'NÃO'),
        ('EQ01', 'Equilibro bem minhas responsabilidades pessoais e profissionais.', 'NÃO'),
        ('EQ02', 'A carga horária e o ritmo de trabalho permitem qualidade de vida.', 'NÃO'),
        ('EX01', 'Sacrifico frequentemente minha vida pessoal por excesso de trabalho.', 'SIM'),
        ('EX02', 'O reconhecimento acontece raramente ou de forma desigual.', 'SIM'),
        ('COM01', 'As mensagens são claras e compreensíveis para todos.', 'NÃO'),
        ('COM02', 'A equipe pratica escuta ativa nas interações.', 'NÃO'),
        ('COM03', 'O feedback é frequente, respeitoso e construtivo.', 'NÃO'),
        ('COM04', 'Informações relevantes são compartilhadas com transparência.', 'NÃO'),
        ('COM05', 'Os canais de comunicação são acessíveis e bem utilizados.', 'NÃO'),
        ('COM06', 'A comunicação entre áreas é fluida e colaborativa.', 'NÃO'),
        ('COM07', 'As reuniões são objetivas, com pautas e registros.', 'NÃO'),
        ('COM08', 'Ruídos, boatos e mal-entendidos atrapalham o trabalho.', 'SIM'),
        ('GC01', 'Conflitos são identificados e tratados logo no início.', 'NÃO'),
        ('GC02', 'Existem critérios/processos claros para mediar conflitos.', 'NÃO'),
        ('GC03', 'As partes são ouvidas de forma imparcial e respeitosa.', 'NÃO'),
        ('GC04', 'Busca-se soluções que considerem os interesses de todos.', 'NÃO'),
        ('GC05', 'É seguro discordar e expor pontos de vista diferentes.', 'NÃO'),
        ('GC06', 'A liderança intervém quando necessário, de modo justo.', 'NÃO'),
        ('GC07', 'Conflitos se arrastam por muito tempo sem solução.', 'SIM'),
        ('GC08', 'Discussões descambam para ataques pessoais.', 'SIM'),
        ('TE01', 'Há objetivos compartilhados e entendimento de prioridades.', 'NÃO'),
        ('TE02', 'Os membros cooperam e se apoiam nas entregas.', 'NÃO'),
        ('TE03', 'Há troca de conhecimentos e boas práticas.', 'NÃO'),
        ('TE04', 'Papéis e responsabilidades são claros para todos.', 'NÃO'),
        ('TE05', 'A equipe se organiza para ajudar nos picos de demanda.', 'NÃO'),
        ('TE06', 'Existe confiança mútua entre os membros.', 'NÃO'),
        ('TE07', 'Existem silos entre áreas ou equipes que dificultam o trabalho.', 'SIM'),
        ('TE08', 'Há competição desleal ou sabotagem entre colegas.', 'SIM'),
        ('RES01', 'As interações são cordiais e educadas.', 'NÃO'),
        ('RES02', 'Horários e compromissos são respeitados.', 'NÃO'),
        ('RES03', 'Contribuições são reconhecidas de forma justa.', 'NÃO'),
        ('RES04', 'Interrupções desrespeitosas acontecem com frequência.', 'SIM'),
        ('RES05', 'Há respeito pela diversidade de opiniões.', 'NÃO'),
        ('RES06', 'A privacidade e os limites pessoais são respeitados.', 'NÃO'),
        ('RES07', 'A comunicação não-violenta é incentivada e praticada.', 'NÃO'),
        ('RES08', 'Piadas ofensivas ou tom agressivo são tolerados.', 'SIM'),
        ('INC01', 'Existem oportunidades iguais de participação e desenvolvimento.', 'NÃO'),
        ('INC02', 'Há representatividade de pessoas diversas em decisões.', 'NÃO'),
        ('INC03', 'Acessibilidade (linguagem, recursos) é considerada nas interações.', 'NÃO'),
        ('INC04', 'Fazem-se adaptações razoáveis quando necessário.', 'NÃO'),
        ('INC05', 'Políticas antidiscriminação são conhecidas e aplicadas.', 'NÃO'),
        ('INC06', 'As pessoas sentem que pertencem ao grupo/equipe.', 'NÃO'),
        ('INC07', 'Microagressões são toleradas ou minimizadas.', 'SIM'),
        ('INC08', 'Vozes minoritárias são ignoradas em discussões/decisões.', 'SIM'),
        ('CONV01', 'Os valores organizacionais são claros e conhecidos.', 'NÃO'),
        ('CONV02', 'Há coerência entre discurso e prática no dia a dia.', 'NÃO'),
        ('CONV03', 'As decisões são tomadas com base em princípios éticos.', 'NÃO'),
        ('CONV04', 'Há segurança para manifestar convicções de forma respeitosa.', 'NÃO'),
        ('CONV05', 'Crenças diversas são respeitadas sem imposição.', 'NÃO'),
        ('CONV06', 'Conflitos de valores são evitados ou ignorados.', 'SIM'),
        ('CONV07', 'Práticas antiéticas são normalizadas no cotidiano.', 'SIM'),
        ('CONV08', 'Há incentivo a ações de responsabilidade social.', 'NÃO'),
        ('LID01', 'A liderança é acessível e presente no dia a dia.', 'NÃO'),
        ('LID02', 'Define e comunica prioridades com clareza.', 'NÃO'),
        ('LID03', 'Reconhece e dá feedback sobre o desempenho.', 'NÃO'),
        ('LID04', 'Estimula o desenvolvimento/mentoria da equipe.', 'NÃO'),
        ('LID05', 'Considera dados e escuta a equipe nas decisões.', 'NÃO'),
        ('LID06', 'Há microgerenciamento excessivo.', 'SIM'),
        ('LID07', 'Favoritismo influencia decisões e oportunidades.', 'SIM'),
        ('LID08', 'Promove colaboração entre áreas/equipes.', 'NÃO'),
        ('IF01', 'O espaço físico é suficiente para as atividades sem congestionamentos.', 'NÃO'),
        ('IF02', 'A limpeza e a organização das áreas são mantidas ao longo do dia.', 'NÃO'),
        ('IF03', 'A iluminação geral é adequada às tarefas realizadas.', 'NÃO'),
        ('IF04', 'A temperatura e a ventilação são adequadas ao tipo de atividade.', 'NÃO'),
        ('IF05', 'O nível de ruído não prejudica a concentração e a comunicação.', 'NÃO'),
        ('IF06', 'A sinalização de rotas, setores e riscos é clara e suficiente.', 'NÃO'),
        ('IF07', 'As saídas de emergência estão desobstruídas e bem sinalizadas.', 'NÃO'),
        ('IF08', 'O layout facilita o fluxo de pessoas, materiais e informações.', 'NÃO'),
        ('IF09', 'As áreas de armazenamento são dimensionadas e identificadas adequadamente.', 'NÃO'),
        ('IF10', 'A infraestrutura é acessível (rampas, corrimãos, largura de portas) para PCD.', 'NÃO'),
        ('IF11', 'Pisos, paredes e tetos estão em bom estado de conservação.', 'NÃO'),
        ('IF12', 'Há obstáculos ou áreas obstruídas que dificultam a circulação.', 'SIM'),
        ('EQ01', 'Os equipamentos necessários estão disponíveis quando requisitados.', 'NÃO'),
        ('EQ02', 'Os equipamentos possuem capacidade/recursos adequados às tarefas.', 'NÃO'),
        ('EQ03', 'Os equipamentos operam de forma confiável, sem falhas frequentes.', 'NÃO'),
        ('EQ04', 'O plano de manutenção preventiva está atualizado e é cumprido.', 'NÃO'),
        ('EQ05', 'O histórico de manutenção está documentado e acessível.', 'NÃO'),
        ('EQ06', 'Instrumentos críticos estão calibrados dentro dos prazos.', 'NÃO'),
        ('EQ07', 'Há disponibilidade de peças de reposição críticas.', 'NÃO'),
        ('EQ08', 'Os usuários dos equipamentos recebem treinamento adequado.', 'NÃO'),
        ('EQ09', 'Manuais e procedimentos de operação estão acessíveis.', 'NÃO'),
        ('EQ10', 'Dispositivos de segurança (proteções, intertravamentos) estão instalados e operantes.', 'NÃO'),
        ('EQ11', 'Paradas não planejadas atrapalham significativamente a rotina de trabalho.', 'SIM'),
        ('EQ12', 'Há equipamentos obsoletos que comprometem a qualidade ou a segurança.', 'SIM'),
        ('FE01', 'As ferramentas necessárias estão disponíveis quando preciso.', 'NÃO'),
        ('FE02', 'As ferramentas possuem qualidade e são adequadas ao trabalho.', 'NÃO'),
        ('FE03', 'As ferramentas manuais são ergonômicas e confortáveis de usar.', 'NÃO'),
        ('FE04', 'Existe padronização adequada de tipos e modelos de ferramentas.', 'NÃO'),
        ('FE05', 'Ferramentas estão identificadas (etiquetas/códigos) e rastreáveis.', 'NÃO'),
        ('FE06', 'O armazenamento é organizado (5S) e evita danos/perdas.', 'NÃO'),
        ('FE07', 'Manutenção/afiação/ajustes estão em dia quando necessário.', 'NÃO'),
        ('FE08', 'Ferramentas compartilhadas raramente estão onde deveriam.', 'SIM'),
        ('FE09', 'Os colaboradores são treinados para o uso correto das ferramentas.', 'NÃO'),
        ('FE10', 'Ferramentas danificadas são substituídas com rapidez.', 'NÃO'),
        ('FE11', 'Existem ferramentas improvisadas em uso nas atividades.', 'SIM'),
        ('FE12', 'As ferramentas estão em conformidade com requisitos de segurança (isolantes, antifaísca, etc.).', 'NÃO'),
        ('PT01', 'O posto permite ajuste ergonômico (altura, apoios, cadeiras).', 'NÃO'),
        ('PT02', 'Materiais e dispositivos estão posicionados ao alcance adequado.', 'NÃO'),
        ('PT03', 'A iluminação focal no posto é adequada.', 'NÃO'),
        ('PT04', 'Ruído e vibração no posto estão dentro de limites aceitáveis.', 'NÃO'),
        ('PT05', 'Há ventilação/exaustão local adequada quando necessário.', 'NÃO'),
        ('PT06', 'Os EPIs necessários estão disponíveis, em bom estado e são utilizados.', 'NÃO'),
        ('PT07', 'O posto está organizado (5S) e livre de excessos.', 'NÃO'),
        ('PT08', 'Instruções de trabalho estão visíveis e atualizadas.', 'NÃO'),
        ('PT09', 'Computadores, softwares e internet funcionam de forma estável.', 'NÃO'),
        ('PT10', 'O desenho do posto induz posturas forçadas ou movimentos repetitivos excessivos.', 'SIM'),
        ('PT11', 'Há falta de EPI adequado ou em bom estado.', 'SIM'),
        ('PT12', 'Cabos, fios ou objetos soltos representam riscos no posto.', 'SIM'),
        ('IF01', 'O espaço físico é suficiente para as atividades sem congestionamentos.', 'NÃO'),
        ('IF02', 'A limpeza e a organização das áreas são mantidas ao longo do dia.', 'NÃO'),
        ('IF03', 'A iluminação geral é adequada às tarefas realizadas.', 'NÃO'),
        ('IF04', 'A temperatura e a ventilação são adequadas ao tipo de atividade.', 'NÃO'),
        ('IF05', 'O nível de ruído não prejudica a concentração e a comunicação.', 'NÃO'),
        ('IF06', 'A sinalização de rotas, setores e riscos é clara e suficiente.', 'NÃO'),
        ('IF07', 'As saídas de emergência estão desobstruídas e bem sinalizadas.', 'NÃO'),
        ('IF08', 'O layout facilita o fluxo de pessoas, materiais e informações.', 'NÃO'),
        ('IF09', 'As áreas de armazenamento são dimensionadas e identificadas adequadamente.', 'NÃO'),
        ('IF10', 'A infraestrutura é acessível (rampas, corrimãos, largura de portas) para PCD.', 'NÃO'),
        ('IF11', 'Pisos, paredes e tetos estão em bom estado de conservação.', 'NÃO'),
        ('IF12', 'Há obstáculos ou áreas obstruídas que dificultam a circulação.', 'SIM'),
        ('EQ01', 'Os equipamentos necessários estão disponíveis quando requisitados.', 'NÃO'),
        ('EQ02', 'Os equipamentos possuem capacidade/recursos adequados às tarefas.', 'NÃO'),
        ('EQ03', 'Os equipamentos operam de forma confiável, sem falhas frequentes.', 'NÃO'),
        ('EQ04', 'O plano de manutenção preventiva está atualizado e é cumprido.', 'NÃO'),
        ('EQ05', 'O histórico de manutenção está documentado e acessível.', 'NÃO'),
        ('EQ06', 'Instrumentos críticos estão calibrados dentro dos prazos.', 'NÃO'),
        ('EQ07', 'Há disponibilidade de peças de reposição críticas.', 'NÃO'),
        ('EQ08', 'Os usuários dos equipamentos recebem treinamento adequado.', 'NÃO'),
        ('EQ09', 'Manuais e procedimentos de operação estão acessíveis.', 'NÃO'),
        ('EQ10', 'Dispositivos de segurança (proteções, intertravamentos) estão instalados e operantes.', 'NÃO'),
        ('EQ11', 'Paradas não planejadas atrapalham significativamente a rotina de trabalho.', 'SIM'),
        ('EQ12', 'Há equipamentos obsoletos que comprometem a qualidade ou a segurança.', 'SIM'),
        ('FE01', 'As ferramentas necessárias estão disponíveis quando preciso.', 'NÃO'),
        ('FE02', 'As ferramentas possuem qualidade e são adequadas ao trabalho.', 'NÃO'),
        ('FE03', 'As ferramentas manuais são ergonômicas e confortáveis de usar.', 'NÃO'),
        ('FE04', 'Existe padronização adequada de tipos e modelos de ferramentas.', 'NÃO'),
        ('FE05', 'Ferramentas estão identificadas (etiquetas/códigos) e rastreáveis.', 'NÃO'),
        ('FE06', 'O armazenamento é organizado (5S) e evita danos/perdas.', 'NÃO'),
        ('FE07', 'Manutenção/afiação/ajustes estão em dia quando necessário.', 'NÃO'),
        ('FE08', 'Ferramentas compartilhadas raramente estão onde deveriam.', 'SIM'),
        ('FE09', 'Os colaboradores são treinados para o uso correto das ferramentas.', 'NÃO'),
        ('FE10', 'Ferramentas danificadas são substituídas com rapidez.', 'NÃO'),
        ('FE11', 'Existem ferramentas improvisadas em uso nas atividades.', 'SIM'),
        ('FE12', 'As ferramentas estão em conformidade com requisitos de segurança (isolantes, antifaísca, etc.).', 'NÃO'),
        ('PT01', 'O posto permite ajuste ergonômico (altura, apoios, cadeiras).', 'NÃO'),
        ('PT02', 'Materiais e dispositivos estão posicionados ao alcance adequado.', 'NÃO'),
        ('PT03', 'A iluminação focal no posto é adequada.', 'NÃO'),
        ('PT04', 'Ruído e vibração no posto estão dentro de limites aceitáveis.', 'NÃO'),
        ('PT05', 'Há ventilação/exaustão local adequada quando necessário.', 'NÃO'),
        ('PT06', 'Os EPIs necessários estão disponíveis, em bom estado e são utilizados.', 'NÃO'),
        ('PT07', 'O posto está organizado (5S) e livre de excessos.', 'NÃO'),
        ('PT08', 'Instruções de trabalho estão visíveis e atualizadas.', 'NÃO'),
        ('PT09', 'Computadores, softwares e internet funcionam de forma estável.', 'NÃO'),
        ('PT10', 'O desenho do posto induz posturas forçadas ou movimentos repetitivos excessivos.', 'SIM'),
        ('PT11', 'Há falta de EPI adequado ou em bom estado.', 'SIM'),
        ('PT12', 'Cabos, fios ou objetos soltos representam riscos no posto.', 'SIM'),
        ('CL01', 'As práticas diárias refletem o que a liderança diz e cobra.', 'NÃO'),
        ('CL02', 'Processos críticos têm donos claros e rotina de revisão.', 'NÃO'),
        ('CL03', 'A comunicação visual (quadros, murais, campanhas) reforça os valores da empresa.', 'NÃO'),
        ('CL04', 'Reconhecimentos e premiações estão alinhados ao comportamento esperado.', 'NÃO'),
        ('CL05', 'Feedbacks e aprendizados com erros ocorrem sem punição inadequada.', 'NÃO'),
        ('CL06', 'Conflitos são tratados com respeito e foco em solução.', 'NÃO'),
        ('CL07', 'Integridade e respeito orientam decisões, mesmo sob pressão.', 'NÃO'),
        ('CL08', 'Não há tolerância a discriminação, assédio ou retaliação.', 'NÃO'),
        ('CL09', 'Critérios de decisão são transparentes e consistentes.', 'NÃO'),
        ('CL10', 'A empresa cumpre o que promete a pessoas e clientes.', 'NÃO'),
        ('CL11', 'Acreditamos que segurança e saúde emocional são inegociáveis.', 'NÃO'),
        ('CL12', 'Acreditamos que diversidade melhora resultados.', 'NÃO'),
        ('CL13', 'Há rituais de reconhecimento (semanal/mensal) que celebram comportamentos-chave.', 'NÃO'),
        ('CL14', 'Reuniões de resultado incluem aprendizados (o que manter, o que ajustar).', 'NÃO'),
        ('CL15', 'Políticas internas são conhecidas e aplicadas (não ficam só no papel).', 'NÃO'),
        ('CA01', 'Sistemas suportam o trabalho (não criam retrabalho ou gargalos).', 'NÃO'),
        ('CA02', 'Indicadores de pessoas e segurança são acompanhados periodicamente.', 'NÃO'),
        ('CA03', 'A linguagem interna é respeitosa e inclusiva.', 'NÃO'),
        ('CA04', 'Termos e siglas são explicados para evitar exclusão.', 'NÃO'),
        ('CA05', 'A comunicação interna é clara e no tempo certo.', 'NÃO'),
        ('CA06', 'Metas e resultados são divulgados com clareza.', 'NÃO'),
        ('SP01', 'Sinto segurança psicológica para expor opiniões e erros.', 'NÃO'),
        ('SP02', 'Consigo equilibrar trabalho e vida pessoal.', 'NÃO'),
        ('SP03', 'Práticas de contratação e promoção são justas e inclusivas.', 'NÃO'),
        ('SP04', 'A empresa promove ambientes livres de assédio e discriminação.', 'NÃO'),
        ('SP05', 'Tenho acesso a ações de saúde/apoio emocional quando preciso.', 'NÃO'),
        ('SP06', 'Carga de trabalho é ajustada para prevenir sobrecarga crônica.', 'NÃO'),
        ('SP07', 'Recebo treinamentos relevantes ao meu perfil de risco e função.', 'NÃO'),
        ('SP08', 'Tenho oportunidades reais de desenvolvimento profissional.', 'NÃO'),
        ('SP09', 'Sou ouvido(a) nas decisões que afetam meu trabalho.', 'NÃO'),
        ('GR01', 'Existe canal de denúncia acessível e confiável.', 'NÃO'),
        ('GR02', 'Conheço o Código de Ética e como reportar condutas impróprias.', 'NÃO'),
        ('GR03', 'Sinto confiança nos processos de investigação e resposta a denúncias.', 'NÃO'),
        ('GR04', 'Há prestação de contas sobre planos e ações corretivas.', 'NÃO'),
        ('GR05', 'Riscos relevantes são identificados e acompanhados regularmente.', 'NÃO'),
        ('GR06', 'Controles internos funcionam e são revisados quando necessário.', 'NÃO'),
        ('GR07', 'Inventário de riscos e planos de ação (PGR) estão atualizados e acessíveis.', 'NÃO'),
        ('GR08', 'Mudanças de processo passam por avaliação de risco antes da implantação.', 'NÃO'),
        ('GR09', 'O canal de denúncia é acessível e protege contra retaliações.', 'NÃO'),
        ('GR10', 'Sinto que denúncias geram ações efetivas.', 'NÃO'),
        ('GR11', 'Tenho meios simples para reportar incidentes/quase-acidentes e perigos.', 'NÃO'),
        ('GR12', 'No meu posto, riscos são avaliados considerando exposição e severidade x probabilidade.', 'NÃO'),
        ('GR13', 'A empresa prioriza eliminar/substituir riscos antes de recorrer ao EPI.', 'NÃO'),
        ('GR14', 'Recebo treinamento quando há mudanças de função/processo/equipamentos.', 'NÃO'),
        ('GR15', 'Há inspeções/observações de segurança com frequência adequada.', 'NÃO'),
        ('GR16', 'Sinalização e procedimentos são claros e atualizados.', 'NÃO'),
        ('GR17', 'Sou convidado(a) a participar das discussões de riscos e soluções.', 'NÃO'),
        ('GR18', 'Planos de emergência são conhecidos e incidentes são investigados com ações corretivas.', 'NÃO'),
        ('FR01', 'No meu ambiente há piadas, constrangimentos ou condutas indesejadas.', 'SIM'),
        ('FR02', 'Tenho receio de represálias ao reportar assédio ou condutas impróprias.', 'SIM'),
        ('FR03', 'Conflitos entre áreas/pessoas permanecem sem solução por muito tempo.', 'SIM'),
        ('FR04', 'Falta respeito nas interações do dia a dia.', 'SIM'),
        ('FR05', 'Falta de informações atrapalha minha entrega.', 'SIM'),
        ('FR06', 'Mensagens importantes chegam tarde ou de forma confusa.', 'SIM'),
        ('FR07', 'Trabalho frequentemente isolado sem suporte adequado.', 'SIM'),
        ('FR08', 'Em teletrabalho me sinto desconectado(a) da equipe.', 'SIM'),
        ('FR09', 'A sobrecarga e prazos incompatíveis são frequentes.', 'SIM'),
        ('FR10', 'As expectativas de produtividade são irreais no meu contexto.', 'SIM'),
        ('RN01', 'As regras da empresa são claras e bem comunicadas a todos os colaboradores.', 'NÃO'),
        ('RN02', 'As normas são aplicadas de forma justa e consistente entre os diferentes setores.', 'NÃO'),
        ('RN03', 'As políticas internas são seguidas na prática, e não apenas no papel.', 'NÃO'),
        ('RN04', 'A empresa revisa e atualiza suas normas de acordo com mudanças no mercado ou legislação.', 'NÃO'),
        ('RI01', 'A empresa é reconhecida externamente como uma organização ética.', 'NÃO'),
        ('RI02', 'Os clientes e parceiros confiam na imagem da empresa.', 'NÃO'),
        ('RI03', 'A reputação da empresa influencia positivamente a motivação dos colaboradores.', 'NÃO'),
        ('RI04', 'A organização é vista como inovadora e de credibilidade no seu setor.', 'NÃO'),
        ('VO01', 'Os valores da empresa são conhecidos e compreendidos pelos colaboradores.', 'NÃO'),
        ('VO02', 'Os líderes praticam os valores que divulgam.', 'NÃO'),
        ('VO03', 'Os valores da empresa orientam decisões estratégicas.', 'NÃO'),
        ('VO04', 'Existe coerência entre discurso e prática em relação aos valores da organização.', 'NÃO'),
        ('PF01', 'Os processos de gestão são padronizados e documentados.', 'NÃO'),
        ('PF02', 'Existem rituais e práticas formais que reforçam a cultura organizacional (ex.: reuniões, relatórios, treinamentos).', 'NÃO'),
        ('PF03', 'Há critérios claros e formais para promoção e reconhecimento de colaboradores.', 'NÃO'),
        ('PF04', 'A empresa oferece programas estruturados de desenvolvimento de pessoas.', 'NÃO'),
        ('PI01', 'A troca de informações ocorre de maneira espontânea e colaborativa.', 'NÃO'),
        ('PI02', 'A cultura do “jeitinho” (soluções improvisadas) é comum na empresa.', 'NÃO'),
        ('PI03', 'Os relacionamentos pessoais influenciam fortemente decisões internas.', 'NÃO'),
        ('PI04', 'Existem redes de apoio informais entre os colaboradores (amizades, grupos, trocas).', 'NÃO'),
        ('CO01', 'As práticas diárias refletem o que a liderança diz e cobra.', 'NÃO'),
        ('CO02', 'Processos críticos têm donos claros e rotina de revisão.', 'NÃO'),
        ('CO03', 'A comunicação visual (quadros, murais, campanhas) reforça os valores da empresa.', 'NÃO'),
        ('CO04', 'Reconhecimentos e premiações estão alinhados ao comportamento esperado.', 'NÃO'),
        ('CO05', 'Feedbacks e aprendizados com erros ocorrem sem punição inadequada.', 'NÃO'),
        ('CO06', 'Conflitos são tratados com respeito e foco em solução.', 'NÃO'),
        ('CO07', 'Integridade e respeito orientam decisões, mesmo sob pressão.', 'NÃO'),
        ('CO08', 'Não há tolerância a discriminação, assédio ou retaliação.', 'NÃO'),
        ('CO09', 'Critérios de decisão são transparentes e consistentes.', 'NÃO'),
        ('CO10', 'A empresa cumpre o que promete a pessoas e clientes.', 'NÃO'),
        ('CO11', 'Acreditamos que segurança e saúde emocional são inegociáveis.', 'NÃO'),
        ('CO12', 'Acreditamos que diversidade melhora resultados.', 'NÃO'),
        ('CO13', 'Há rituais de reconhecimento (semanal/mensal) que celebram comportamentos-chave.', 'NÃO'),
        ('CO14', 'Reuniões de resultado incluem aprendizados (o que manter, o que ajustar).', 'NÃO'),
        ('CO15', 'Políticas internas são conhecidas e aplicadas (não ficam só no papel).', 'NÃO'),
        ('CO16', 'Existe canal de denúncia acessível e confiável.', 'NÃO'),
        ('CO17', 'Sistemas suportam o trabalho (não criam retrabalho ou gargalos).', 'NÃO'),
        ('CO18', 'Indicadores de pessoas e segurança são acompanhados periodicamente.', 'NÃO'),
        ('CO19', 'A linguagem interna é respeitosa e inclusiva.', 'NÃO'),
        ('CO20', 'Termos e siglas são explicados para evitar exclusão.', 'NÃO'),
        ('CO21', 'Sinto segurança psicológica para expor opiniões e erros.', 'NÃO'),
        ('CO22', 'Consigo equilibrar trabalho e vida pessoal.', 'NÃO'),
        ('ESGS01', 'Práticas de contratação e promoção são justas e inclusivas.', 'NÃO'),
        ('ESGS02', 'A empresa promove ambientes livres de assédio e discriminação.', 'NÃO'),
        ('ESGS03', 'Tenho acesso a ações de saúde/apoio emocional quando preciso.', 'NÃO'),
        ('ESGS04', 'Carga de trabalho é ajustada para prevenir sobrecarga crônica.', 'NÃO'),
        ('ESGS05', 'Recebo treinamentos relevantes ao meu perfil de risco e função.', 'NÃO'),
        ('ESGS06', 'Tenho oportunidades reais de desenvolvimento profissional.', 'NÃO'),
        ('ESGS07', 'Sou ouvido(a) nas decisões que afetam meu trabalho.', 'NÃO'),
        ('ESGS08', 'A comunicação interna é clara e no tempo certo.', 'NÃO'),
        ('ESGG01', 'Conheço o Código de Ética e como reportar condutas impróprias.', 'NÃO'),
        ('ESGG02', 'Sinto confiança nos processos de investigação e resposta a denúncias.', 'NÃO'),
        ('ESGG03', 'Metas e resultados são divulgados com clareza.', 'NÃO'),
        ('ESGG04', 'Há prestação de contas sobre planos e ações corretivas.', 'NÃO'),
        ('ESGG05', 'Controles', 'Riscos relevantes são identificados e acompanhados regularmente.', 'NÃO'),
        ('ESGG06', 'Controles', 'Controles internos funcionam e são revisados quando necessário.', 'NÃO'),
        ('ESGG07', 'Inventário de riscos e planos de ação (PGR) estão atualizados e acessíveis.', 'NÃO'),
        ('ESGG08', 'Mudanças de processo passam por avaliação de risco antes da implantação.', 'NÃO'),
        ('ESGG09', 'O canal de denúncia é acessível e protege contra retaliações.', 'NÃO'),
        ('ESGG10', 'Sinto que denúncias geram ações efetivas.', 'NÃO'),
        ('NR101', 'Tenho meios simples para reportar incidentes/quase-acidentes e perigos.', 'NÃO'),
        ('NR102', 'No meu posto, riscos são avaliados considerando exposição e severidade x probabilidade.', 'NÃO'),
        ('NR103', 'A empresa prioriza eliminar/substituir riscos antes de recorrer ao EPI.', 'NÃO'),
        ('NR104', 'Recebo treinamento quando há mudanças de função/processo/equipamentos.', 'NÃO'),
        ('NR105', 'Há inspeções/observações de segurança com frequência adequada.', 'NÃO'),
        ('NR106', 'Sinalização e procedimentos são claros e atualizados.', 'NÃO'),
        ('NR107', 'Sou convidado(a) a participar das discussões de riscos e soluções.', 'NÃO'),
        ('NR108', 'Planos de emergência são conhecidos e incidentes são investigados com ações corretivas.', 'NÃO'),
        ('FRPS01', 'No meu ambiente há piadas, constrangimentos ou condutas indesejadas.', 'SIM'),
        ('FRPS02', 'Tenho receio de represálias ao reportar assédio ou condutas impróprias.', 'SIM'),
        ('FRPS03', 'Conflitos entre áreas/pessoas permanecem sem solução por muito tempo.', 'SIM'),
        ('FRPS04', 'Falta respeito nas interações do dia a dia.', 'SIM'),
        ('FRPS05', 'Falta de informações atrapalha minha entrega.', 'SIM'),
        ('FRPS06', 'Mensagens importantes chegam tarde ou de forma confusa.', 'SIM'),
        ('FRPS07', 'Trabalho frequentemente isolado sem suporte adequado.', 'SIM'),
        ('FRPS08', 'Em teletrabalho me sinto desconectado(a) da equipe.', 'SIM'),
        ('FRPS09', 'Demandas', 'A sobrecarga e prazos incompatíveis são frequentes.', 'SIM'),
        ('FRPS10', 'Demandas', 'As expectativas de produtividade são irreais no meu contexto.', 'SIM'),
        # ... (continue adicionando todos os outros itens aqui) ...
    ]
    df_master = pd.DataFrame(todos_os_itens, columns=["ID_Item", "Dimensão", "Item", "Reverso"])
    # O dashboard usa a coluna 'Item' para fazer a correspondência.
    return df_master

# --- CONEXÃO COM GOOGLE SHEETS E CARREGAMENTO DE DADOS ---
@st.cache_resource
def connect_to_gsheet():
    creds_dict = dict(st.secrets["google_credentials"])
    creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
    gc = gspread.service_account_from_dict(creds_dict)
    spreadsheet = gc.open("Respostas Formularios")
    return spreadsheet

@st.cache_data(ttl=600)
def load_all_data(_spreadsheet, _df_master):
    # O _rerun_trigger não é usado, mas sua mudança invalida o cache
    if _spreadsheet is None: return pd.DataFrame()
    worksheets = _spreadsheet.worksheets()
    all_dfs = []
    # ... (lógica de leitura das abas permanece a mesma) ...
    for ws in worksheets:
         if "observacoes" not in ws.title.lower() and "teste" not in ws.title.lower():
             try:
                 data = ws.get_all_records()
                 if data:
                     df = pd.DataFrame(data)
                     all_dfs.append(df)
             except Exception as e:
                 st.warning(f"Não foi possível ler a aba '{ws.title}': {e}")
    if not all_dfs: return pd.DataFrame()
    consolidated_df = pd.concat(all_dfs, ignore_index=True)
    
    # --- CÁLCULO DA PONTUAÇÃO ---
    consolidated_df = pd.merge(consolidated_df, _df_master[['Item', 'Reverso']], on='Item', how='left')
    consolidated_df['Resposta_Num'] = pd.to_numeric(consolidated_df['Resposta'], errors='coerce')
    def ajustar_reverso(row):
        # Primeiro, verifica se a pontuação é válida
        if pd.isna(row['Resposta_Num']): 
            return None
        # Verifica se a coluna 'Reverso' existe, não é NaN E é igual a 'SIM'
        if pd.notna(row['Reverso']) and row['Reverso'] == 'SIM': 
            return 6 - row['Resposta_Num']
        # Caso contrário, retorna a pontuação normal
        else:
            return row['Resposta_Num']
    consolidated_df['Pontuação'] = consolidated_df.apply(ajustar_reverso, axis=1)
    consolidated_df['Data'] = pd.to_datetime(consolidated_df['Data'], errors='coerce', dayfirst=True)
    consolidated_df = consolidated_df.dropna(subset=['Data'])
    return consolidated_df

# --- GERADOR DE LINKS DE FORMULÁRIO ---
st.header("🔗 Gerador de Links para Formulários")

with st.container(border=True):
    st.markdown("Preencha o nome da Organização Coletora e selecione o formulário para gerar um link pré-preenchido e não editável.")

    # Input para o nome da Organização Coletora
    org_coletora_input = st.text_input("Nome da Organização Coletora:", key="input_org_link")

    # Mapeamento de nomes amigáveis para as URLs base dos seus apps
    apps_urls = {
        "Cultura e Prática": "https://wedja-culturaepratica.streamlit.app/",
        "Fatores Essenciais": "https://wedja-fatoresessenciais.streamlit.app/",
        "Fatores Interpessoais": "https://wedja-fatoresinterpesoais.streamlit.app/",
        "Fatores Essenciais": "https://wedja-fatoresessenciais.streamlit.app/",
        "Inventário de Infraestrutura": "https://wedja-consultoria.streamlit.app/",
        "Inventário de Infraestrutura Likert": "https://wedja-likert.streamlit.app/",
        "Inventário Organizacional": "https://wedja-organizacional.streamlit.app/",
        "Cultura Organizacional e Saúde Emocional": "https://wedja-saudeemocional.streamlit.app/",
    }

    form_selecionado = st.selectbox("Selecione o Formulário:", options=list(apps_urls.keys()))

    if st.button("Gerar Link Seguro", key="generate_link_button"):
        if not org_coletora_input:
            st.warning("Por favor, insira o nome da Organização Coletora.")
        elif not form_selecionado:
             st.warning("Por favor, selecione um formulário.")
        else:
            base_url = apps_urls[form_selecionado]
            org_encoded = urllib.parse.quote(org_coletora_input)
            
            # --- Lógica de Assinatura ---
            secret_key = st.secrets["LINK_SECRET_KEY"].encode('utf-8')
            message = org_coletora_input.encode('utf-8') # Assina o nome original, não o codificado
            
            # Calcula a assinatura HMAC-SHA256
            signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
            # --- Fim da Lógica de Assinatura ---

            # Monta a URL final com organização e assinatura
            link_final = f"{base_url}?org={org_encoded}&sig={signature}"
            
            st.success("Link Seguro Gerado!")
            st.markdown(f"**Link para {form_selecionado} (Organização: {org_coletora_input}):**")
            st.code(link_final, language=None)
            st.markdown("Copie este link. A organização não poderá ser alterada pelo usuário.")
# ##### CABEÇALHO MODIFICADO #####
st.title("📊 Dashboard de Análise de Respostas")

# Botão para recarregar dados, agora abaixo do título e à esquerda
if st.button("CARREGAR DADOS", key="load_data_button"):
    # Limpa o cache especificamente para esta função
    load_all_data.clear()
    st.success("Forçando recarregamento dos dados...")
    st.rerun() # Reexecuta o script para carregar os dados frescos

df_master_itens = carregar_itens_master()
spreadsheet = connect_to_gsheet()
df = load_all_data(spreadsheet, df_master_itens) # Argumento _rerun_trigger removido

# Carrega os dados após a definição do botão (para que o rerun funcione)
df_master_itens = carregar_itens_master()
spreadsheet = connect_to_gsheet()
df = load_all_data(spreadsheet, df_master_itens)
if df.empty:
    st.warning("Não foi possível carregar ou processar dados das planilhas.")
    st.stop()

# --- BARRA LATERAL DE FILTROS ---
st.sidebar.header("Filtros")
lista_respondentes = df['Respondente'].dropna().unique().tolist()
respondentes_selecionados = st.sidebar.multiselect("Filtrar por Respondente:", options=lista_respondentes)

min_date = df['Data'].min().date()
max_date = df['Data'].max().date()
data_selecionada = st.sidebar.date_input(
    "Filtrar por Período:", value=(min_date, max_date),
    min_value=min_date, max_value=max_date
)

lista_dimensoes = df['Dimensão'].dropna().unique().tolist()
dimensoes_selecionadas = st.sidebar.multiselect("Filtrar por Dimensão (opcional):", options=lista_dimensoes)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df.copy()
if len(data_selecionada) == 2:
    start_date, end_date = data_selecionada
    df_filtrado = df_filtrado[df_filtrado['Data'].dt.date.between(start_date, end_date)]
if respondentes_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Respondente'].isin(respondentes_selecionados)]
if dimensoes_selecionadas:
    df_filtrado = df_filtrado[df_filtrado['Dimensão'].isin(dimensoes_selecionadas)]

# --- EXIBIÇÃO DOS RESULTADOS ---
st.header("Análise de Desempenho por Dimensão")

resumo_dimensoes = pd.DataFrame() # Inicializa vazio
if not df_filtrado.empty:
    resumo_dimensoes = df_filtrado.groupby('Dimensão')['Pontuação'].mean().round(2).reset_index()
    resumo_dimensoes = resumo_dimensoes.rename(columns={'Pontuação': 'Média'}).sort_values('Média', ascending=False)
    # Remove linhas onde a média não pôde ser calculada (caso raro)
    resumo_dimensoes = resumo_dimensoes.dropna(subset=['Média']) 

# ##### LÓGICA CONDICIONAL REFINADA #####
if not respondentes_selecionados and not dimensoes_selecionadas:
    # Caso 1: NENHUM filtro principal aplicado
    st.info("Selecione os dados para vê-los no seu dashboard!")
    df_para_expandir = df # Mostra todos os dados no expander

elif respondentes_selecionados and not dimensoes_selecionadas:
    # Caso 2: APENAS Respondente(s) selecionado(s), NENHUMA Dimensão
    st.info("Por favor selecione no mínimo 2 dimensões para ver o gráfico")
    st.subheader("Pontuação Média por Dimensão (para respondente(s) selecionado(s))")
    if not resumo_dimensoes.empty:
        st.dataframe(resumo_dimensoes, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma resposta válida encontrada para este(s) respondente(s).")
    df_para_expandir = df_filtrado # Mostra dados filtrados por respondente

else:
    # Caso 3: Dimensões foram selecionadas (com ou sem Respondente)
    if df_filtrado.empty:
        st.info("Nenhuma resposta encontrada para os filtros selecionados.")
        df_para_expandir = df_filtrado
    elif resumo_dimensoes.empty:
         st.info("Nenhuma resposta válida (1-5) para gerar a análise por dimensão com os filtros atuais.")
         df_para_expandir = df_filtrado
    else:
        # Exibe a tabela de médias
        st.subheader("Pontuação Média por Dimensão")
        st.dataframe(resumo_dimensoes, use_container_width=True, hide_index=True)

        st.subheader("Gráfico Comparativo por Dimensão")
        # Verifica se há pelo menos 2 dimensões RESULTANTES para plotar
        if len(resumo_dimensoes) >= 2:
            # Plota o gráfico
            labels = resumo_dimensoes["Dimensão"]
            values = resumo_dimensoes["Média"]
            slice_labels = [str(i+1) for i in range(len(labels))]

            fig, ax = plt.subplots(figsize=(8, 6))
            wedges, texts = ax.pie(
                values, 
                labels=slice_labels, 
                startangle=90,
                textprops=dict(color="black", size=14, weight="bold") 
            )
            ax.axis('equal')
            st.pyplot(fig)

            st.subheader("Legenda do Gráfico")
            for i, row in resumo_dimensoes.iterrows():
                st.markdown(f"**{i+1}:** {row['Dimensão']} (Média: **{row['Média']:.2f}**)")
        else:
            # Exibe a mensagem se menos de 2 dimensões resultaram do filtro
            st.info("Por favor selecione no mínimo 2 dimensões para ver o gráfico")
        
        df_para_expandir = df_filtrado
# Expander com dados brutos (agora usa df_para_expandir)
with st.expander("Ver dados filtrados"):
    st.dataframe(df_para_expandir)

# --- SEÇÃO DE EXPORTAR E LIMPAR ---
st.header("⚙️ Ações")
with st.expander("Ver ações"): 
    st.subheader("Exportar Todos os Dados e Limpar Planilhas de Origem")
    col_download, col_clear = st.columns(2)

    # ##### ALTERAÇÃO: Lógica para exportar TODAS as abas para Excel #####
    output = io.BytesIO()
    try:
        # Usa o objeto spreadsheet que já temos da conexão
        if spreadsheet:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                worksheets_to_export = spreadsheet.worksheets()
                exported_sheets_count = 0
                for ws in worksheets_to_export:
                    # Exporta apenas as abas de resposta (ignora observações, etc.)
                    if "observacoes" not in ws.title.lower() and "teste" not in ws.title.lower():
                        try:
                            data = ws.get_all_records()
                            if data:
                                df_sheet = pd.DataFrame(data)
                                # Opcional: Limpar colunas internas antes de salvar
                                # df_sheet_cleaned = df_sheet.drop(columns=[col for col in ['Reverso', 'Resposta_Num', 'Pontuação'] if col in df_sheet.columns], errors='ignore')
                                df_sheet.to_excel(writer, sheet_name=ws.title, index=False)
                                exported_sheets_count += 1
                        except Exception as e:
                            st.error(f"Erro ao processar aba '{ws.title}' para exportação: {e}")
                
                # Se nenhuma aba foi exportada, cria uma aba de status
                if exported_sheets_count == 0:
                     pd.DataFrame([{"Status": "Nenhuma aba de dados encontrada para exportar."}]).to_excel(writer, sheet_name='Status', index=False)
        else:
            # Caso a conexão inicial tenha falhado
             pd.DataFrame([{"Status": "Não foi possível conectar à Planilha Google."}]).to_excel(output, sheet_name='Erro', index=False)

    except Exception as e:
        st.error(f"Erro ao gerar arquivo Excel: {e}")
        # Cria um arquivo de erro se a geração falhar
        pd.DataFrame([{"Erro": str(e)}]).to_excel(output, sheet_name='Erro', index=False)
        
    processed_data = output.getvalue()

    with col_download:
        st.download_button(
            label="Exportar Dados", 
            data=processed_data,
            file_name=f"export_completo_respostas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", # Nome do arquivo alterado
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=df.empty # Desabilita se não houver dados carregados
        )

    with col_clear:
        # Define o nome da NOVA planilha de backup
        timestamp_backup = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        backup_spreadsheet_name = f"Backup Respostas Formularios - {timestamp_backup}"

        # Atualiza a mensagem de aviso para o novo processo
        st.warning(f"""
            ⚠️ **Atenção:** Ao clicar em 'Limpar Planilha', uma **NOVA PLANILHA** chamada
            **'{backup_spreadsheet_name}'** será criada no seu Google Drive. Os dados de cada aba de resposta
            serão copiados para esta nova planilha, um por um.
            Somente após a cópia bem-sucedida de TODAS as abas, a limpeza dos dados na planilha será realizada. A limpeza é permanente.
        """)

        confirm_clear = st.checkbox("Confirmo que desejo criar a nova planilha de backup e limpar os dados da original.")

        if st.button("Limpar Planilha", type="primary", disabled=not confirm_clear):
            if confirm_clear:
                st.session_state.limpar_clicado = True
                backup_successful = False # Flag para controlar se o backup deu certo
                
                try:
                    # 1. Reconectar e obter cliente gspread
                    with st.spinner("Conectando ao Google Sheets..."):
                        creds_dict_clear = dict(st.secrets["google_credentials"])
                        creds_dict_clear['private_key'] = creds_dict_clear['private_key'].replace('\\n', '\n')
                        gc_clear = gspread.service_account_from_dict(creds_dict_clear)
                        source_spreadsheet = gc_clear.open("Respostas Formularios")
                        st.info("Conectado à planilha de origem.")

                    # 2. Criar a nova planilha de backup
                    with st.spinner(f"Criando planilha de backup '{backup_spreadsheet_name}'..."):
                        try:
                            backup_spreadsheet = gc_clear.create(backup_spreadsheet_name)
                            # Compartilha com a conta de serviço para poder escrever nela
                            backup_spreadsheet.share(creds_dict_clear['client_email'], perm_type='user', role='writer')
                            st.success(f"Planilha de backup '{backup_spreadsheet_name}' criada.")
                            # Tenta deletar a aba padrão 'Sheet1' se ela existir e não for uma das que queremos copiar
                            try:
                                default_sheet = backup_spreadsheet.worksheet('Sheet1')
                                # Verifica se 'Sheet1' é uma das abas de origem para não deletar por engano
                                source_sheet_names = [ws.title for ws in source_spreadsheet.worksheets() if "observacoes" not in ws.title.lower() and "teste" not in ws.title.lower()]
                                if 'Sheet1' not in source_sheet_names:
                                    backup_spreadsheet.del_worksheet(default_sheet)
                            except gspread.WorksheetNotFound:
                                pass # Aba padrão já não existe ou foi renomeada
                        except Exception as create_error:
                            st.error(f"Falha ao criar a planilha de backup: {create_error}")
                            st.stop() # Interrompe se não conseguir criar o backup

                    # 3. Copiar dados aba por aba
                    source_worksheets = source_spreadsheet.worksheets()
                    sheets_to_copy = [ws for ws in source_worksheets if "observacoes" not in ws.title.lower() and "teste" not in ws.title.lower()]
                    
                    if not sheets_to_copy:
                         st.warning("Nenhuma aba de resposta encontrada na planilha de origem para fazer backup.")
                         backup_successful = True # Considera sucesso pois não há o que copiar
                    else:
                        errors_copying = []
                        progress_bar = st.progress(0, text="Copiando abas...")
                        for i, ws_source in enumerate(sheets_to_copy):
                            sheet_title = ws_source.title
                            progress_text = f"Copiando aba: '{sheet_title}' ({i+1}/{len(sheets_to_copy)})..."
                            progress_bar.progress((i + 1) / len(sheets_to_copy), text=progress_text)
                            try:
                                data = ws_source.get_all_values() # Pega cabeçalho + dados
                                if data:
                                    # Cria a nova aba no backup
                                    ws_target = backup_spreadsheet.add_worksheet(title=sheet_title, rows=len(data), cols=len(data[0]) if data else 1)
                                    # Escreve os dados
                                    ws_target.update(data, value_input_option='USER_ENTERED')
                                else:
                                    # Cria aba vazia se a original estiver vazia
                                     backup_spreadsheet.add_worksheet(title=sheet_title, rows=1, cols=1)
                                st.write(f"- Aba '{sheet_title}' copiada com sucesso.")

                            except Exception as copy_error:
                                st.error(f"- Erro ao copiar aba '{sheet_title}': {copy_error}")
                                errors_copying.append(sheet_title)
                        
                        progress_bar.empty() # Remove a barra de progresso
                        
                        if not errors_copying:
                            st.success("Todas as abas de resposta foram copiadas para o backup com sucesso!")
                            backup_successful = True
                        else:
                            st.error(f"Falha ao copiar as seguintes abas: {', '.join(errors_copying)}")
                            st.warning("A limpeza da planilha original NÃO será realizada.")
                            backup_successful = False

                    # 4. Limpar a planilha original (SOMENTE se backup foi 100% ok)
                    if backup_successful:
                        with st.spinner("Limpando abas da planilha original..."):
                            cleared_sheets_count = 0
                            errors_clearing = []
                            for ws in sheets_to_copy: # Itera novamente nas abas que deveriam ter sido copiadas
                                try:
                                    if ws.row_count > 1:
                                        ws.delete_rows(2, ws.row_count)
                                        cleared_sheets_count += 1
                                except Exception as clear_error:
                                    errors_clearing.append(f"Erro ao limpar aba '{ws.title}': {clear_error}")
                            
                            if cleared_sheets_count > 0:
                                st.success(f"{cleared_sheets_count} aba(s) na planilha original foram limpas (mantendo cabeçalhos).")
                            if errors_clearing:
                                for error in errors_clearing: st.error(error)
                            
                            # Limpa o cache para o dashboard refletir a mudança
                            load_all_data.clear()
                            st.info("Cache de dados do dashboard limpo. Use 'CARREGAR DADOS' para atualizar.")
                            # st.rerun() # Opcional

                except Exception as e:
                    st.error(f"Ocorreu um erro inesperado durante o processo: {e}")

            # Mensagem se clicou sem confirmar
            elif not confirm_clear and 'limpar_clicado' in st.session_state and st.session_state.limpar_clicado:
                 st.warning("Você precisa marcar a caixa de confirmação para iniciar o processo.")
            
            # Controle do estado do clique
            if 'limpar_clicado' not in st.session_state: st.session_state.limpar_clicado = False
            if not confirm_clear: st.session_state.limpar_clicado = True

with st.empty():
    st.markdown('<div id="autoclick-div">', unsafe_allow_html=True)
    if st.button("Ping Button", key="autoclick_button"):
        print("Ping button clicked by automation.")
    st.markdown('</div>', unsafe_allow_html=True)