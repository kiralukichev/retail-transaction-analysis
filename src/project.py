import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

retail = pd.read_csv('C:/VsCode/venv/retail-transaction-analysis/data/data.csv', encoding= 'ISO-8859-1')
transaction_data = pd.read_csv('C:/VsCode/venv/retail-transaction-analysis/data/transaction_data.csv')
transaction_data_updated = pd.read_csv('C:/VsCode/venv/retail-transaction-analysis/data/transaction_data_updated.csv')

# Удаление дебликатов из датафрейма
retail = retail.drop_duplicates()
# Удаление из "InvoiceNo" значений, начинающихся с "С"
retail = retail.drop(retail[retail['InvoiceNo'].str.startswith('C')].index)

# Ваша задача — проанализировать покупки наиболее активных пользователей одной из стран. 
# Для этого сначала вам нужно найти пользователей из Германии, которые совершили значительное количество заказов, т.е. выше определенного порога N. 
# Ваши коллеги уже расчитали, что этот порог — 80-й процентиль. 
# Иными словами, вам нужно посчитать число заказов (см.колонку InvoiceNo) для каждого пользователя (см. колонку CustomerID) 
#   из Германии (Germany) и оставить только тех, кто совершил более N заказов, где N – 80-й процентиль. 
# Запишите полученные id пользователей в переменную germany_top (не весь датафрейм, только id).

uniq_ger = retail.query('Country == "Germany"') \
    .groupby('CustomerID', as_index=False) \
    .agg({'InvoiceNo':'nunique'})

proc_80 = uniq_ger['InvoiceNo'].quantile(0.8)

germany_top = uniq_ger.query('InvoiceNo > @proc_80')['CustomerID']

# Удаление дебликатов из датафрейма
retail = retail.drop_duplicates()
# Удаление из "InvoiceNo" значений, начинающихся с "С"
retail = retail.drop(retail[retail['InvoiceNo'].str.startswith('C')].index)

proc_80 = uniq_ger['InvoiceNo'].quantile(0.8)

germany_top = uniq_ger.query('InvoiceNo > @proc_80')['CustomerID']

# Задание 5

# Возьмите из датафрейма retail записи только по интересующим нас пользователям из переменной germany_top. 
# Результирующий датафрейм запишите в top_retail_germany.
top_retail_germany = retail[retail.CustomerID.isin(germany_top)]

top_ger = top_retail_germany.query('StockCode != "POST"') \
    .groupby('StockCode', as_index=False) \
    .agg({'InvoiceNo':'count'}) \
    .sort_values('InvoiceNo', ascending=False)

# Удаление дебликатов из датафрейма
retail = retail.drop_duplicates()
# Удаление из "InvoiceNo" значений, начинающихся с "С"
retail = retail.drop(retail[retail['InvoiceNo'].str.startswith('C')].index)

# Вернемся к анализу датафрейма retail. Вам нужно найти 5 наиболее крупных по выручке заказов. 
# Для этого сначала посчитайте сумму покупки для каждой транзакции, т.е. создайте колонку Revenue с суммой покупки, используя колонки Quantity и UnitPrice. 
# Потом для каждого заказа (см.колонку InvoiceNo) суммируйте выручку всех входящих в него транзакций — это будет колонка TotalRevenue. 
# Отсортируйте записи в порядке убывания TotalRevenue. 
# В качестве ответа укажите топ-5 заказов (см.колонку InvoiceNo) по сумме заказа (через запятую с пробелом, в том же порядке).

retail['Revenue'] = retail['Quantity']*retail['UnitPrice']
retail_sum_rev = retail.groupby('InvoiceNo', as_index=False) \
    .agg({'Revenue':'sum'}) \
    .sort_values('Revenue', ascending=False) \
    .head(5)

# Задание 9
# Определите количество транзакций того или иного статуса.
trans_count = transaction_data. \
    groupby('transaction', as_index=False). \
    agg({'name':'count'})

# Задание 10 
# Сколько успешных транзакций совершил каждый пользователь.
success_trans = transaction_data. \
    query('transaction == "successfull"'). \
    groupby('name', as_index=False). \
    agg({'transaction':'count'})

transaction_data_updated['date'] = pd.to_datetime(transaction_data_updated.date)

# Задание 12
# Сформировать сводную таблицу, которая покажет, какое количество операций осуществлял каждый пользователь 
#   в каждую минуту наблюдаемого временного промежутка.
pivot_trans_per_min = transaction_data_updated.groupby(['name','minute'], as_index=False) \
    .agg({'transaction':'count'}) \
    .pivot(index='minute', columns='name', values='transaction') \
    .fillna(0)

# Задание 14
# Подсчитайте правильное количество минут, прошедших с начала дня, а не минутную часть времени, 
#   сохранив результаты в новой колонке 'true_minute'.
transaction_data_updated['true_minute'] = transaction_data_updated['date'].dt.hour*60+transaction_data_updated['date'].dt.minute

print()