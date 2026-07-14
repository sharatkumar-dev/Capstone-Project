FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --theme.base=dark --theme.primaryColor=#38bdf8 --theme.backgroundColor=#0f172a --theme.secondaryBackgroundColor=#1e293b --theme.textColor=#f1f5f9"]
