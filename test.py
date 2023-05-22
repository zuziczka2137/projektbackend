lista = ["2023-05-22","14:00"]
godziny = ["10:00","11:00","12:00","13:00","14:00"]
for i in godziny:
    if i in lista:
        continue
    print(f"{i} wolny termin")
