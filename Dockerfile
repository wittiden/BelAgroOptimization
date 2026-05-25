FROM continuumio/miniconda3:latest AS conda
FROM python:3.14-slim

COPY --from=conda /opt/conda /opt/conda

ENV PATH="/opt/conda/bin:${PATH}"

WORKDIR /app

RUN conda install -c conda-forge ipopt cyipopt -y && \
    conda clean --all -y

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]
