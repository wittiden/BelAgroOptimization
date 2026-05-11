# app/run.py

from app.database.engine import session_factory
from app.modules.model.opt_model import BelarusAgroModel
from app.modules.repository.repo import AgroRepository, ModelDataBuilder


def main():
    # Подключение к БД


    with session_factory() as session:
        # Создаём репозиторий и строитель данных
        repo = AgroRepository(session)
        builder = ModelDataBuilder(repo)

        # Загружаем данные из активного сценария
        model_data = builder.build_from_active_scenario()

        # Создаём и запускаем модель
        model = BelarusAgroModel(model_data)

        if model.solve():
            model.print_results()


if __name__ == "__main__":
    main()