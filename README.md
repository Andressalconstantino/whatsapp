<h1>Aplicação Whatsapp</h1> 

<p align="center">
  <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54"/>
</p>

> Status do Projeto: :heavy_check_mark: (concluido)

### Tópicos 

:small_blue_diamond: [Descrição do projeto](#descrição-do-projeto)

:small_blue_diamond: [Funcionalidades](#funcionalidades)

:small_blue_diamond: [Pré-requisitos](#pré-requisitos)

:small_blue_diamond: [Como rodar a aplicação](#como-rodar-a-aplicação-arrow_forward)

## Descrição do projeto 

<p align="justify">
  Este projeto foi desenvolvido em Python seguindo o modelo cliente-servidor utilizando o protocolo TCP, com o objetivo de permitir a comunicação entre múltiplos clientes conectados simultaneamente.
</p>

## Funcionalidades

:heavy_check_mark: Permitir que 2 clientes conversem entre si 

:heavy_check_mark: Permitir criação de grupos

:heavy_check_mark: Avisar quando a mensagem for lida/recebida 

:heavy_check_mark: Permitir que múltiplos clientes se conectem simultaneamente

## Pré-requisitos

:heavy_check_mark: Python 3.x

:heavy_check_mark: Biliotecas: Socket, Threading e Pickle

## Como rodar a aplicação :arrow_forward:

No terminal, rode o servidor: 

```
python3 servidor.py
```

E depois abra um terminal para cada cliente que desejar rodar:
```
python3 cliente.py
```
