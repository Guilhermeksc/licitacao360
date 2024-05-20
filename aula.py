# def calcular_area(a, b):
#     area = a * b
#     return area

# print(calcular_area(10, 20), "m2")
# print("Área de", calcular_area(10, 20), "m2")


salario = 12500

if salario <= 1412:
    print("Até 1 salário mínimo")
elif salario > 1412 and salario <= 4236:
    print("De 1 a 3 salários mínimos")
elif salario > 4236 and salario <= 7060:
    print("De 3 a 5 salários mínimos")
else:
    print("Acima de 5 salários mínimos")

def quantidade_salarios(salario):

    quantidade = (salario / 1412)

    if quantidade <= 10:
        return quantidade
    else:
        return ("Acima de 10 salários mínimos")
    
print(quantidade_salarios(12500))
print(quantidade_salarios(1412))
print(quantidade_salarios(4236))


lista_invest = []

while saldo_investimento < 10000:
    saldo_investimento = (saldo_investimento*1.1)
    lista_invest.append(saldo_investimento)

print(lista_invest)