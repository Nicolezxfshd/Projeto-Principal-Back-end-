import pytest   

def soma(a, b):
    return a + b

def test_soma_dois_numeros():
    resultado = soma(2, 3)
    assert resultado == 5   