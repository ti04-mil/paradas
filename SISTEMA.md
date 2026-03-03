# Sistema de Paradas

## Visão geral
O **Sistema de Paradas** é uma aplicação web em Flask para registrar e monitorar paradas de teares por turno, incluindo envio de produção consolidada, gestão de motivos de parada, cadastro de usuários e acompanhamento de status operacional em tempo real.

A aplicação utiliza banco SQLite e escolhe automaticamente o caminho do banco na seguinte ordem:
1. variável de ambiente `PARADAS_DB_PATH`;
2. caminho de rede padrão (`\\server\\TI\\Temp\\Paradas\\Sistema\\Paradas.db`) se existir;
3. arquivo local `Paradas.db` na pasta do projeto.

## Principais funcionalidades

- **Autenticação de usuários** com login e sessão.
- **Controle por níveis/setores** para habilitar permissões por perfil.
- **Gestão de usuários e setores** (cadastro, edição e exclusão).
- **Gestão de turnos da empresa** e tipos de turno.
- **Gestão de motivos de parada** com código padronizado em 4 dígitos.
- **Gestão de teares** (cadastro e manutenção).
- **Tela de status dos teares** para iniciar/parar máquina e registrar intervalos.
- **Descanso semanal** com validação de período.
- **Envio de produção por turno** (1º, 2º e 3º turno), incluindo execução manual e sincronização automática.

## Regras operacionais importantes

- O sistema normaliza nomes de turno para evitar divergências de escrita.
- Cálculos de duração tratam corretamente virada de dia (ex.: término menor que início).
- O 3º turno considera janela que cruza meia-noite.
- Existe rotina de sincronização automática protegida por lock para evitar execução concorrente.

## Estrutura principal do projeto

- `app.py`: aplicação Flask, regras de negócio, inicialização do banco e rotas.
- `templates/`: páginas HTML (login, sistema, usuários, teares, motivos, turnos, envio e status).
- `imagens/logo.png`: identidade visual usada na interface.
- Arquivos `.bat`, `.iss` e logs: apoio para execução local e empacotamento/instalação.

## Rotas principais da aplicação

- `/login`: autenticação.
- `/`: página inicial.
- `/sistema`: menu principal.
- `/enviar`, `/enviar/1-turno`, `/enviar/2-turno`, `/enviar/3-turno`, `/enviar/manual`: envio de produção.
- `/usuarios`: administração de usuários.
- `/setores`: administração de setores.
- `/turnos-empresa`: configuração de janelas de turno por dia.
- `/motivos`: cadastro de motivos de parada.
- `/teares`: cadastro de teares.
- `/status-teares`: operação de início/parada e status das máquinas.
- `/descanso-semanal`: controle de descanso semanal.

## Tecnologias

- **Python**
- **Flask**
- **SQLite**
- **Jinja2** (templates HTML)

## Execução

Com dependências instaladas (`requirements.txt`), execute:

```bash
python app.py
```

A aplicação inicializa estruturas necessárias no banco e sobe o servidor web para uso interno.
