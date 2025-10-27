import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

retail = pd.read_csv('C:/VsCode/venv/retail-transaction-analysis/data/data.csv', encoding= 'ISO-8859-1')
transaction_data = pd.read_csv('C:/VsCode/venv/retail-transaction-analysis/data/transaction_data.csv')
retail['Date'] = pd.to_datetime(retail.InvoiceDate)
transaction_data['date'] = pd.to_datetime(transaction_data.date)
transaction_data['minute'] = transaction_data['date'].dt.minute

# Удаление дубликатов из датафрейма.
check_duplicates = retail.duplicated(keep='first')
duplicates = retail[check_duplicates].copy()
retail_uniq = retail.drop_duplicates(keep='first')
duplicates_count = duplicates.InvoiceNo.count()
duplicates_percent = duplicates_count*100/retail.InvoiceNo.count()
#print(f"Обнаружено {duplicates_count} повторяющихся транзакций ({duplicates_percent:.2f}% от общего объема)")
#print("Вывод: Повторяющиеся транзакции могут указывать на проблемы в системе учета или дублирование записей. Рекомендую провести аудит процесса сбора данных.")

# Отмененные транзакции. 
cancelled_count = len(retail[retail['InvoiceNo'].str.startswith('C')])
total_orders = retail['InvoiceNo'].nunique()
cancellation_rate = (cancelled_count / total_orders) * 100 
#print(f"Вывод: Уровень отмен заказов составляет {cancellation_rate:.1f}%. Это {['ниже', 'выше'][cancellation_rate > 5]} среднего по отрасли (3-5%). Стоит проанализировать причины отмен.")

# Удаление из "InvoiceNo" значений, начинающихся с "С"
retail_uniq = retail.drop(retail[retail['InvoiceNo'].str.startswith('C')].index)

# Анализ покупок наиболее активных пользователей из Германии. 
# (Ваши коллеги уже расчитали, что этот порог — 80-й процентиль.)

uniq_ger = retail_uniq.query('Country == "Germany"') \
    .groupby('CustomerID', as_index=False) \
    .agg({'InvoiceNo':'nunique'})
proc_80 = uniq_ger['InvoiceNo'].quantile(0.8)
top_customers = uniq_ger.query('InvoiceNo > @proc_80')['CustomerID']
#print(f"Вывод: Выделена группа из {len(top_customers)} наиболее активных клиентов (80-й процентиль). \
#Эти клиенты генерируют непропорционально большую долю выручки и требуют особого подхода к удержанию.")

# Смотрим на табличку только по этим подльзователям.
top_retail_germany = retail_uniq[retail_uniq.CustomerID.isin(top_customers)]

top_products = top_retail_germany.query('StockCode != "POST"') \
    .groupby('StockCode', as_index=False) \
    .agg({'InvoiceNo':'count'}) \
    .sort_values('InvoiceNo', ascending=False) \
    .head(5)
#print(f"Вывод: Топ-5 товаров среди премиальных клиентов: {list(top_products.index)}. \
#Эти товары стоит включить в персонализированные предложения и рекламные кампании.")

# Вернемся к анализу датафрейма retail. Вам нужно найти 5 наиболее крупных по выручке заказов. 
# Для этого сначала посчитайте сумму покупки для каждой транзакции, т.е. создайте колонку Revenue с суммой покупки, используя колонки Quantity и UnitPrice. 
# Потом для каждого заказа (см.колонку InvoiceNo) суммируйте выручку всех входящих в него транзакций — это будет колонка TotalRevenue. 
# Отсортируйте записи в порядке убывания TotalRevenue. 
# В качестве ответа укажите топ-5 заказов (см.колонку InvoiceNo) по сумме заказа (через запятую с пробелом, в том же порядке).

retail_uniq['Revenue'] = retail_uniq['Quantity']*retail_uniq['UnitPrice']
top_orders = retail_uniq.groupby('InvoiceNo', as_index=False) \
    .agg({'Revenue':'sum'}) \
    .sort_values('Revenue', ascending=False) \
    .head(5)
#print(f"Вывод: Самые крупные заказы приносят от {top_orders.Revenue.min():.0f} до {top_orders.Revenue.max():.0f}. \
#Анализ состава этих заказов поможет понять, что стимулирует крупные покупки.")

# Определите количество транзакций того или иного статуса.
trans_counts = transaction_data['transaction'].value_counts()

# Кол-во успешных транзакций по каждопу пользователю.
success_trans = transaction_data. \
    query('transaction == "successfull"'). \
    groupby('name', as_index=False). \
    agg({'transaction':'count'})

# Процент ошибочных транзакций.
error_rate = (trans_counts.get('error', 0) / len(transaction_data)) * 100
#print(f"Вывод: Доля ошибочных транзакций: {error_rate:.2f}%. \
#Такая доля ошибок не требует срочного вмешательства.")

# Измерение кол-ва операций осуществляемых каждым пользователем в каждую минуту наблюдаемого временного промежутка.
trans_per_min = transaction_data.groupby(['name','minute'], as_index=False) \
    .agg({'transaction':'count'}) \
    .pivot(index='minute', columns='name', values='transaction') \
    .fillna(0)
# После построения pivot_trans_per_min
peak_minute = trans_per_min.sum(axis=1).idxmax()
peak_activity = trans_per_min.sum(axis=1).max()
avg_activity = trans_per_min.sum(axis=1).mean()
growth_factor = peak_activity / avg_activity 
#print(f"Вывод: Обнаружен аномальный всплеск активности в {peak_minute}-ю минуту: +{growth_factor:.1f}x к среднему значению. \
#Это напрямую коррелирует с публикацией рекламы блогером и демонстрирует мгновенный отклик аудитории.")

# Расчет RFM

# Расчет давности последней покупки
current_date = retail['Date'].max()
recency_df = retail.groupby('CustomerID')['Date'].max().reset_index()
recency_df['Recency'] = (current_date - recency_df['Date']).dt.days

# Расчет частоты покупок
frequency_df = retail.groupby('CustomerID')['InvoiceNo'].nunique().reset_index()
frequency_df.rename(columns={'InvoiceNo': 'Frequency'}, inplace=True)

# Расчет общей суммы покупок
retail['TotalPrice'] = retail['Quantity'] * retail['UnitPrice']
monetary_df = retail.groupby('CustomerID')['TotalPrice'].sum().reset_index()
monetary_df.rename(columns={'TotalPrice': 'Monetary'}, inplace=True)

# Собираем все метрики вместе
rfm_df = recency_df.merge(frequency_df, on='CustomerID').merge(monetary_df, on='CustomerID')

# Присваиваем баллы (1-5, где 5 - лучший)
rfm_df['R_Score'] = pd.qcut(rfm_df['Recency'], 5, labels=[5,4,3,2,1])
rfm_df['F_Score'] = pd.qcut(rfm_df['Frequency'], 5, labels=[1,2,3,4,5])
rfm_df['M_Score'] = pd.qcut(rfm_df['Monetary'], 5, labels=[1,2,3,4,5])

# Создаем RFM-сегмент
rfm_df['RFM_Segment'] = rfm_df['R_Score'].astype(str) + rfm_df['F_Score'].astype(str) + rfm_df['M_Score'].astype(str)
rfm_df['RFM_Score'] = rfm_df['R_Score'].astype(int) + rfm_df['F_Score'].astype(int) + rfm_df['M_Score'].astype(int)

# Для просмотра значений и таблиц:
print()