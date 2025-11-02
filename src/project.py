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
total_orders = len(retail['InvoiceNo'])
cancellation_rate = (cancelled_count / total_orders) * 100 
#print(f"Вывод: Уровень отмен заказов составляет {cancellation_rate:.1f}%. Это {['ниже', 'выше'][cancellation_rate > 5]} среднего по отрасли (5-10%). Стоит проанализировать причины отмен.")

# Удаление из "InvoiceNo" значений, начинающихся с "С"
retail_uniq = retail.drop(retail[retail['InvoiceNo'].str.startswith('C')].index)

# Анализ покупок наиболее активных пользователей из Германии. 
# (Коллеги уже расчитали, что этот порог — 80-й процентиль.)
uniq_ger = retail_uniq.query('Country == "Germany"') \
    .groupby('CustomerID', as_index=False) \
    .agg({'InvoiceNo':'nunique'})
proc_80 = uniq_ger['InvoiceNo'].quantile(0.8)
top_customers = uniq_ger.query('InvoiceNo > @proc_80')['CustomerID']
#print(f"Вывод: Выделена группа из {len(top_customers)} наиболее активных клиентов (80-й процентиль). Эти клиенты генерируют непропорционально большую долю выручки и требуют особого подхода к удержанию.")

# Смотрим на табличку только по этим подльзователям.
top_retail_germany = retail_uniq[retail_uniq.CustomerID.isin(top_customers)]
top_retail_germany['Revenue'] = top_retail_germany['Quantity']*top_retail_germany['UnitPrice']

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
#print(f"Вывод: Топ-5 товаров среди премиальных клиентов: {list(top_products.index)}. Эти товары стоит включить в персонализированные предложения и рекламные кампании.")

# 5 наиболее крупных по выручке заказов. 
retail_uniq['Revenue'] = retail_uniq['Quantity']*retail_uniq['UnitPrice']
top_orders = retail_uniq.groupby('InvoiceNo', as_index=False) \
    .agg({'Revenue':'sum'}) \
    .sort_values('Revenue', ascending=False) \
    .head(5)
#print(f"Вывод: Самые крупные заказы приносят от {top_orders.Revenue.min():.0f} до {top_orders.Revenue.max():.0f}. Анализ состава этих заказов поможет понять, что стимулирует крупные покупки.")

# Определите количество транзакций того или иного статуса.
trans_counts = transaction_data['transaction'].value_counts()

# Кол-во успешных транзакций по каждопу пользователю.
success_trans = transaction_data. \
    query('transaction == "successfull"'). \
    groupby('name', as_index=False). \
    agg({'transaction':'count'})

# Процент ошибочных транзакций.
error_rate = (trans_counts.get('error', 0) / len(transaction_data)) * 100
#print(f"Вывод: Доля ошибочных транзакций: {error_rate:.2f}%. Такая доля ошибок не требует срочного вмешательства.")

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
#print(f"Вывод: Обнаружен аномальный всплеск активности пользователей в {peak_minute}-ю минуту: +{growth_factor:.1f}x к среднему значению.")

# Для просмотра значений и таблиц:
print()








# Графики:
plt.rcParams['figure.figsize'] = (10, 6)
sns.set_style("whitegrid")
# Сохранение: plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')


# Подсчет статусов
status_counts = transaction_data['transaction'].value_counts()

# Простой барплот
plt.figure(figsize=(8, 5))
plt.bar(status_counts.index, status_counts.values, color=['green', 'red', 'blue', 'orange'])
plt.title('Статусы транзакций')
plt.ylabel('Количество')
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/transaction_status.png', dpi=300, bbox_inches='tight')
plt.show()

# Круговая диаграмма
plt.figure(figsize=(8, 8))
plt.pie(status_counts.values, labels=status_counts.index, autopct='%1.1f%%')
plt.title('Доли статусов транзакций')
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/transaction_status_circle.png', dpi=300, bbox_inches='tight')
plt.show()

# Топ-15 пользователей по количеству транзакций
user_counts = retail['name'].value_counts().head(15)

plt.figure(figsize=(12, 6))
plt.bar(user_counts.index, user_counts.values)
plt.title('Топ-15 пользователей по количеству транзакций')
plt.xticks(rotation=45)
plt.ylabel('Количество транзакций')
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/top_15.png', dpi=300, bbox_inches='tight')
plt.show()

# Считаем заказы на клиента
orders_per_customer = uniq_ger.groupby('CustomerID')['InvoiceNo'].nunique()

plt.figure(figsize=(10, 6))
plt.hist(orders_per_customer, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
plt.title('Количество заказов на клиента (Германия)')
plt.xlabel('Количество заказов')
plt.ylabel('Количество клиентов')
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/germany_per_client.png', dpi=300, bbox_inches='tight')
plt.show()

# Популярные товары

plt.figure(figsize=(10, 6))
plt.barh(range(len(top_products)), top_products.values)
plt.yticks(range(len(top_products)), [str(x)[:40] + '...' for x in top_products.index])
plt.title('Топ-10 популярных товаров в Германии')
plt.xlabel('Количество заказов')
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/top_products.png', dpi=300, bbox_inches='tight')
plt.show()


#???
# Считаем сумму каждого заказа
retail['TotalValue'] = retail['Quantity'] * retail['UnitPrice']
order_totals = retail.groupby('InvoiceNo')['TotalValue'].sum()

# Топ-10 самых крупных заказов
top_orders = order_totals.nlargest(10)

plt.figure(figsize=(10, 6))
plt.bar(range(len(top_orders)), top_orders.values, color='orange')
plt.title('Топ-10 самых крупных заказов')
plt.xlabel('Номер заказа')
plt.ylabel('Сумма заказа')
plt.xticks(range(len(top_orders)), top_orders.index, rotation=45)
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')
plt.show()

# Сумма продаж по странам (топ-10)
country_revenue = retail_df.groupby('Country')['TotalValue'].sum().nlargest(10)

plt.figure(figsize=(10, 6))
plt.bar(country_revenue.index, country_revenue.values, color='lightgreen')
plt.title('Выручка по странам (топ-10)')
plt.ylabel('Общая выручка')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')
plt.show()

# Предполагаем, что rfm_df уже рассчитан
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# Recency
ax1.hist(rfm_df['Recency'], bins=15, alpha=0.7, color='red')
ax1.set_title('Recency (дни с последней покупки)')
ax1.set_xlabel('Дней')

# Frequency
ax2.hist(rfm_df['Frequency'], bins=15, alpha=0.7, color='blue')
ax2.set_title('Frequency (количество заказов)')
ax2.set_xlabel('Заказов')

# Monetary
ax3.hist(rfm_df['Monetary'], bins=15, alpha=0.7, color='green')
ax3.set_title('Monetary (общая сумма)')
ax3.set_xlabel('Сумма')

plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')
plt.show()

# Распределение баллов
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

ax1.bar(rfm_df['R_Score'].value_counts().index, rfm_df['R_Score'].value_counts().values)
ax1.set_title('Recency Scores')

ax2.bar(rfm_df['F_Score'].value_counts().index, rfm_df['F_Score'].value_counts().values)
ax2.set_title('Frequency Scores')

ax3.bar(rfm_df['M_Score'].value_counts().index, rfm_df['M_Score'].value_counts().values)
ax3.set_title('Monetary Scores')

plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')
plt.show()

# Если есть колонка true_minute
if 'true_minute' in transaction_df.columns:
    minute_activity = transaction_df.groupby('true_minute').size()
    
    plt.figure(figsize=(12, 6))
    plt.plot(minute_activity.index, minute_activity.values, linewidth=2)
    plt.title('Активность транзакций по минутам')
    plt.xlabel('Минута')
    plt.ylabel('Количество транзакций')
    
    # Показываем пик
    peak_minute = minute_activity.idxmax()
    peak_value = minute_activity.max()
    plt.axvline(x=peak_minute, color='red', linestyle='--', 
                label=f'Пик: {peak_value} на {peak_minute} минуте')
    plt.legend()
    plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Средний чек по странам (топ-10)
avg_ticket_by_country = (retail_df[~retail_df['is_cancelled']]
                         .groupby('Country')['TotalValue']
                         .mean()
                         .nlargest(10))

plt.figure(figsize=(10, 6))
plt.bar(avg_ticket_by_country.index, avg_ticket_by_country.values, color='purple')
plt.title('Средний чек по странам (топ-10)')
plt.ylabel('Средний чек')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')
plt.show()