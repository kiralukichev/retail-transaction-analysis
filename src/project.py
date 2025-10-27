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
# (Коллеги уже расчитали, что этот порог — 80-й процентиль.)
uniq_ger = retail_uniq.query('Country == "Germany"') \
    .groupby('CustomerID', as_index=False) \
    .agg({'InvoiceNo':'nunique'})
proc_80 = uniq_ger['InvoiceNo'].quantile(0.8)
top_customers = uniq_ger.query('InvoiceNo > @proc_80')['CustomerID']
#print(f"Вывод: Выделена группа из {len(top_customers)} наиболее активных клиентов (80-й процентиль). \
#Эти клиенты генерируют непропорционально большую долю выручки и требуют особого подхода к удержанию.")

# Смотрим на табличку только по этим подльзователям.
top_retail_germany = retail_uniq[retail_uniq.CustomerID.isin(top_customers)]

# Расчет RFM
def calculate_rfm_metrics(df):
    #Расчет RFM-метрик для сегментации клиентов#
    
    # Фильтруем только успешные транзакции (без отмен)
    successful_df = df[~df['InvoiceNo'].str.startswith('C', na=False)]
    successful_df = successful_df[successful_df['Quantity'] > 0]
    
    # Recency
    current_date = successful_df['Date'].max()
    recency = successful_df.groupby('CustomerID') \
        .agg ({'Date':'max'}) \
        .reset_index()
    recency['Recency'] = (current_date - recency['Date']).dt.days
    
    # Frequency
    frequency = successful_df.groupby('CustomerID') \
        .agg({'InvoiceNo':'nunique'}) \
        .reset_index()
    frequency.rename(columns={'InvoiceNo': 'Frequency'}, inplace=True)
    
    # Monetary
    successful_df['TotalValue'] = successful_df['Quantity'] * successful_df['UnitPrice']
    monetary = successful_df.groupby('CustomerID') \
        .agg({'TotalValue':'sum'}) \
        .reset_index()
    monetary.rename(columns={'TotalValue': 'Monetary'}, inplace=True)
    
    # Объединяем
    rfm = recency.merge(frequency, on='CustomerID').merge(monetary, on='CustomerID')
    
    # RFM-баллы
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1])
    rfm['F_Score'] = pd.qcut(rfm['Frequency'], 5, labels=[1,2,3,4,5])
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1,2,3,4,5])
    
    return rfm

# Применяем к данным по Германии
german_rfm = calculate_rfm_metrics(top_retail_germany)

top_products = top_retail_germany.query('StockCode != "POST"') \
    .groupby('StockCode', as_index=False) \
    .agg({'InvoiceNo':'count'}) \
    .sort_values('InvoiceNo', ascending=False) \
    .head(5)
#print(f"Вывод: Топ-5 товаров среди премиальных клиентов: {list(top_products.index)}. \
#Эти товары стоит включить в персонализированные предложения и рекламные кампании.")

# 5 наиболее крупных по выручке заказов. 
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
#print(f"Вывод: Обнаружен аномальный всплеск активности в {peak_minute}-ю минуту: +{growth_factor:.1f}x к среднему значению.")

# Для просмотра значений и таблиц:
print()