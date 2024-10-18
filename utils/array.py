def divide_chunks(lst, n):
    # Проходим по списку с шагом n и возвращаем срезы
    for i in range(0, len(lst), n):
        yield lst[i : i + n]
