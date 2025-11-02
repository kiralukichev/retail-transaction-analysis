import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from project import transaction_data, top_retail_germany, retail_uniq, german_rfm

# Настройки графиков:
plt.rcParams['figure.figsize'] = (10, 6)
sns.set_style("whitegrid")
# Сохранение графиков: 
# plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/name.png', dpi=300, bbox_inches='tight')

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

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from project import transaction_data, top_retail_germany, retail_uniq, german_rfm

# Исключаем POST и считаем популярные товары
top_10_products_ger = (top_retail_germany[top_retail_germany['StockCode'] != 'POST']
                .groupby('StockCode')['InvoiceNo']
                .count()
                .nlargest(10))

plt.figure(figsize=(10, 6))
plt.barh(range(len(top_10_products_ger)), top_10_products_ger.values)
plt.yticks(range(len(top_10_products_ger)), [str(x)[:40] + '...' for x in top_10_products_ger.index])
plt.title('Топ-10 популярных товаров в Германии')
plt.xlabel('Количество заказов')
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/top_10_products_ger.png', dpi=300, bbox_inches='tight')
plt.show()

# Считаем сумму каждого заказа
order_totals = retail_uniq.groupby('InvoiceNo')['Revenue'].sum()

# Топ-10 самых крупных заказов
top_orders = order_totals.nlargest(10)

plt.figure(figsize=(10, 6))
plt.bar(range(len(top_orders)), top_orders.values, color='orange')
plt.title('Топ-10 самых крупных заказов')
plt.xlabel('Номер заказа')
plt.ylabel('Сумма заказа')
plt.xticks(range(len(top_orders)), top_orders.index, rotation=45)
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/top_10_orders.png', dpi=300, bbox_inches='tight')
plt.show()

# Сумма продаж по странам (топ-10)
country_revenue = retail_uniq.groupby('Country')['Revenue'].sum().nlargest(10)

plt.figure(figsize=(10, 6))
plt.bar(country_revenue.index, country_revenue.values, color='lightgreen')
plt.title('Выручка по странам (топ-10)')
plt.ylabel('Общая выручка')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/top_10_country.png', dpi=300, bbox_inches='tight')
plt.show()

# Предполагаем, что rfm_df уже рассчитан
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# Recency
ax1.hist(german_rfm['Recency'], bins=15, alpha=0.7, color='red')
ax1.set_title('Recency (дни с последней покупки)')
ax1.set_xlabel('Дней')

# Frequency
ax2.hist(german_rfm['Frequency'], bins=15, alpha=0.7, color='blue')
ax2.set_title('Frequency (количество заказов)')
ax2.set_xlabel('Заказов')

# Monetary
ax3.hist(german_rfm['Monetary'], bins=15, alpha=0.7, color='green')
ax3.set_title('Monetary (общая сумма)')
ax3.set_xlabel('Сумма')

plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/rfm.png', dpi=300, bbox_inches='tight')
plt.show()

# Распределение баллов
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

ax1.bar(german_rfm['R_Score'].value_counts().index, german_rfm['R_Score'].value_counts().values)
ax1.set_title('Recency Scores')

ax2.bar(german_rfm['F_Score'].value_counts().index, german_rfm['F_Score'].value_counts().values)
ax2.set_title('Frequency Scores')

ax3.bar(german_rfm['M_Score'].value_counts().index, german_rfm['M_Score'].value_counts().values)
ax3.set_title('Monetary Scores')

plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/frm_score.png', dpi=300, bbox_inches='tight')
plt.show()

# Средний чек по странам (топ-10)
avg_ticket_by_country = (retail_uniq \
                         .groupby('Country')['Revenue']
                         .mean()
                         .nlargest(10))

plt.figure(figsize=(10, 6))
plt.bar(avg_ticket_by_country.index, avg_ticket_by_country.values, color='purple')
plt.title('Средний чек по странам (топ-10)')
plt.ylabel('Средний чек')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('C:/VsCode/venv/retail-transaction-analysis/reports/top_10_avg_rev_country.png', dpi=300, bbox_inches='tight')
plt.show()